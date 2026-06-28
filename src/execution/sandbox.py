import re
import subprocess
import sqlite3
import sys
import tempfile
from pathlib import Path

TIMEOUT_SECONDS = 8


def extract_code_blocks(texto: str) -> list[dict]:
    """Extrai blocos ```python e ```sql de uma resposta em markdown."""
    blocos = []
    for match in re.finditer(r"```(python|sql)\n(.*?)```", texto, re.DOTALL):
        linguagem = match.group(1)
        codigo = match.group(2).strip()
        if codigo:
            blocos.append({"linguagem": linguagem, "codigo": codigo})
    return blocos


def run_python(codigo: str) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = Path(tmpdir) / "snippet.py"
        script_path.write_text(codigo, encoding="utf-8")

        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
                cwd=tmpdir,
                env={},  # sem variaveis de ambiente do processo pai
            )
            sucesso = result.returncode == 0
            return {
                "sucesso": sucesso,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
            }
        except subprocess.TimeoutExpired:
            return {"sucesso": False, "stdout": "", "stderr": f"Timeout ({TIMEOUT_SECONDS}s excedido)"}


def run_sql(codigo: str) -> dict:
    """Roda contra SQLite em memoria com uma tabela dummy generica para validar sintaxe."""
    try:
        conn = sqlite3.connect(":memory:")
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE pessoas (
                id INTEGER PRIMARY KEY,
                nome TEXT,
                idade INTEGER
            )
        """)
        cur.executemany(
            "INSERT INTO pessoas (nome, idade) VALUES (?, ?)",
            [("Ana", 30), ("Bruno", 25), ("Carla", 40)],
        )
        conn.commit()

        cur.execute(codigo)
        linhas = cur.fetchall()
        conn.close()
        return {"sucesso": True, "stdout": str(linhas), "stderr": ""}
    except sqlite3.Error as e:
        return {"sucesso": False, "stdout": "", "stderr": str(e)}


def run_snippet(bloco: dict) -> dict:
    if bloco["linguagem"] == "python":
        return run_python(bloco["codigo"])
    elif bloco["linguagem"] == "sql":
        return run_sql(bloco["codigo"])
    return {"sucesso": False, "stdout": "", "stderr": f"Linguagem nao suportada: {bloco['linguagem']}"}