"""
app.py
------
Universal, Schema-Agnostic NL2SQL Engine UI (Streamlit).

Features:
- Dual-mode database selection:
  1. Preloaded Enterprise HR Database (Instant 1-click demo)
  2. Upload SQLite Database (.db, .sqlite)
  3. Custom Database URI (PostgreSQL, MySQL, SQLite, etc.)
- Dynamic Schema Introspection & Live Schema Explorer
- Multi-dialect SQL generation (Postgres, SQLite, MySQL)
- sqlglot AST-level safety validation (SELECT-only, schema whitelist, sensitive column blocks)
- Few-shot semantic retrieval toggle (FAISS)
"""

import json
import os
import sys
import tempfile
import time
import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "config"))

from config import BLOCKED_COLUMNS, DATA_DIR
import nl2sql_chain as chain
from db_manager import create_db_engine, introspect_schema, execute_query
from audit_logger import get_recent_audit_logs
from sqlalchemy import create_engine

st.set_page_config(
    page_title="DataMind — Universal NL2SQL Engine",
    page_icon="🧠",
    layout="wide",
)


@st.cache_resource
def get_cached_llm():
    """Initializes and caches the LLM instance."""
    return chain.get_llm()


def get_default_connection():
    """Initializes default engine (Cloud Postgres or local SQLite demo)."""
    return create_db_engine()


def render_sidebar():
    st.sidebar.title("🧠 DataMind NL2SQL")
    st.sidebar.markdown(
        "RAG-driven natural language query engine with **automated schema reflection**, "
        "**SQLGlot AST validation**, and **zero-cost execution**."
    )

    st.sidebar.subheader("🔌 Database Connection")
    source_mode = st.sidebar.radio(
        "Select Database Source:",
        ["Preloaded HR ERP (Demo)", "Upload SQLite File", "Custom Database URI"],
        index=0,
    )

    engine = None
    dialect = "postgres"
    display_name = ""
    is_default = False

    if source_mode == "Preloaded HR ERP (Demo)":
        is_default = True
        try:
            engine, dialect, display_name = get_default_connection()
        except Exception as e:
            st.sidebar.error(f"Error loading demo database: {e}")

    elif source_mode == "Upload SQLite File":
        uploaded_file = st.sidebar.file_uploader(
            "Upload SQLite database (.db / .sqlite)",
            type=["db", "sqlite", "sqlite3"],
        )
        if uploaded_file is not None:
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f"uploaded_{uploaded_file.name}")
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            sqlite_uri = f"sqlite:///{temp_path.replace(os.sep, '/')}"
            try:
                engine = create_engine(sqlite_uri)
                dialect = "sqlite"
                display_name = f"Uploaded SQLite ({uploaded_file.name})"
            except Exception as e:
                st.sidebar.error(f"Failed to connect: {e}")
        else:
            st.sidebar.info("Upload any SQLite database file to query it.")

    elif source_mode == "Custom Database URI":
        custom_uri = st.sidebar.text_input(
            "Database Connection URI:",
            placeholder="postgresql://user:pass@host:5432/dbname",
            help="Supports postgresql://, mysql+pymysql://, sqlite:///",
        )
        if custom_uri:
            try:
                engine, dialect, display_name = create_db_engine(custom_uri)
                st.sidebar.success(f"Connected to {dialect.upper()}")
            except Exception as e:
                st.sidebar.error(f"Connection failed: {e}")
        else:
            st.sidebar.info("Enter a connection string to introspect your database.")

    st.sidebar.divider()

    schema_whitelist = {}
    schema_prompt = ""
    tables_meta = []

    if engine is not None:
        try:
            schema_whitelist, schema_prompt, tables_meta = introspect_schema(engine)
        except Exception as e:
            st.sidebar.error(f"Schema introspection error: {e}")

        with st.sidebar.expander(f"📊 Inspected Schema ({len(tables_meta)} tables)", expanded=False):
            for t in tables_meta:
                st.markdown(f"**`{t['name']}`** ({len(t['columns'])} cols, ~{t['row_count'] or 'N/A'} rows)")
                st.caption(", ".join(t["columns"][:8]) + ("..." if len(t["columns"]) > 8 else ""))

    st.sidebar.subheader("⚙️ Query Controls")
    use_few_shot = st.sidebar.toggle(
        "Few-shot semantic retrieval (FAISS)",
        value=is_default,
        disabled=not is_default,
        help="Few-shot examples are trained on the HR ERP schema. Automatically disabled on custom databases.",
    )
    show_sql = st.sidebar.toggle("Show generated SQL & AST details", value=True)

    with st.sidebar.expander("🛡️ Safety & Policy Rules", expanded=False):
        blocked_input = st.text_input(
            "Sensitive/Blocked Columns (comma-separated):",
            value=", ".join(BLOCKED_COLUMNS),
            help="Queries attempting to access these columns will be hard-rejected by AST analysis.",
        )
        custom_blocked = [c.strip().lower() for c in blocked_input.split(",") if c.strip()]

        custom_rules = st.text_area(
            "Custom Business Rules (optional):",
            value="" if not is_default else chain.DEFAULT_BUSINESS_RULES,
            height=120,
        )

    return {
        "engine": engine,
        "dialect": dialect,
        "display_name": display_name,
        "is_default": is_default,
        "whitelist": schema_whitelist,
        "schema_prompt": schema_prompt,
        "tables_meta": tables_meta,
        "use_few_shot": use_few_shot,
        "show_sql": show_sql,
        "blocked_columns": custom_blocked,
        "custom_rules": custom_rules,
    }


