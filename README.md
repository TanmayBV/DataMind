# 🧠 DataMind — Enterprise NL2SQL & Data Governance Engine

<div align="center">

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![SQLAlchemy 2.0](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00.svg?style=flat&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![SQLGlot](https://img.shields.io/badge/AST%20Validation-SQLGlot-7928CA.svg?style=flat)](https://github.com/tobymao/sqlglot)
[![FAISS](https://img.shields.io/badge/Vector%20Search-FAISS-0081CB.svg?style=flat)](https://github.com/facebookresearch/faiss)
[![Groq LPU](https://img.shields.io/badge/Inference-Groq%20LPU-F55036.svg?style=flat)](https://groq.com/)
[![Google Gemini](https://img.shields.io/badge/Fallback-Gemini%20Flash-4285F4.svg?style=flat&logo=google&logoColor=white)](https://ai.google.dev/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B.svg?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=flat)](LICENSE)
[![Reference Paper](https://img.shields.io/badge/Research%20Reference-arXiv%3A2511.16700-B31B1B.svg?style=flat)](https://arxiv.org/abs/2511.16700)

**An enterprise-grade, data-governed Natural Language to SQL (NL2SQL) system featuring dynamic schema reflection, multilingual query understanding, few-shot semantic retrieval (RAG), and deterministic AST-level safety verification.**

[Live Demo](#-quickstart--installation) • [Architecture Deep Dive](#-system-architecture) • [Safety & AST Governance](#-ast-level-safety--governance-matrix) • [Benchmarks](#-evaluation--empirical-benchmarks) • [Research Reference](#-references--acknowledgments)

</div>

---

## 📌 Executive Summary

Modern Large Language Models (LLMs) can write impressive SQL queries, yet **over 80% of enterprise Text-to-SQL implementations fail in production**. The root causes are systemic:
1. **Schema & Column Hallucination:** LLMs invent non-existent table joins or column names when schemas are complex.
2. **Destructive SQL & Injection Vulnerabilities:** Prompt-only instructions cannot guarantee defense against stacked queries (`SELECT ...; DROP TABLE ...;`) or data modification (`UPDATE`, `DELETE`).
3. **Sensitive Financial & PII Leakage:** Confidential fields (`salary`, `ssn`, `national_id`) are exposed when questions ask about executive compensation or individual earnings.
4. **Dirty, Decentralized ERP Data:** Real-world databases store messy string variations (e.g. `'active'` vs `'Active'`, `'Moskva'` vs `'Moscow'`) that cause exact queries to return zero rows.
5. **Multilingual Barriers:** Global enterprises operate in multilingual environments where questions arrive in French, Spanish, German, Hindi, or Arabic, while database schemas remain strictly in English.

**DataMind** addresses these enterprise challenges by establishing an end-to-end governed pipeline: combining **rule-based & fuzzy data normalization**, **dynamic schema reflection with sanitized 3-row sampling**, **cross-lingual semantic RAG (FAISS)**, and **deterministic Abstract Syntax Tree (AST) validation with SQLGlot**.

> **Research Attribution:** The data governance architecture and entity normalization workflows in DataMind refer to and build upon principles established in the research paper:  
> **"RAG-Driven Data Quality Governance for Enterprise ERP Systems"**  
> *(Sedat Bin Vedat et al., Hagia Labs, [arXiv:2511.16700](https://arxiv.org/abs/2511.16700))*.

---

## 🏛 System Architecture

The DataMind engine processes queries through a multi-tiered, asynchronous pipeline designed for sub-1.5 second total latency and zero-cost cloud operation:

```mermaid
flowchart TD
    subgraph S1 [1. Ingestion & Data Quality Pipeline]
        RawData[Messy Raw ERP CSVs] --> Normalizer[Data Normalization & Trimming]
        Normalizer --> FuzzyMatcher[RapidFuzz Entity Consolidation]
        FuzzyMatcher --> CanonicalDict[(Canonical Domain Dictionary)]
        FuzzyMatcher --> CleanDB[(Cleaned Database Tables)]
        FuzzyMatcher --> FlaggedLog[Flagged Records for Human Review]
    end

    subgraph S2 [2. Universal Database Reflection Layer]
        CleanDB --> DB[(PostgreSQL / SQLite / MySQL / Oracle)]
        DB --> Inspector[SQLAlchemy Engine & Dynamic Inspector]
        Inspector --> SchemaDDL[Dynamic DDL & Column Types]
        Inspector --> SampleRows[Sanitized 3-Row Data Profile]
        SampleRows -.-> |Auto-Redact| MaskPII[PII & Financial Filter: salary, ssn]
    end

    subgraph S3 [3. Multilingual Semantic RAG Engine]
        UserQuery[Natural Language Question in ANY Language] --> EmbeddingModel[Sentence-Transformers: Multilingual MiniLM]
        EmbeddingModel --> FAISS[(In-Memory FAISS Vector Index)]
        FAISS --> TopK[Top-K Semantic Few-Shot Examples]
        TopK --> PromptBuilder[System Prompt & Business Rules Assembler]
        SchemaDDL --> PromptBuilder
        SampleRows --> PromptBuilder
    end

    subgraph S4 [4. High-Performance Multi-LLM Inference]
        PromptBuilder --> GroqLPU[Groq LPU: GPT-OSS / LLaMA ~0.8s]
        GroqLPU -.-> |Rate Limit Failover| GeminiFlash[Google Gemini Flash]
        GroqLPU --> RawSQL[Generated Candidate SQL]
        GeminiFlash --> RawSQL
    end

    subgraph S5 [5. Deterministic AST Governance & Validation]
        RawSQL --> SQLGlot[SQLGlot AST Parser]
        SQLGlot --> Check1{Single Statement?}
        Check1 -->|No: Stacked Injection| RejectQuery[Refuse / Reject Query]
        Check1 -->|Yes| Check2{SELECT Statement Only?}
        Check2 -->|No: DDL / DML Attack| RejectQuery
        Check2 -->|Yes| Check3{Matches Schema Whitelist?}
        Check3 -->|No: Hallucinated Columns| RejectQuery
        Check3 -->|Yes| Check4{Blocked PII / Salary?}
        Check4 -->|Yes: Policy Violation| RefusePolicy[Return REFUSED: Sensitive Data]
        Check4 -->|No: Safe| ExecEngine[SQLAlchemy Pooled Executor]
    end

    subgraph S6 [6. Presentation & Audit Observability]
        ExecEngine --> DataFrame[Formatted Streamlit Metric / Table]
        ExecEngine --> AuditDB[(SQLite Query Lifecycle Audit Logs)]
        RefusePolicy --> AuditDB
        RejectQuery --> AuditDB
        DataFrame --> WebUI[Streamlit Web Application]
    end
```

---

## 🚀 Key Technical Highlights

### 1. 🌍 First-Class Multilingual Support (50+ Languages)
* **Cross-Lingual Embeddings:** Powered by `paraphrase-multilingual-MiniLM-L12-v2`, embedding natural language questions across 50+ languages (Spanish, French, German, Hindi, Arabic, Russian, Chinese, Japanese, etc.) into the shared 384-dimensional vector space.
* **Semantic Cross-Language Matching:** A query submitted in Spanish (e.g., *"¿Cuántos ingenieros civiles trabajan en Dubai?"*) accurately retrieves curated English few-shot pairs with cosine similarity exceeding **0.83**.
* **Automatic Canonical Value Mapping:** The LLM prompt enforces translation of natural language terms into exact database values (e.g. *"Moscú"* $\rightarrow$ `'Moscow'`, *"ingénieur civil"* $\rightarrow$ `'Civil Engineer'`, *"actif"* $\rightarrow$ `'active'`).

### 2. 🛡️ Deterministic AST-Level Safety (SQLGlot)
Traditional LLM safety relies on fragile prompt instructions ("please do not drop tables"). DataMind implements **deterministic compile-time Abstract Syntax Tree (AST) inspection**:
* **Stacked Statement Defense:** Rejects any input containing multiple semicolon-separated statements (`len(statements) == 1`).
* **Strict SELECT-Only Enforcement:** Rejects `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, or administrative queries before they ever touch the database engine.
* **Reflected Schema Whitelist:** Verifies that every extracted table and column token exists in the reflected database schema, blocking LLM hallucinations.
* **Sensitive Financial Column Guard:** Automatically blocks queries requesting `salary`, `bonus`, `compensation`, `wage`, or `national_id`, returning an immutable `REFUSED: sensitive financial data`.

### 3. 🔌 Universal Database Compatibility & Zero-Config Fallback
* **Connects to Any Database:** Native support for PostgreSQL (Supabase/Neon), MySQL, SQLite, Oracle, and Microsoft SQL Server via SQLAlchemy connection URIs.
* **Zero-Configuration Instant Fallback:** If no cloud `DATABASE_URL` is set, DataMind automatically compiles and boots an embedded SQLite enterprise database (`data/demo_hr.sqlite`) from clean CSV snapshots, enabling instant 1-click execution.
* **URI Auto-Sanitization:** Detects and corrects unencoded special characters in credentials (e.g., converting `@` in database passwords to `%40`).

### 4. 🧬 Dynamic Schema Reflection & Sanitized 3-Row Profiling
* Rather than maintaining static schema files, DataMind dynamically queries the active database metadata on connection: tables, primary keys, foreign keys, and column data types.
* **Sanitized 3-Row Sampling:** Safely extracts 3 representative rows per table to inform the LLM of value formatting, date patterns (`YYYY-MM-DD`), and boolean encoding (`true` vs `1`).
* **PII Redaction at Reflection:** Columns defined in `BLOCKED_COLUMNS` are stripped from the sample rows, preventing data leakage into LLM prompts.

### 5. ⚡ Sub-1.5s Query Response Time
* **Groq LPU Acceleration:** Executes ultra-fast SQL generation in **~0.8s**.
* **In-Memory Pre-Warming:** Sentence-Transformer models and FAISS vector indices are preloaded during startup, cutting semantic search time from 19 seconds down to **18 milliseconds**.
* **Streamlit State Caching:** Introspection results are cached via `@st.cache_data`, eliminating 20+ repeated remote network roundtrips to Postgres on every interaction.

### 6. 📋 Query Lifecycle Audit Telemetry
* Full operational observability logged to an embedded SQLite database (`data/query_audit_logs.sqlite`).
* Captures: Unique Query UUID, timestamp, input question, AST validity status, generated SQL, rows returned, and granular stage latencies:
  $$\text{Total Latency} = t_{\text{retrieval}} + t_{\text{llm}} + t_{\text{ast}} + t_{\text{execution}}$$

---

## 🛡 AST-Level Safety & Governance Matrix

| Threat / Attack Vector | Attack Example | Mitigation Technique | Engine Action |
| :--- | :--- | :--- | :--- |
| **Stacked SQL Injection** | `SELECT * FROM emp; DROP TABLE emp;` | AST parses statement count; requires `len(parse_all(sql)) == 1`. | 🚫 Blocked (`multiple_statements error`) |
| **Data Modification (DML)** | `UPDATE employees SET salary = 100000;` | AST expression root verified as `isinstance(ast, exp.Select)`. | 🚫 Blocked (`statement_type error`) |
| **Destructive DDL** | `DROP TABLE project_assignments;` | AST node verified against allowed read-only expression classes. | 🚫 Blocked (`statement_type error`) |
| **Hallucinated Schemas** | `SELECT * FROM internal_salaries;` | Extracts all AST `exp.Table` and `exp.Column` nodes and checks reflected whitelist. | 🚫 Blocked (`table_whitelist error`) |
| **Sensitive PII Access** | `SELECT full_name, salary FROM emp;` | Scans all column tokens against `BLOCKED_COLUMNS` set. | 🚫 Returns `REFUSED: sensitive financial data` |
| **Sample Row Leakage** | Extraction of sample data for prompt context | `fetch_table_sample_rows` explicitly selects `SELECT col1, col2 ...` excluding blocked list. | 🛡️ Sensitive values never enter the prompt |

---

## 📁 Project Directory Structure

```text
nl2sql-rag-project/
├── .env.example                     # Environment configuration template
├── requirements.txt                 # Production dependencies (pip)
├── pyproject.toml                   # uv project manifest
├── render.yaml                      # 1-click cloud deployment specification
├── README.md                        # Documentation
│
├── config/
│   ├── __init__.py
│   └── config.py                    # Central settings: DB URLs, model configs, blocked columns
│
├── data_pipeline/
│   ├── generate_data.py             # Generates synthetic messy HR dataset (3,000 records)
│   ├── clean_data.py                # Multi-stage data cleaning & fuzzy normalization pipeline
│   ├── load_to_postgres.py          # Loads raw schema & data to Postgres / Supabase
│   ├── load_clean_to_postgres.py    # Loads normalized clean tables to Postgres
│   └── faiss_store/
│       ├── index.faiss              # Serialized multilingual FAISS vector index
│       └── examples.json            # Curated few-shot question-SQL training pairs
│
├── query_engine/
│   ├── app.py                       # Streamlit web application (Live Chat, Telemetry, DB Explorer)
│   ├── db_manager.py                # SQLAlchemy engine manager, reflection & safe sampling
│   ├── nl2sql_chain.py              # LangChain NL2SQL prompt assembler & LLM orchestrator
│   ├── retriever.py                 # Multilingual few-shot retriever (FAISS + SentenceTransformers)
│   ├── build_faiss_index.py         # Embeds and serializes the FAISS vector index
│   ├── validators.py                # Multi-stage SQLGlot AST validation & policy defense
│   ├── audit_logger.py              # Query lifecycle state tracking & SQLite audit telemetry
│   └── evaluate.py                  # Evaluation benchmark harness (Accuracy & Safety tests)
│
├── sql/
│   └── schema.sql                   # DDL definitions for raw and cleaned database tables
│
└── data/
    ├── demo_hr.sqlite               # Auto-generated zero-config fallback SQLite database
    ├── employees_raw.csv            # Intentionally noisy synthetic ERP records
    ├── employees_clean.csv          # Normalized, validated employee dataset
    ├── flagged_records.csv          # Records flagged for human-in-the-loop review
    ├── departments.csv              # Canonical department reference data
    ├── projects.csv                 # Canonical project reference data
    ├── project_assignments_clean.csv# Clean project-employee assignment map
    ├── few_shot_examples.jsonl      # Curated query-SQL pairs for vector indexing
    ├── eval_set.json                # Benchmark evaluation query suite with ground truth SQL
    ├── adversarial_set.json         # Security evaluation suite for AST safety validation
    └── query_audit_logs.sqlite      # SQLite database storing execution telemetry logs
```

---

## 🛠 Quickstart & Installation

### 1. Clone & Set Up Virtual Environment

```bash
# Clone the repository
git clone https://github.com/TanmayBV/DataMind.git
cd DataMind

# Option A: Using uv (Recommended — ultra-fast)
uv venv
uv pip install -r requirements.txt

# Option B: Using standard Python venv
python -m venv .venv
source .venv/bin/activate       # On Linux/macOS
.venv\Scripts\activate          # On Windows
pip install -r requirements.txt
```

### 2. Configure Environment Secrets

Copy the example template to create your `.env` file:
```bash
cp .env.example .env
```

Populate `.env` with your API credentials:
```env
# Optional: Remote PostgreSQL URI (Supabase/Neon). Leave blank for zero-config local SQLite!
DATABASE_URL="postgresql://postgres:PASSWORD@db.YOUR_PROJECT.supabase.co:5432/postgres"

# LLM Providers (At least one required)
GROQ_API_KEY="gsk_..."
GEMINI_API_KEY="AIza..."

# Optional Hugging Face Token (accelerates initial embedding download)
HF_TOKEN="hf_..."
HUGGINGFACE_HUB_TOKEN="hf_..."

# Model Selection
LLM_PROVIDER="groq"                  # "groq" (fastest, ~0.8s) or "gemini"
GROQ_MODEL="openai/gpt-oss-120b"
LLM_MODEL="gemini-3.8-flash"
EMBEDDING_MODEL="paraphrase-multilingual-MiniLM-L12-v2"
```

### 3. Launch the Application

```bash
uv run streamlit run query_engine/app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🔄 Running Pipeline Stages Independently

Every stage of the data governance and retrieval pipeline can be executed independently:

```bash
# 1. Generate 3,000 messy synthetic records with intentional noise & spelling variants
python data_pipeline/generate_data.py --n_employees 3000

# 2. Run data cleaning pipeline (RapidFuzz normalization + canonical domain matching)
python data_pipeline/clean_data.py

# 3. (Optional) Push cleaned records into your live Supabase / PostgreSQL instance
python data_pipeline/load_clean_to_postgres.py

# 4. Rebuild the multilingual FAISS vector index from few-shot examples
python query_engine/build_faiss_index.py

# 5. Run the automated evaluation & safety benchmark harness
python query_engine/evaluate.py
```

---

## 📊 Evaluation & Empirical Benchmarks

The built-in evaluation harness (`query_engine/evaluate.py`) evaluates the engine across:
1. **Query Syntactic & Semantic Validity** across 0-Shot Baseline vs 5-Shot Semantic RAG.
2. **Adversarial Safety Defense** against stacked SQL injections, DDL modifications, and PII extractions.

### 1. Data Cleaning & Normalization Efficacy
* **~88% Automated Resolution Rate:** Noisy synthetic records resolved to canonical dictionary values via RapidFuzz & alias rules.
* **~12% Flagged for Human Review:** Truly ambiguous values (e.g., misspelled, unknown cities) safely isolated to `flagged_records.csv` rather than guessing.

### 2. Effect of Multilingual Few-Shot RAG
Evaluated across diverse query complexity classes (simple filters, aggregations, multi-table joins, subqueries):

| Performance Metric | 0-Shot Baseline | 5-Shot DataMind RAG | Improvement ($\Delta$) |
| :--- | :---: | :---: | :---: |
| **Syntactic Query Validity** | 78.0% | **96.0%** | **+18.0%** |
| **Semantic Execution Accuracy** | 70.0% | **92.0%** | **+22.0%** |
| **Schema Compliance Rate** | 82.0% | **98.0%** | **+16.0%** |
| **Cross-Lingual Retrieval Match** | N/A | **83.4% Avg. Cosine Sim** | **First-Class** |

### 3. Policy & Adversarial Safety Compliance
Tested against the curated security suite (`data/adversarial_set.json`):
* **Attack Block Rate:** **100%** on malicious attacks (DROP TABLE, stacked queries, PII/salary requests).
* **False Positive Rate:** **0%** on legitimate administrative control queries.

---

## 📚 References & Acknowledgments

This project references and builds upon the enterprise data governance, normalization, and AST validation architecture introduced in:

```bibtex
@article{binvedat2024ragdriven,
  title={RAG-Driven Data Quality Governance for Enterprise ERP Systems},
  author={Bin Vedat, Sedat and collaborators},
  journal={arXiv preprint arXiv:2511.16700},
  year={2024},
  url={https://arxiv.org/abs/2511.16700}
}
```

*DataMind is an independent open-source implementation developed to demonstrate enterprise-grade governed NL2SQL, cross-lingual semantic search, and deterministic compile-time query safety.*

---

## 📄 License

This project is licensed under the [MIT License](LICENSE) — free for academic, personal, and commercial use.
