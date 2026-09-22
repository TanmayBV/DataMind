"""
app.py
------
Day 7: Streamlit front-end for the NL2SQL query engine.

Wraps query_engine.ask() (Days 3-5: few-shot retrieval + validation)
in a simple chat-style UI, with the few-shot toggle and generated-SQL
transparency built in Days 3-4 exposed as UI controls instead of a CLI
'toggle' command.

Run locally:
    streamlit run query_engine/app.py

Deploy free:
    Push this repo to GitHub, then deploy on
    https://share.streamlit.io (Streamlit Community Cloud) or
    https://huggingface.co/spaces (Hugging Face Spaces, Streamlit SDK).
    Set GROQ_API_KEY and DATABASE_URL as secrets in the deploy settings —
    never commit them to the repo (see .env.example / .gitignore).
"""

import os
import sys
import time

import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "config"))
sys.path.insert(0, os.path.dirname(__file__))

st.set_page_config(page_title="NL2SQL — Ask Your Database", page_icon="🗄️", layout="centered")


@st.cache_resource
def load_chain():
    """Cached so the LLM client and FAISS index only load once per
    session, not on every question."""
    import nl2sql_chain as chain
    llm = chain.get_llm()
    return chain, llm


def render_sidebar():
    st.sidebar.title("🗄️ NL2SQL")
    st.sidebar.markdown(
        "Ask questions about the employee database in plain English. "
        "The system generates SQL, validates it against a schema "
        "whitelist and safety rules, then runs it."
    )
    use_few_shot = st.sidebar.toggle(
        "Few-shot retrieval (Day 4)", value=True,
        help="ON: retrieves similar validated examples via FAISS before "
             "generation. OFF: zero-shot baseline (Day 3). Toggle this to "
             "compare quality live — this is exactly what Day 6's "
             "evaluation measures in aggregate.",
    )
    show_sql = st.sidebar.toggle("Show generated SQL", value=True)

    st.sidebar.divider()
    st.sidebar.markdown(
        "**Try asking:**\n"
        "- How many active civil engineers are there?\n"
        "- Who is working on the GPP project?\n"
        "- How many contractors work in Moscow?\n\n"
        "**Try a blocked query (safety layer, Day 5):**\n"
        "- What is the average salary of engineers?"
    )
    return use_few_shot, show_sql


def render_result(sql, columns, rows, show_sql, elapsed):
    if show_sql:
        st.code(sql, language="sql")

    if sql.startswith("REFUSED"):
        st.warning("🚫 Blocked by business rules — this question asks for "
                    "sensitive data (e.g. salary), which this system never exposes.")
        return

    if columns is None and isinstance(rows, str):
        st.error(f"🚫 Rejected by the validation layer: {rows}")
        return

    if not rows:
        st.info("Query ran successfully but returned no rows.")
        return

    import pandas as pd
    df = pd.DataFrame(rows, columns=columns)
    st.dataframe(df, use_container_width=True)
    st.caption(f"{len(rows)} row(s) · {elapsed:.2f}s")


def main():
    st.title("Ask your database")
    st.caption(
        "A RAG-driven NL2SQL demo over a synthetic, intentionally messy "
        "HR dataset — cleaned, schema-validated, and safety-checked. "
        "[See the full build write-up on GitHub]"
        "(https://github.com/YOUR_USERNAME/nl2sql-rag)."
    )

    use_few_shot, show_sql = render_sidebar()

    try:
        chain, llm = load_chain()
    except Exception as e:
        st.error(
            f"Could not initialize the query engine: {e}\n\n"
            "Make sure GROQ_API_KEY and DATABASE_URL are set as secrets "
            "in your deployment settings (or in .env if running locally)."
        )
        st.stop()

    if "history" not in st.session_state:
        st.session_state.history = []

    question = st.chat_input("Ask a question about the employee database...")

    if question:
        with st.spinner("Generating SQL..."):
            start = time.time()
            try:
                sql, columns, rows = chain.ask(question, llm=llm, use_few_shot=use_few_shot)
            except Exception as e:
                sql, columns, rows = "", None, f"Error: {e}"
            elapsed = time.time() - start

        st.session_state.history.append({
            "question": question, "sql": sql, "columns": columns,
            "rows": rows, "elapsed": elapsed, "few_shot": use_few_shot,
        })

    for turn in reversed(st.session_state.history):
        with st.chat_message("user"):
            st.write(turn["question"])
        with st.chat_message("assistant"):
            mode_label = "few-shot" if turn["few_shot"] else "zero-shot"
            st.caption(f"mode: {mode_label}")
            render_result(turn["sql"], turn["columns"], turn["rows"], show_sql, turn["elapsed"])

    if not st.session_state.history:
        st.info("👋 Ask a question above to get started, or try one of the "
                 "example questions in the sidebar.")


if __name__ == "__main__":
    main()
