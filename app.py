import json
import sys
from pathlib import Path

import streamlit as st
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.rag.intent import is_code_generation_request
from src.rag.pipeline import ask
from src.execution.sandbox import extract_code_blocks
from src.execution.verify_loop import verify_and_correct

st.set_page_config(page_title="Kai — RAG Python/SQL", page_icon="🐍", layout="wide")


@st.cache_resource
def warmup():
    from src.rag.retrieve import _get_model, _get_collection
    _get_model()
    _get_collection()
    return True


warmup()

if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------- SIDEBAR ----------
with st.sidebar:
    st.title("🐍 Kai")
    st.caption("RAG sobre documentação Python + SQL (SQLite/PostgreSQL)")

    page = st.radio("Navegação", ["💬 Chat", "📊 Eval Dashboard"])

    st.divider()
    dbms_filter = st.selectbox("Filtrar por SGBD", ["Todos", "sqlite", "postgresql"])
    executar_codigo = st.checkbox("Execution loop (valida/autocorrige código)", value=True)

    if st.button("🗑️ Limpar conversa"):
        st.session_state.messages = []
        st.rerun()

dbms = None if dbms_filter == "Todos" else dbms_filter

# ---------- PÁGINA CHAT ----------
if page == "💬 Chat":
    st.title("Kai — RAG Python + SQL")

    # Renderiza o histórico
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

            if msg["role"] == "assistant":
                if msg.get("exec_result"):
                    exec_result = msg["exec_result"]
                    status = "✅ Código validado" if exec_result["sucesso_final"] else "❌ Código não passou na verificação"
                    with st.expander(f"Verificação de execução — {status}"):
                        for t in exec_result["tentativas"]:
                            icone = "✅" if t["sucesso"] else "❌"
                            st.markdown(f"**{icone} Tentativa {t['numero']}**")
                            st.code(t["codigo"])
                            st.text(t["stdout"] if t["sucesso"] else t["stderr"])

                if msg.get("hits"):
                    with st.expander("Fontes usadas"):
                        for hit in msg["hits"]:
                            meta = hit["metadata"]
                            st.markdown(f"- `{meta['arquivo']}` | {meta['secao']} (dist={hit['distance']:.3f})")

    # Input de chat (fixo embaixo, estilo ChatGPT)
    query = st.chat_input("Pergunte sobre Python ou SQL...")

    if query:
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)

        with st.chat_message("assistant"):
            with st.spinner("Buscando contexto e gerando resposta..."):
                historico_para_ask = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages[:-1]  # exclui a pergunta atual, que acabou de ser adicionada
                ]
                result = ask(query, k=5, dbms=dbms, history=historico_para_ask)
            st.markdown(result["answer"])

            if result["retrieval_query"] != result["query"]:
                st.caption(f"🔍 Interpretada para busca como: *{result['retrieval_query']}*")
            exec_result = None
            blocos = extract_code_blocks(result["answer"])
            eh_pedido_de_codigo = is_code_generation_request(query)

            if blocos and executar_codigo and eh_pedido_de_codigo:
                with st.spinner("Validando código no sandbox..."):
                    exec_result = verify_and_correct(query, result["answer"])
                status = "✅ Código validado" if exec_result["sucesso_final"] else "❌ Código não passou na verificação"
                with st.expander(f"Verificação de execução — {status}"):
                    for t in exec_result["tentativas"]:
                        icone = "✅" if t["sucesso"] else "❌"
                        st.markdown(f"**{icone} Tentativa {t['numero']}**")
                        st.code(t["codigo"])
                        st.text(t["stdout"] if t["sucesso"] else t["stderr"])
            elif blocos and not eh_pedido_de_codigo:
                st.caption("ℹ️ Código de exemplo ilustrativo — verificação de execução não aplicada (pergunta conceitual, não pedido de geração).")
            with st.expander("Fontes usadas"):
                for hit in result["hits"]:
                    meta = hit["metadata"]
                    st.markdown(f"- `{meta['arquivo']}` | {meta['secao']} (dist={hit['distance']:.3f})")

        st.session_state.messages.append({
            "role": "assistant",
            "content": result["answer"],
            "hits": result["hits"],
            "exec_result": exec_result,
        })

# ---------- PÁGINA EVAL DASHBOARD ----------
else:
    st.title("Resultados de Avaliação")

    baseline_path = Path("eval/resultados_baseline.json")
    execution_path = Path("eval/resultados_execution.json")

    if not baseline_path.exists():
        st.warning("Rode `python -m eval.run_eval` primeiro para gerar os resultados.")
    else:
        resultados = json.loads(baseline_path.read_text(encoding="utf-8"))
        n = len(resultados)

        recall_medio = sum(r["recall_at_k"] for r in resultados) / n
        mrr_medio = sum(r["reciprocal_rank"] for r in resultados) / n
        faith_sim = sum(1 for r in resultados if r["faithfulness"] == "sim") / n

        col1, col2, col3 = st.columns(3)
        col1.metric("Recall@5", f"{recall_medio:.1%}")
        col2.metric("MRR", f"{mrr_medio:.3f}")
        col3.metric("Faithfulness", f"{faith_sim:.1%}")

        st.markdown("### Recall@5 por categoria")
        categorias = ["python", "sqlite", "postgresql"]
        valores = []
        for cat in categorias:
            subset = [r for r in resultados if r["categoria"] == cat]
            valores.append(sum(r["recall_at_k"] for r in subset) / len(subset) if subset else 0)

        fig = go.Figure(go.Bar(x=categorias, y=valores, text=[f"{v:.0%}" for v in valores], textposition="auto"))
        fig.update_layout(yaxis_tickformat=".0%", yaxis_range=[0, 1], height=350)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### Itens individuais")
        st.dataframe(resultados, use_container_width=True)

    if execution_path.exists():
        st.markdown("---")
        st.markdown("### Execution Loop — antes vs. depois")
        exec_resultados = json.loads(execution_path.read_text(encoding="utf-8"))
        n_exec = len(exec_resultados)

        taxa_sem = sum(r["sem_loop_sucesso"] for r in exec_resultados) / n_exec
        taxa_com = sum(r["com_loop_sucesso"] for r in exec_resultados) / n_exec

        fig2 = go.Figure(go.Bar(
            x=["Sem loop", "Com loop"],
            y=[taxa_sem, taxa_com],
            text=[f"{taxa_sem:.0%}", f"{taxa_com:.0%}"],
            textposition="auto",
            marker_color=["#d62728", "#2ca02c"],
        ))
        fig2.update_layout(yaxis_tickformat=".0%", yaxis_range=[0, 1], height=350)
        st.plotly_chart(fig2, use_container_width=True)

        corrigidos = sum(1 for r in exec_resultados if r["corrigido"])
        st.caption(f"O execution loop corrigiu {corrigidos} de {n_exec} casos que falhariam sem ele.")