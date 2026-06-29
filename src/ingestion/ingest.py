import json
import re as _re
from pathlib import Path
from bs4 import BeautifulSoup

RAW_DIR = Path("corpus/raw")
CHUNKS_DIR = Path("corpus/chunks")
CHUNKS_DIR.mkdir(parents=True, exist_ok=True)

CHUNK_MAX_CHARS = 900
CHUNK_OVERLAP = 120

def infer_metadata(filename: str) -> dict:
    if filename.startswith("python_"):
        return {"linguagem": "python", "dbms": None}
    if filename.startswith("sqlite_"):
        return {"linguagem": "sql", "dbms": "sqlite"}
    if filename.startswith("postgres_"):
        return {"linguagem": "sql", "dbms": "postgresql"}
    return {"linguagem": "desconhecido", "dbms": None}

def extract_main_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()
    main = (
        soup.select_one("div.body[role='main']")
        or soup.select_one("div#docContent")
        or soup.select_one("main")
        or soup.body
        or soup
    )
    return main

def split_by_headings(main) -> list[tuple[str, str]]:
    """Retorna lista de (titulo_secao, texto_secao)."""
    sections = []
    current_title = "introducao"
    current_text = []

    for el in main.descendants:
        if getattr(el, "name", None) in ("h1", "h2", "h3"):
            if current_text:
                sections.append((current_title, " ".join(current_text).strip()))
            current_title = el.get_text(strip=True) or current_title
            current_text = []
        elif getattr(el, "name", None) in ("p", "li", "pre", "code", "dt", "dd"):
            text = el.get_text(" ", strip=True)
            if text:
                current_text.append(text)

    if current_text:
        sections.append((current_title, " ".join(current_text).strip()))

    return [(t, txt) for t, txt in sections if len(txt) > 40]

def chunk_text(text: str) -> list[str]:
    text = _re.sub(r"\s+", " ", text).strip()
    if len(text) <= CHUNK_MAX_CHARS:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_MAX_CHARS
        chunks.append(text[start:end])
        start = end - CHUNK_OVERLAP
    return chunks

def is_junk_chunk(text: str) -> bool:
    """Detecta boilerplate de navegacao e despejos de diagrama de sintaxe/gramatica BNF."""
    menu_markers = ["Home Menu About Documentation Download License Support Purchase Search"]
    if any(m in text for m in menu_markers):
        return True

    diagram_hits = len(_re.findall(r"[\w-]+:\s*(show|hide)", text))
    if diagram_hits >= 3:
        return True

    # Heuristica geral: prosa de verdade tem pontuacao de frase. Despejos de
    # gramatica/diagrama (sqlite e postgres) sao so tokens concatenados, sem
    # nenhum ponto final numa string longa.
    if len(text) > 150:
        pontuacao_final = text.count(".") + text.count("!") + text.count("?")
        if pontuacao_final == 0:
            return True

    return False

def main():
    manifest = json.loads((RAW_DIR / "manifest.json").read_text(encoding="utf-8"))
    out_path = CHUNKS_DIR / "chunks.jsonl"
    total = 0
    seen_texts = set()

    with out_path.open("w", encoding="utf-8") as out:
        for filename, url in manifest.items():
            html = (RAW_DIR / filename).read_text(encoding="utf-8")
            main_el = extract_main_text(html)
            sections = split_by_headings(main_el)
            metadata = infer_metadata(filename)

            for sec_idx, (titulo, texto) in enumerate(sections):
                for chunk_idx, chunk in enumerate(chunk_text(texto)):
                    if is_junk_chunk(chunk):
                        continue
                    if chunk in seen_texts:
                        continue
                    seen_texts.add(chunk)

                    record = {
                        "id": f"{filename}_{sec_idx:03d}_{chunk_idx:02d}",
                        "source": url,
                        "arquivo": filename,
                        "secao": titulo,
                        "text": chunk,
                        "metadata": metadata,
                    }
                    out.write(json.dumps(record, ensure_ascii=False) + "\n")
                    total += 1

    print(f"Total de chunks gerados: {total}")
    print(f"Salvo em: {out_path}")

if __name__ == "__main__":
    main()