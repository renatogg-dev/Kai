# Kai — Multilingual RAG for Python + SQL Documentation

Retrieval-Augmented Generation system that answers questions in **Portuguese**
over technical documentation written in **English** (Python, SQLite, and
PostgreSQL). Beyond the retrieval + generation pipeline, the project includes
an **evaluation harness** with recall/MRR/faithfulness metrics and an
**execution loop** that runs and self-corrects the code it generates.

## Features

- **Multilingual retrieval.** `multilingual-e5-base` embeddings let Portuguese
  queries retrieve the right chunk from English documentation, with no
  intermediate translation step.
- **Evaluation harness.** 18-question golden set with ground truth, measuring
  `recall@k`, `MRR`, and `faithfulness` (via LLM-as-judge).
- **Execution loop.** When a response contains code, it's executed in an
  isolated sandbox; on failure, the traceback is fed back to the model for
  correction, up to 3 attempts.
- **Intent detection.** The execution loop only fires when the question asks
  for code generation, not on illustrative examples inside conceptual answers.
- **Conversational memory.** Follow-up questions ("what about PostgreSQL?")
  are rewritten into standalone questions before retrieval, using the
  conversation history.

## Architecture

```
Question (PT) → [Query Rewriting w/ history] → [Multilingual e5 Retrieval]
              → [Grounded Generation, Claude] → Answer
                                                     ↓
                                    [Execution Loop, if code generation intent]
                                    runs in sandbox → fails? → self-corrects (max 3x)
```

- **Embedding:** `intfloat/multilingual-e5-base`, local, with contextual chunk
  headers (`[SQLite (SQL)] section: text`) to reduce ambiguity between
  syntactically similar sources (SQLite vs. PostgreSQL).
- **Vector store:** ChromaDB, persisted to disk.
- **Generation and judge:** Claude via the Anthropic API.
- **Execution sandbox:** isolated `subprocess` (no network, no inherited
  environment variables, timeout) for Python; in-memory SQLite for SQL syntax
  validation.
- **Interface:** Streamlit, with chat and an evaluation dashboard.

## Evaluation results

18-question golden set (9 Python, 6 SQLite, 3 PostgreSQL), covering retrieval
and code generation.

| Metric | Result |
|---|---|
| Recall@5 | 94.4% |
| MRR | 0.833 |
| Faithfulness (answers grounded in context) | 83.3% |

By category:

| Category | Recall@5 | MRR |
|---|---|---|
| Python | 100% | 0.944 |
| SQLite | 83.3% | 0.583 |
| PostgreSQL | 100% | 1.000 |

### Execution loop — before vs. after

| | Without loop | With loop |
|---|---|---|
| Execution success rate | 66.7% | 83.3% |

The loop fixed 2 out of 6 code cases that would otherwise have failed,
including a real SQL syntax error, automatically corrected within 3 attempts.

### About the faithfulness judge

The system allows **composing** documented syntax into new code (e.g., using
`dict` + `for`, both documented, to write a word-frequency-count function that
doesn't literally exist in the docs). The first version of the prompt treated
this as near-hallucination and refused legitimate tasks; the current version
distinguishes "inventing a fact" from "composing real syntax to solve
something new," and the faithfulness judge was updated to reflect that same
distinction.

### Known limitations

- **Ambiguity between topically overlapping files.** A question about `GROUP
  BY` with aggregation in PostgreSQL can be answered from either
  `postgres_select.html` or `postgres_aggregate.html` — the golden set
  accepts both as correct in this case.
- **Retrieval favors dense reference pages over smaller expression pages.** A
  question about the SQL string concatenation operator (`||`) doesn't
  reliably surface the (small) `sqlite_expr.html` page in the top 5, when
  competing against larger pages in the corpus. A targeted keyword-boost fix
  improved this case but regressed 3 others — it was reverted after
  measurement, and remains a candidate for future improvement (specificity-
  based re-ranking, not keyword-based).
- **The execution loop validates Python and SQLite only.** Validating
  PostgreSQL would require a real Postgres container, since the dialects
  diverge enough that validating against SQLite would be inaccurate.

## Stack

Python 3.11, ChromaDB, `sentence-transformers` (multilingual-e5-base), Claude
API (Anthropic), Streamlit, Plotly, BeautifulSoup4.

## Running it

```powershell
git clone https://github.com/renatogg-dev/Kai
cd kai
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create a `.env` file in the project root with `ANTHROPIC_API_KEY=your_key`.

Build the index (first run, or after changing the corpus):

```powershell
python -m src.ingestion.fetch_corpus
python -m src.ingestion.ingest
python -m src.indexing.index
```

Start the interface:

```powershell
streamlit run app.py
```

Or, on Windows, double-click `run_kai.bat`.

Run the full evaluation:

```powershell
python -m eval.run_eval
python -m eval.run_eval_execution
```

## Project structure

```
kai/
├── app.py                     # Streamlit interface (chat + dashboard)
├── run_kai.bat                # Quick-start shortcut (Windows)
├── corpus/
│   ├── raw/                   # Raw downloaded HTML
│   └── chunks/                # Processed chunks (.jsonl)
├── src/
│   ├── ingestion/              # Corpus download + chunking
│   ├── indexing/                # Embeddings + vector indexing
│   ├── rag/                     # Retrieval, generation, query rewriting, pipeline
│   ├── execution/                # Sandbox + execution loop
│   └── diagnostics/              # Corpus inspection scripts
├── eval/
│   ├── golden_set.jsonl          # 18 questions with ground truth
│   ├── metrics.py                 # recall@k, MRR, faithfulness
│   ├── run_eval.py                # Retrieval/generation evaluation
│   └── run_eval_execution.py       # Execution loop evaluation
└── store/                        # Persisted vector index (ChromaDB)
```

## Roadmap

- PostgreSQL execution sandbox via container.
- Retrieval re-ranking (or cross-encoder) to reduce reliance on raw embedding
  weight when small pages compete against dense ones.
- Expanding the golden set for stronger statistical significance on the
  execution loop.