def render_query_result(sql, columns, rows, show_sql, elapsed):
    if show_sql:
        st.markdown("#### Generated SQL Query")
        st.code(sql, language="sql")

    if sql.startswith("REFUSED"):
        st.warning("🚫 **Refused by Business Safety Policy:** This question requests sensitive financial or PII data that is restricted.")
        return

    if columns is None and isinstance(rows, str):
        st.error(f"🚫 **Rejected by AST Validation Layer:**\n\n`{rows}`")
        return

    if not rows:
        st.info("Query executed successfully, but returned 0 rows.")
        return

    df = pd.DataFrame(rows, columns=columns)
    st.markdown("#### Query Results")

    # If it's a single scalar count/value (e.g. COUNT(*)), display a prominent metric card
    if len(rows) == 1 and len(columns) == 1:
        val = rows[0][0]
        st.metric(label=str(columns[0]).upper(), value=f"{val:,}" if isinstance(val, (int, float)) else str(val))
    else:
        try:
            st.dataframe(df, hide_index=True, width="stretch")
        except Exception:
            st.dataframe(df)

    st.caption(f"Returned {len(rows)} row(s) in {elapsed:.2f}s · Verified safe via `sqlglot` · Auto-redacted PII")


def main():
    ctx = render_sidebar()

    st.title("🧠 DataMind — NL2SQL Data Governance Engine")
    st.caption(
        "A scaled-down replication of 'RAG-Driven Data Quality Governance for Enterprise ERP Systems' (arXiv:2511.16700). "
        "Features automated schema introspection, FAISS few-shot RAG, and AST safety verification at $0 cost."
    )

    if ctx["engine"] is not None:
        table_count = len(ctx["tables_meta"])
        st.success(
            f"🟢 **Connected:** {ctx['display_name']} | **Dialect:** `{ctx['dialect'].upper()}` | "
            f"**Discovered Tables:** `{table_count}`"
        )
    else:
        st.warning("⚠️ Please select or connect a database from the sidebar to start asking questions.")
        st.stop()

    tab_chat, tab_benchmarks, tab_audit = st.tabs([
        "💬 Query Assistant",
        "📊 Paper Benchmarks",
        "📋 Query Audit & Lifecycle Logs"
    ])

    with tab_chat:
        if ctx["is_default"]:
            st.markdown("**Sample Questions (Click to test):**")
            cols = st.columns(4)
            sample_q1 = "How many active civil engineers are there?"
            sample_q2 = "Who is working on the GPP project?"
            sample_q3 = "How many contractors work in London?"
            sample_q4 = "What is the average salary of employees?"

            if cols[0].button("👷 Active Engineers", use_container_width=True):
                st.session_state.pending_question = sample_q1
            if cols[1].button("📂 GPP Project Staff", use_container_width=True):
                st.session_state.pending_question = sample_q2
            if cols[2].button("🏙️ London Contractors", use_container_width=True):
                st.session_state.pending_question = sample_q3
            if cols[3].button("🛡️ Test Blocked Salary", use_container_width=True):
                st.session_state.pending_question = sample_q4

        try:
            llm = get_cached_llm()
        except Exception as e:
            st.error(
                f"Could not initialize LLM client: {e}\n\n"
                "Please ensure `GEMINI_API_KEY` is configured in `.env` or deployment secrets."
            )
            st.stop()

        if "history" not in st.session_state:
            st.session_state.history = []

        pending_q = st.session_state.pop("pending_question", None)
        question = st.chat_input("Ask a question about your database in plain English...") or pending_q

        if question:
            with st.spinner(f"Generating and validating {ctx['dialect'].upper()} SQL..."):
                start = time.time()
                try:
                    sql, columns, rows = chain.ask(
                        question=question,
                        llm=llm,
                        use_few_shot=ctx["use_few_shot"],
                        engine=ctx["engine"],
                        schema_whitelist=ctx["whitelist"],
                        schema_description=ctx["schema_prompt"],
                        dialect=ctx["dialect"],
                        business_rules=ctx["custom_rules"] or None,
                        blocked_columns=ctx["blocked_columns"],
                        is_default_schema=ctx["is_default"],
                    )
                except Exception as e:
                    sql, columns, rows = "", None, f"Execution Error: {e}"
                elapsed = time.time() - start

            st.session_state.history.append({
                "question": question,
                "sql": sql,
                "columns": columns,
                "rows": rows,
                "elapsed": elapsed,
                "dialect": ctx["dialect"],
            })

        for turn in reversed(st.session_state.history):
            with st.chat_message("user"):
                st.write(turn["question"])
            with st.chat_message("assistant"):
                render_query_result(
                    turn["sql"],
                    turn["columns"],
                    turn["rows"],
                    ctx["show_sql"],
                    turn["elapsed"],
                )

        if not st.session_state.history:
            st.info("👋 Ask a question above or choose a sample question to see the engine in action.")

    with tab_benchmarks:
        st.subheader("📊 Research Paper Results Replication")
        st.markdown(
            "Empirical results replicating **Table I (Record Normalization)** and **Table II (Few-Shot Performance)** "
            "from *'RAG-Driven Data Quality Governance for Enterprise ERP Systems'*."
        )

        # Table I: Data Cleaning Transformations
        st.markdown("#### Table I: Examples of Record Normalization (Data Cleaning Pipeline)")
        before_after_path = os.path.join(DATA_DIR, "before_after_examples.csv")
        if os.path.exists(before_after_path):
            df_norm = pd.read_csv(before_after_path)
            try:
                st.dataframe(df_norm, width="stretch")
            except TypeError:
                st.dataframe(df_norm)
        else:
            st.info("Run `python data_pipeline/clean_data.py` to generate Table I samples.")

        # Table II: Evaluation Results
        st.markdown("#### Table II: Effect of Few-Shot Learning on SQL Performance")
        eval_results_path = os.path.join(DATA_DIR, "eval_results.json")
        if os.path.exists(eval_results_path):
            with open(eval_results_path) as f:
                res = json.load(f)
            z = res.get("zero_shot", {})
            f_shot = res.get("few_shot", {})
            saf = res.get("safety", {})

            t2_data = [
                {
                    "Metric": "Valid SQL Queries (%)",
                    "0-Shot Baseline": f"{z.get('pass_rate', 0)*100:.1f}%",
                    "5-Shot Retrieval": f"{f_shot.get('pass_rate', 0)*100:.1f}%",
                    "Improvement (Diff)": f"{(f_shot.get('pass_rate', 0) - z.get('pass_rate', 0))*100:+.1f}%",
                },
                {
                    "Metric": "Semantic Accuracy (%)",
                    "0-Shot Baseline": f"{z.get('semantic_accuracy', 0)*100:.1f}%",
                    "5-Shot Retrieval": f"{f_shot.get('semantic_accuracy', 0)*100:.1f}%",
                    "Improvement (Diff)": f"{(f_shot.get('semantic_accuracy', 0) - z.get('semantic_accuracy', 0))*100:+.1f}%",
                },
                {
                    "Metric": "Avg. Latency (s)",
                    "0-Shot Baseline": f"{z.get('avg_latency_s', 0):.2f}s",
                    "5-Shot Retrieval": f"{f_shot.get('avg_latency_s', 0):.2f}s",
                    "Improvement (Diff)": f"{f_shot.get('avg_latency_s', 0) - z.get('avg_latency_s', 0):+.2f}s",
                },
            ]
            st.table(pd.DataFrame(t2_data))

            st.markdown("#### 🛡️ Safety & Policy Enforcement Metrics (Section VII)")
            col_s1, col_s2, col_s3 = st.columns(3)
            col_s1.metric("Attack Block Rate", f"{saf.get('attack_block_rate', 0)*100:.1f}%", help="Goal: 100%")
            col_s2.metric("False Positive Rate", f"{saf.get('false_positive_rate', 0)*100:.1f}%", help="Goal: 0%")
            col_s3.metric("Overall Safety Compliance", f"{saf.get('correct', 0)}/{saf.get('total', 1)} ({saf.get('correct', 0)/max(saf.get('total', 1), 1)*100:.1f}%)")
        else:
            st.info("Run `python query_engine/evaluate.py` to compute and display live Table II benchmark results.")

    with tab_audit:
        st.subheader("📋 Query Audit Trail & Lifecycle Telemetry")
        st.caption("Replicates Algorithm 1 Phase 7: Persistent query execution audit logs with stage-by-stage latency tracking.")

        audit_logs = get_recent_audit_logs(limit=50)
        if audit_logs:
            df_audit = pd.DataFrame(audit_logs)
            try:
                st.dataframe(df_audit, width="stretch")
            except TypeError:
                st.dataframe(df_audit)
            st.caption(f"Showing last {len(audit_logs)} logged interaction(s). Saved in `data/query_audit_logs.sqlite`.")
        else:
            st.info("No query logs recorded yet. Ask a question in the chat tab to generate your first audit record.")


if __name__ == "__main__":
    main()
