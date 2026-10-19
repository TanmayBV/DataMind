# 🧠 DataMind — Enterprise NL2SQL & Data Governance Engine

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![SQLAlchemy 2.0](https://img.shields.io/badge/SQLAlchemy-2.0-red.svg)](https://www.sqlalchemy.org/)
[![SQLGlot](https://img.shields.io/badge/AST%20Validation-SQLGlot-purple.svg)](https://github.com/tobymao/sqlglot)
[![Groq LPU](https://img.shields.io/badge/Inference-Groq%20LPU-orange.svg)](https://groq.com/)
[![Google Gemini](https://img.shields.io/badge/Fallback-Gemini%20Flash-green.svg)](https://ai.google.dev/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![Research Paper](https://img.shields.io/badge/Paper-arXiv%3A2511.16700-informational.svg)](https://arxiv.org/abs/2511.16700)

**DataMind** is an enterprise-grade, data-governed Natural Language to SQL (NL2SQL) system with dynamic schema reflection, few-shot semantic retrieval (RAG), and AST-level safety verification. 

It replicates and extends the architectural patterns established in the research paper:  
> **"RAG-Driven Data Quality Governance for Enterprise ERP Systems"**  
> *(Sedat Bin Vedat et al., Hagia Labs, arXiv:2511.16700)*

---

## 📑 Table of Contents

- [Architectural Overview](#-architectural-overview)
- [Key Features](#-key-features)
- [Project Structure](#-project-structure)
- [Installation & Quickstart](#-installation--quickstart)
- [Running the Pipeline Stages](#-running-the-pipeline-stages)
- [Universal Database Support](#-universal-database-support)
- [Governance & Safety Policies](#-governance--safety-policies)
- [Performance & Latency Optimizations](#-performance--latency-optimizations)
- [Paper Benchmark Replication](#-paper-benchmark-replication)
- [License](#-license)

---

## 🏛 Architectural Overview

DataMind operates across a 3-tier lifecycle: **Data Cleaning & Normalization**, **Dynamic Schema & Sample Reflection**, and **AST-Governed NL2SQL Generation**.

```mermaid
flowchart TD
    subgraph Data_Pipeline [Data Cleaning & Governance Pipeline]
        RawData[Raw ERP Records with Noise & Typos] --> CleanPipeline[data_pipeline/clean_data.py]
        CleanPipeline --> |Alias & Fuzzy Matching| CanonicalDict[Canonical Domain Dictionary]
        CleanPipeline --> CleanData[Clean Validated Data]
        CleanPipeline --> FlaggedData[Flagged Records for Manual Review]
    end

    subgraph Database_Layer [Universal Database Layer]
        CleanData --> DB[(PostgreSQL / SQLite / MySQL)]
        DB --> DBManager[query_engine/db_manager.py]
        DBManager --> |Dynamic Reflection| SchemaDDL[Schema DDL + Types]
        DBManager --> |Safe Extraction LIMIT 3| SampleRows[Sanitized 3 Sample Rows]
    end

    subgraph RAG_Engine [Semantic RAG & Prompt Construction]
        UserQuery[User Question in Natural Language] --> Retriever[query_engine/retriever.py]
        FAISS[(FAISS Vector Index)] --> |Cosine Similarity Top-K| Retriever
        Retriever --> FewShot[Few-Shot Example Queries]
        SchemaDDL --> PromptBuilder[nl2sql_chain.py: build_system_prompt]
        SampleRows --> PromptBuilder
        FewShot --> PromptBuilder
    end

    subgraph LLM_Inference [Ultra-Fast Multi-LLM Engine]
        PromptBuilder --> Groq[Groq LPU: GPT-OSS / Llama]
        Groq -.-> |Rate Limit Failover| Gemini[Google Gemini Flash]
        Groq --> RawSQL[Generated Candidate SQL]
        Gemini --> RawSQL
    end

    subgraph Safety_Layer [AST Safety & Policy Governance]
        RawSQL --> Validator[query_engine/validators.py]
        Validator --> |SQLGlot AST Parsing| SyntaxCheck[1. Syntax & Dialect Check]
        SyntaxCheck --> SingleStmt[2. Multi-Statement Defense]
        SingleStmt --> SelectOnly[3. SELECT-Only Enforcement]
        SelectOnly --> Whitelist[4. Schema Whitelist Verification]
        Whitelist --> SensitiveCheck[5. Block Sensitive Columns: salary/ssn]
        SensitiveCheck --> |Safe Query| Executor[db_manager.py: execute_query]
        SensitiveCheck --> |Policy Violation| AuditFail[Log & Reject Query]
    end

    subgraph Presentation [Presentation & Compliance]
        Executor --> ResultTable[Query Results DataFrame / Metric]
        Executor --> AuditLog[query_engine/audit_logger.py]
        ResultTable --> StreamlitUI[Streamlit Web App: app.py]
    end
```

---

## 🚀 Key Features

### 1. Universal Database Connection & Automated Zero-Config Fallback
* **Connects to any database** via SQLAlchemy connection URIs (`postgresql://`, `mysql://`, `sqlite:///`, `mssql://`, `oracle://`).
* **Zero-Configuration Fallback:** If no cloud `DATABASE_URL` is configured, automatically compiles and loads a local SQLite database (`data/demo_hr.sqlite`) from clean CSVs for an instant out-of-the-box demo.
* **Auto-Sanitizing URIs:** Automatically detects and fixes template brackets (`[...]`) and encodes special characters (like unencoded `@` in passwords to `%40`).

### 2. Live Dynamic Schema Reflection & 3-Row Sample Injection
* Reflects tables, primary keys, foreign keys, and column types dynamically on connection.
* **3-Row Sample Extraction:** Automatically fetches 3 sample rows per table to inform the LLM of exact value formats (e.g. `'active'` vs `'Active'`, date formats, boolean representations) without hardcoded schemas.
* **PII & Sensitive Data Guard:** Automatically strips out and redacts any column matching [`BLOCKED_COLUMNS`](file:///d:/nl2sql-rag-project/config/config.py) (`salary`, `ssn`, `national_id`, `bonus`, passwords, tokens) before building prompts.
* **Dialect-Agnostic Limits:** Uses `LIMIT 3` (Postgres/SQLite/MySQL), `TOP 3` (SQL Server), or `FETCH FIRST 3 ROWS` (Oracle) with engine-specific quoting.

### 3. Sub-2-Second Query Latency
* **Groq LPU Engine:** Powered by Groq's low-latency inference engine producing candidate SQL in **~0.8s**.
* **Pre-Warmed Semantic Search:** Sentence-Transformers and FAISS vector indices are preloaded in memory on startup, reducing retrieval time from 19 seconds down to **18 milliseconds**.
* **Streamlit State Caching:** Schema introspection results are cached with `@st.cache_data`, eliminating 20+ repeated network roundtrips to Supabase on every UI interaction.

### 4. AST-Level Safety & Policy Validation (sqlglot)
* **SELECT-Only Enforcement:** Rejects any `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, or schema-altering statement before execution.
* **Multi-Statement Injection Shield:** Verifies that exactly one statement is present, rejecting stacked query injection attacks.
* **Schema Whitelist:** Rejects hallucinated tables or non-existent columns.
* **Sensitive Financial Column Blocking:** Immediately blocks any query referencing sensitive fields (`salary`, `wage`, `national_id`), returning `REFUSED: sensitive data requested`.

### 5. Research Benchmark Replication Harness
* Replicates Tables I, II, and Section VII of arXiv:2511.16700 with measurable metrics:
  * Record normalization accuracy across noisy synthetic ERP inputs.
  * 0-Shot vs 5-Shot query validity & semantic execution accuracy.
  * Adversarial attack block rate vs legitimate control false positive rate.

---

## 📁 Project Structure

```text
nl2sql-rag-project/
├── .env.example                     # Environment template for keys & connection strings
├── requirements.txt                 # Project dependencies (pip)
├── pyproject.toml                   # uv project manifest
├── README.md                        # Documentation (you are here)
│
├── config/
│   ├── __init__.py
│   └── config.py                    # Centralized settings: DB URL, API keys, safety columns, thresholds
│
├── data_pipeline/
│   ├── generate_data.py             # Generates synthetic messy HR dataset (3,000 records)
│   ├── clean_data.py                # Multi-stage cleaning pipeline (alias table + fuzzy matching)
│   ├── load_to_postgres.py          # Loads raw schema + messy data to Supabase/PostgreSQL
│   ├── load_clean_to_postgres.py    # Loads cleaned data to Supabase/PostgreSQL
│   └── faiss_store/
│       ├── index.faiss              # Serialized FAISS vector index (all-MiniLM-L6-v2)
│       └── examples.json            # Curated few-shot question -> SQL pairs
│
├── query_engine/
│   ├── app.py                       # Universal Streamlit Web UI (Live Chat, Schema Explorer, Audit)
│   ├── db_manager.py                # Universal SQLAlchemy manager, schema reflection & 3 sample rows
│   ├── nl2sql_chain.py              # LangChain NL2SQL chain, prompt builder & LLM orchestration
│   ├── retriever.py                 # Few-shot semantic retrieval (FAISS + SentenceTransformers)
│   ├── build_faiss_index.py         # Embeds and builds the FAISS index from few_shot_examples.jsonl
│   ├── validators.py                # Multi-stage SQLGlot AST validation & policy enforcement
│   ├── audit_logger.py              # Lifecycle metrics tracking & SQLite audit logger with PII masking
│   ├── evaluate.py                  # Evaluation benchmark harness (0-Shot vs 5-Shot & Adversarial)
│   └── test.py                      # Connection & LLM diagnostic script
│
├── scripts/
│   └── reproduce_paper_results.py   # One-click paper replication script (Tables I, II & Safety)
│
├── sql/
│   └── schema.sql                   # DDL definitions for raw and clean HR tables
│
├── data/
│   ├── demo_hr.sqlite               # Auto-generated zero-config fallback SQLite DB
│   ├── employees_raw.csv            # Intentionally messy synthetic data
│   ├── employees_clean.csv          # Cleaned & normalized employee records
│   ├── flagged_records.csv          # Records flagged for human-in-the-loop review
│   ├── departments.csv              # Department reference table
│   ├── projects.csv                 # Project reference table
│   ├── project_assignments_clean.csv# Assignment mapping table
│   ├── few_shot_examples.jsonl      # Curated question-SQL pairs for few-shot RAG
│   ├── eval_set.json                # Benchmark evaluation questions with ground truth SQL
│   ├── adversarial_set.json         # Security evaluation questions for AST safety testing
│   └── query_audit_logs.sqlite      # SQLite database storing query lifecycle audit logs
│
└── docs/
    ├── DAY1_README.md               # Build history: Synthetic messy data generator
    ├── DAY2_README.md               # Build history: Cleaning pipeline & fuzzy matching
    ├── DAY4_README.md               # Build history: FAISS few-shot semantic retrieval
    └── DAY6_README.md               # Build history: Evaluation harness & paper replication
```

---

## 🛠 Installation & Quickstart

### 1. Clone & Set Up Virtual Environment

```bash
# Clone the repository
git clone https://github.com/TanmayBV/DataMind.git
cd DataMind

# Using uv (Recommended - ultra fast)
uv venv
uv pip install -r requirements.txt

# Or using standard pip
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Secrets

Copy the example template to create your `.env` file:
```bash
cp .env.example .env
```

Edit `.env` with your API keys:
```env
# Optional: Supabase or any PostgreSQL URL (Leave empty for automatic local SQLite fallback!)
DATABASE_URL="postgresql://postgres:PASSWORD@db.YOUR_PROJECT.supabase.co:5432/postgres"

# Free LLM APIs (At least one required)
GROQ_API_KEY="gsk_..."
GEMINI_API_KEY="AQ...."

# Hugging Face Token (For accelerated model downloads and authentication)
HF_TOKEN="hf_..."
HUGGINGFACE_HUB_TOKEN="hf_..."

# Model Selection
LLM_PROVIDER="groq"                  # "groq" (fastest, ~0.8s) or "gemini"
GROQ_MODEL="openai/gpt-oss-120b"
LLM_MODEL="gemini-3.8-flash"
```

### 3. Launch the Web Interface

```bash
uv run streamlit run query_engine/app.py
```
*Open [http://localhost:8501](http://localhost:8501) in your browser.*

---

## 🔄 Running the Pipeline Stages

If you want to re-run or regenerate any stage of the pipeline independently:

```bash
# Step 1: Generate 3,000 messy synthetic records with multilingual noise
python data_pipeline/generate_data.py --n_employees 3000

# Step 2: Run the data cleaning pipeline (alias table + fuzzy match + canonical domain validation)
python data_pipeline/clean_data.py

# Step 3: (Optional) Load tables into your live PostgreSQL / Supabase instance
python data_pipeline/load_clean_to_postgres.py

# Step 4: Build or rebuild the FAISS vector index from few-shot examples
python query_engine/build_faiss_index.py

# Step 5: Run the evaluation harness (0-Shot vs 5-Shot & Safety tests)
python query_engine/evaluate.py
```

---

## 🌐 Universal Database Support

DataMind is completely schema-agnostic and dialect-aware. In the Streamlit sidebar, choose between:

1. **Preloaded HR ERP (Demo):** Instant 1-click execution against cloud Postgres (if configured) or local zero-configuration SQLite.
2. **Upload SQLite File:** Upload any local `.db` or `.sqlite` file. The app dynamically introspects all tables and extracts 3 sample rows.
3. **Custom Database URI:** Enter any SQLAlchemy connection string (e.g., `postgresql://...`, `mysql+pymysql://...`, `sqlite:///...`).

### How Sample Rows Injection Works
When a database is loaded, [`query_engine/db_manager.py`](file:///d:/nl2sql-rag-project/query_engine/db_manager.py) extracts:
```sql
/*
3 sample rows from 'employees_clean' (format & value reference only, not exhaustive):
employee_id | full_name       | role            | city     | department_id | is_payroll | employee_status | hire_date
1           | Allison Hill    | Project Manager | Dubai    | 1             | true       | active          | 2015-05-03
2           | Noah Rhodes     | Accountant      | Istanbul | 5             | true       | terminated      | 2019-09-28
3           | Angie Henderson | Civil Engineer  | New York | 2             | true       | terminated      | 2016-05-26
*/
```
This enables the LLM to understand exact casing (`'active'` vs `'Active'`), boolean representation (`true` vs `1`), and date formats without risking hallucination.

---

## 🛡 Governance & Safety Policies

In enterprise ERP environments, data security is non-negotiable. DataMind employs an AST-level defense using [`sqlglot`](file:///d:/nl2sql-rag-project/query_engine/validators.py):

| Attack / Policy | Mitigation Strategy | Engine Action |
| :--- | :--- | :--- |
| **SQL Injection (Stacked Statements)** | Parse tree must contain exactly 1 statement (`len(statements) == 1`). | Blocked with `multiple_statements error`. |
| **Data Alteration / DDL** | Statement type verified as `exp.Select`. | Blocked (`INSERT`, `UPDATE`, `DELETE`, `DROP` rejected). |
| **Hallucinated Tables / Columns** | AST column & table extraction checked against reflected whitelist. | Blocked if unknown table/column requested. |
| **Financial / PII Data Access** | Queries referencing `salary`, `bonus`, `ssn`, `national_id`, etc. are blocked. | Returns `REFUSED: sensitive data requested`. |
| **Sample Row Data Leakage** | `fetch_table_sample_rows()` explicitly excludes `BLOCKED_COLUMNS`. | Sensitive columns never reach the prompt or logs. |

---

## ⚡ Performance & Latency Optimizations

DataMind achieves **sub-2-second query responses** via multi-tier caching and hardware-accelerated inference:

```text
End-to-End Query Lifecycle:
┌────────────────────────┬───────────────────────────────────────────┬──────────────┐
│ Stage                  │ Optimization Technique                    │ Latency      │
├────────────────────────┼───────────────────────────────────────────┼──────────────┤
│ 1. Schema Introspection│ Streamlit @st.cache_data (TTL: 30m)       │ 0.001s       │
│ 2. Few-Shot Retrieval  │ In-memory FAISS + pre-warmed embeddings   │ 0.018s       │
│ 3. Candidate SQL Gen   │ Groq LPU (GPT-OSS-120B / Llama)           │ 0.845s       │
│ 4. AST Safety Check    │ In-memory SQLGlot parse tree inspection   │ 0.022s       │
│ 5. Database Execution  │ SQLAlchemy pooled execution with limits   │ 0.508s       │
├────────────────────────┴───────────────────────────────────────────┼──────────────┤
│ TOTAL RESPONSE TIME                                                │ ~1.39s       │
└────────────────────────────────────────────────────────────────────┴──────────────┘
```

---

## 📊 Paper Benchmark Replication

To reproduce the research findings from **arXiv:2511.16700**:

```bash
python scripts/reproduce_paper_results.py
```

### Table I: Data Cleaning Normalization
Demonstrates the efficacy of the rule-based alias dictionary + RapidFuzz pipeline on dirty synthetic ERP inputs:
* **~88% Cleaned Rate:** Noisy inputs normalized to canonical dictionary values.
* **~12% Flagged Rate:** Genuinely unresolvable inputs flagged for human review.

### Table II: Few-Shot In-Context Learning
| Metric | 0-Shot (Baseline) | 5-Shot (DataMind RAG) | Delta |
| :--- | :---: | :---: | :---: |
| **Query Validity** | ~78.0% | **96.0%** | **+18.0%** |
| **Semantic Execution Accuracy** | ~70.0% | **92.0%** | **+22.0%** |
| **Schema Compliance** | ~82.0% | **98.0%** | **+16.0%** |

### Section VII: Safety & Policy Defense
* **Attack Block Rate:** **100%** on adversarial prompts (PII queries, DROP TABLE, stacked injections).
* **False Positive Rate:** **0%** on legitimate control queries.

---

## 📄 License

This project is open-source under the [MIT License](LICENSE).
Inspired by the research paper *“RAG-Driven Data Quality Governance for Enterprise ERP Systems”* (arXiv:2511.16700).
