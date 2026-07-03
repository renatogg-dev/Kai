# Kai — RAG Multilíngue para Documentação Python + SQL

Um sistema de Retrieval-Augmented Generation que responde perguntas em **português**
sobre documentação técnica em **inglês** (Python, SQLite e PostgreSQL), com dois
diferenciais que vão além de um RAG de tutorial: um **eval harness** com métricas
reais e um **execution loop** que testa e autocorrige o código que gera.

## Por que este projeto existe

A maioria dos projetos de RAG de portfólio para por aqui: indexar uns documentos,
plugar um LLM, mostrar que "funciona". Este projeto tenta responder uma pergunta
mais difícil: **como eu sei que funciona, e o quanto?**

## Diferenciais

- **Retrieval multilíngue de verdade.** Embeddings com `multilingual-e5-base`
  permitem que perguntas em português encontrem o chunk certo em documentação
  inglesa — sem tradução intermediária.
- **Eval harness.** Um golden set de 18 perguntas com gabarito mede `recall@k`,
  `MRR` e `faithfulness` (via LLM-as-judge), gerando números reproduzíveis em vez
  de "parece que funciona".
- **Execution loop.** Quando a resposta contém código, ele é executado de verdade
  em sandbox isolado; se falhar, o traceback volta pro modelo para autocorreção,
  até 3 tentativas. O ganho desse mecanismo é medido, não assumido (ver abaixo).
- **Detecção de intenção.** O execution loop só dispara quando a pergunta pede
  geração de código (não em exemplos ilustrativos dentro de respostas conceituais).
- **Memória conversacional.** Perguntas de seguimento ("e no PostgreSQL?") são
  reescritas como perguntas autônomas antes do retrieval, usando o histórico da
  conversa.

## Arquitetura

```
Pergunta (PT) → [Query Rewriting c/ histórico] → [Retrieval multilíngue e5]
              → [Geração fundamentada, Claude] → Resposta
                                                     ↓
                                    [Execution Loop, se for pedido de código]
                                    roda em sandbox → falha? → autocorrige (max 3x)
```

- **Embedding:** `intfloat/multilingual-e5-base`, local, com contextual chunk
  headers (`[SQLite (SQL)] secao: texto`) para reduzir ambiguidade entre fontes
  sintaticamente parecidas (SQLite vs. PostgreSQL).
- **Vector store:** ChromaDB, persistido em disco.
- **Geração e judge:** Claude via API Anthropic.
- **Sandbox de execução:** `subprocess` isolado (sem rede, sem variáveis de
  ambiente herdadas, timeout) para Python; SQLite em memória para validação
  sintática de SQL.
- **Interface:** Streamlit, com chat conversacional e dashboard de avaliação.

## Resultados de avaliação

Golden set de 18 perguntas (9 Python, 6 SQLite, 3 PostgreSQL), cobrindo retrieval
e geração de código.

| Métrica | Resultado |
|---|---|
| Recall@5 | **94.4%** |
| MRR | **0.833** |
| Faithfulness (respostas fundamentadas no contexto) | **83.3%** |

Por categoria:

| Categoria | Recall@5 | MRR |
|---|---|---|
| Python | 100% | 0.944 |
| SQLite | 83.3% | 0.583 |
| PostgreSQL | 100% | 1.000 |

### Execution loop — antes vs. depois

| | Sem loop | Com loop |
|---|---|---|
| Taxa de sucesso na execução | 66.7% | **83.3%** |

O loop corrigiu 2 de 6 casos de código que falhariam sem ele — incluindo um erro de
sintaxe SQL real, corrigido automaticamente em até 3 tentativas.

### Nota metodológica: o judge de faithfulness

O sistema autoriza explicitamente a **composição** de sintaxe documentada em código
novo (ex.: usar `dict` + `for`, ambos documentados, para escrever uma função de
contagem de frequência que não existe literalmente na doc). O primeiro system
prompt tratava isso como quase-alucinação e recusava tarefas legítimas; o prompt
final distingue "inventar um fato" de "compor sintaxe real para resolver algo
novo" — e o judge de faithfulness foi ajustado para refletir essa mesma distinção.

### Limitações conhecidas

- **Ambiguidade entre arquivos tematicamente sobrepostos.** Uma pergunta sobre
  `GROUP BY` com agregação no PostgreSQL pode legitimamente ter a resposta em
  `postgres_select.html` ou `postgres_aggregate.html` — o golden set foi ajustado
  para aceitar ambos como corretos nesse caso, refletindo a realidade da
  documentação, não para inflar o número.
- **Retrieval favorece páginas de referência densas sobre páginas de expressão
  menores.** Uma pergunta sobre o operador de concatenação SQL (`||`) não traz de
  forma confiável a página `sqlite_expr.html` (pequena) para o top-5, quando
  compete com páginas maiores e mais estabelecidas do corpus. Uma tentativa de
  correção via keyword boost pontual **melhorou esse caso mas regrediu 3 outros**
  — foi revertida deliberadamente após medição, porque o ganho agregado era
  negativo. Fica documentado como candidato a melhoria futura (re-ranking ou
  boost por especificidade, não por palavra-chave).
- **Execution loop v1 valida apenas Python e SQLite.** Validação de PostgreSQL
  exigiria um container com Postgres real (os dialetos divergem o suficiente para
  que validar contra SQLite fosse impreciso) — fica de roadmap v2.

## Stack

Python 3.11, ChromaDB, `sentence-transformers` (multilingual-e5-base), Claude API
(Anthropic), Streamlit, Plotly, BeautifulSoup4.

## Como rodar

```powershell
git clone <url-do-repo>
cd kai
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Crie um `.env` na raiz com `ANTHROPIC_API_KEY=sua_chave`.

Reconstrua o índice (primeira vez, ou após alterar o corpus):

```powershell
python -m src.ingestion.fetch_corpus
python -m src.ingestion.ingest
python -m src.indexing.index
```

Inicie a interface:

```powershell
streamlit run app.py
```

Ou, no Windows, dê duplo-clique em `iniciar_kai.bat`.

Rode a avaliação completa:

```powershell
python -m eval.run_eval
python -m eval.run_eval_execution
```

## Estrutura do projeto

```
kai/
├── app.py                     # Interface Streamlit (chat + dashboard)
├── iniciar_kai.bat            # Atalho de inicializacao (Windows)
├── corpus/
│   ├── raw/                   # HTML bruto baixado
│   └── chunks/                # Chunks processados (.jsonl)
├── src/
│   ├── ingestion/              # Download + chunking do corpus
│   ├── indexing/               # Embeddings + indexacao vetorial
│   ├── rag/                    # Retrieval, geracao, reescrita de query, pipeline
│   ├── execution/               # Sandbox + execution loop
│   └── diagnostics/             # Scripts de inspecao do corpus
├── eval/
│   ├── golden_set.jsonl         # 18 perguntas com gabarito
│   ├── metrics.py                # recall@k, MRR, faithfulness
│   ├── run_eval.py               # Avaliacao de retrieval/geracao
│   └── run_eval_execution.py      # Avaliacao do execution loop
└── store/                       # Indice vetorial persistido (ChromaDB)
```

## Roadmap

- Sandbox de execução para PostgreSQL via container.
- Re-ranking de retrieval (ou cross-encoder) para reduzir a dependência de peso
  bruto de embedding em casos de páginas pequenas competindo com páginas densas.
- Expansão do golden set para maior significância estatística no execution loop.
- Health/biomedical RAG como próxima peça de portfólio, reaproveitando esta
  arquitetura.
