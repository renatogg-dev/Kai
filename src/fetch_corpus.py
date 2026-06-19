import json
import requests
from pathlib import Path

RAW_DIR = Path("corpus/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

SOURCES = {
    "python_sqlite3.html": "https://docs.python.org/3/library/sqlite3.html",
    "python_datetime.html": "https://docs.python.org/3/library/datetime.html",
    "python_datastructures.html": "https://docs.python.org/3/tutorial/datastructures.html",
    "python_controlflow.html": "https://docs.python.org/3/tutorial/controlflow.html",
    "python_classes.html": "https://docs.python.org/3/tutorial/classes.html",
    "python_errors.html": "https://docs.python.org/3/tutorial/errors.html",
    "python_modules.html": "https://docs.python.org/3/tutorial/modules.html",
    "sqlite_select.html": "https://www.sqlite.org/lang_select.html",
    "sqlite_aggfunc.html": "https://www.sqlite.org/lang_aggfunc.html",
    "sqlite_createtable.html": "https://www.sqlite.org/lang_createtable.html",
    "postgres_select.html": "https://www.postgresql.org/docs/current/sql-select.html",
    "postgres_aggregate.html": "https://www.postgresql.org/docs/current/functions-aggregate.html",
    "postgres_datatype.html": "https://www.postgresql.org/docs/current/datatype.html",
}

headers = {"User-Agent": "Mozilla/5.0 (projeto-kai-portfolio)"}
manifest = {}

for filename, url in SOURCES.items():
    dest = RAW_DIR / filename
    print(f"Baixando {url} -> {dest}")
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding  
    dest.write_text(resp.text, encoding="utf-8")
    manifest[filename] = url

(RAW_DIR / "manifest.json").write_text(
    json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
)
print("Concluido.")