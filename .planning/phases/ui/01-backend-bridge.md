---
phase: ui
plan: 01-backend-bridge
type: execute
wave: 1
depends_on: []
files_modified:
  - requirements.txt
  - query_engine/api_server.py
  - tests/test_api_server.py
autonomous: true
requirements:
  - UI-01-FASTAPI-BRIDGE
estimate:
  tokens: 18000
  raw_tokens: 12000
  tasks: 3
  confidence: high
must_haves:
  truths:
    - "FastAPI server runs on port 8000 exposing /api/health, /api/connection/connect, /api/connection/upload, /api/schema, /api/query/ask, and /api/audit/logs"
    - "FastAPI server wraps query_engine/nl2sql_chain.py, db_manager.py, and audit_logger.py without altering core business logic"
    - "All routes pass automated pytest test suite in tests/test_api_server.py using TestClient with zero failures"
  artifacts:
    - "requirements.txt"
    - "query_engine/api_server.py"
    - "tests/test_api_server.py"
  key_links:
    - "api_server.py invokes db_manager.create_db_engine() and fetch_table_sample_rows() for schema reflection"
    - "api_server.py invokes nl2sql_chain.ask() for SQL generation and AST validation"
    - "api_server.py invokes audit_logger.get_recent_audit_logs() for telemetry inspection"
---

<objective>
Implement and verify the production-grade FastAPI REST API server bridge for the DataMind Universal NL2SQL Data Governance Engine.

Expose all core query engine capabilities via clean, well-typed RESTful endpoints conforming to the UI-SPEC Section 8 contract:
- Server health & environment probe (`GET /api/health`)
- Database connection switching & SQLite upload (`POST /api/connection/connect`, `POST /api/connection/upload`)
- Dynamic database schema introspection (`GET /api/schema`)
- NL2SQL query execution with AST validation & telemetry (`POST /api/query/ask`)
- Query audit trail inspection (`GET /api/audit/logs`)

Output:
- `requirements.txt`: Updated with FastAPI, Uvicorn, Multipart, Pytest, and Httpx dependencies
- `query_engine/api_server.py`: Complete FastAPI application with CORS and global error handlers
- `tests/test_api_server.py`: Comprehensive test suite verifying all routes
</objective>

<execution_context>
@~/.gemini/antigravity/gsd-core/workflows/execute-plan.md
@~/.gemini/antigravity/gsd-core/templates/summary.md
</execution_context>

<context>
@d:/nl2sql-rag-project/UI-SPEC.md
@d:/nl2sql-rag-project/query_engine/app.py
@d:/nl2sql-rag-project/query_engine/nl2sql_chain.py
@d:/nl2sql-rag-project/query_engine/db_manager.py
@d:/nl2sql-rag-project/query_engine/audit_logger.py
@d:/nl2sql-rag-project/query_engine/validators.py
@d:/nl2sql-rag-project/config/config.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Install Backend Dependencies & Update requirements.txt</name>
  <files>requirements.txt</files>
  <action>
1. Update `requirements.txt` to include backend API and testing dependencies:
   - `fastapi>=0.110.0`
   - `uvicorn>=0.29.0`
   - `python-multipart>=0.0.9`
   - `pytest>=8.0.0`
   - `httpx>=0.27.0`
2. Explicitly execute dependency installation into the active virtual environment:
   `pip install fastapi uvicorn python-multipart pytest httpx` (or `.venv\Scripts\python.exe -m pip install fastapi uvicorn python-multipart pytest httpx`).
3. Verify all packages import cleanly without version conflicts.
  </action>
  <verify>
    <automated>.venv\Scripts\python.exe -c "import fastapi, uvicorn, multipart, pytest, httpx; print('Dependencies OK')"</automated>
    <fails_when>ImportError is raised or exit code is non-zero</fails_when>
  </verify>
  <done>
    `requirements.txt` is updated, and fastapi, uvicorn, python-multipart, pytest, and httpx are successfully installed in the Python virtual environment.
  </done>
</task>

<task type="auto">
  <name>Task 2: Implement FastAPI REST Bridge Server</name>
  <files>query_engine/api_server.py</files>
  <action>
Create `query_engine/api_server.py` implementing the complete REST interface:
1. Configure `FastAPI` instance with title "DataMind API", version "2.4.0", and `CORSMiddleware` allowing `http://localhost:5173`, `http://localhost:3000`, and `*`.
2. Manage thread-safe active database connection state, defaulting to `create_db_engine()` from `db_manager.py`.
3. Implement `GET /api/health` returning `status`, `version`, `llm_provider`, `llm_model`, `database_connected`, and `dialect`.
4. Implement `POST /api/connection/connect` accepting `{"mode": "demo" | "custom", "custom_uri": str | None}`, updating active engine, introspecting schema, and returning `{success, dialect, display_name, table_count}`.
5. Implement `POST /api/connection/upload` accepting SQLite database upload (`multipart/form-data`), persisting to a secure temporary file using `tempfile.NamedTemporaryFile`, mounting with SQLite engine, and returning connection details.
6. Implement `GET /api/schema` returning reflected tables, column types, primary keys, foreign keys, row counts, and sanitized 3 sample rows. Support `?refresh=true` to force fresh SQLAlchemy reflection.
7. Implement `POST /api/query/ask` accepting `{"question": str, "use_few_shot": bool, "blocked_columns": list[str] | None, "custom_rules": str | None}`, invoking `nl2sql_chain.ask()`, and returning `{query_id, question, status, is_valid, generated_sql, columns, rows, error_message, telemetry}`.
8. Implement `GET /api/audit/logs` accepting `limit`, `offset`, and `status`, querying `get_recent_audit_logs()`, and returning `{total, logs}`.
9. Add global exception handlers returning consistent JSON `{detail: str}` with appropriate HTTP status codes.
  </action>
  <verify>
    <automated>.venv\Scripts\python.exe -c "from query_engine.api_server import app; assert app.title == 'DataMind API'; print('FastAPI app loaded')"</automated>
    <fails_when>ImportError or app initialization failure</fails_when>
  </verify>
  <done>
    `query_engine/api_server.py` exposes all 6 endpoints with CORS, Pydantic schemas, and error handling.
  </done>
</task>

<task type="auto">
  <name>Task 3: Automated Test Suite for API Server</name>
  <files>tests/test_api_server.py</files>
  <action>
Implement automated tests in `tests/test_api_server.py` using `fastapi.testclient.TestClient`:
1. Test `GET /api/health`: assert 200 OK, status="healthy", dialect="sqlite".
2. Test `GET /api/schema`: assert 200 OK, tables list contains "employees_clean", "departments", "projects", "project_assignments".
3. Test `POST /api/connection/connect`: assert 200 OK with mode="demo".
4. Test `POST /api/query/ask`:
   - Valid query: assert response contains query_id, is_valid=True, and status="ready".
   - Blocked query (e.g. salary): assert status="refused" and is_valid=False.
5. Test `GET /api/audit/logs`: assert total >= 0 and logs list returned.
  </action>
  <verify>
    <automated>.venv\Scripts\python.exe -m pytest tests/test_api_server.py -v</automated>
    <fails_when>Any test failure or unhandled exception in test suite</fails_when>
  </verify>
  <done>
    All API endpoints pass unit tests with 100% pass rate.
  </done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| Client Browser -> FastAPI API Bridge | Untrusted natural language queries, custom database connection strings, and uploaded SQLite database files cross into the backend engine. |
| FastAPI -> SQLAlchemy Engine | Generated SQL statements are executed against the target database engine. |
| FastAPI -> External LLM (Gemini / Groq) | User natural language prompts and schema descriptions cross external provider network boundaries. |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-ui-01 | Tampering | `/api/query/ask` | high | mitigate | All generated SQL passes through sqlglot AST validation (`validators.py`): SELECT-only enforcement, single-statement check, and schema whitelist enforcement prior to SQLAlchemy execution. |
| T-ui-02 | Information Disclosure | `/api/query/ask` & `/api/schema` | high | mitigate | Sensitive columns (`salary`, `bonus`, `ssn`, `compensation`) are hard-blocked at AST inspection. `fetch_table_sample_rows` excludes sensitive columns. |
| T-ui-03 | Elevation of Privilege | `/api/connection/connect` | high | mitigate | Custom database URIs are sanitized using `normalize_db_url()`. Connection timeout is strictly capped (3-5s). Pool pre-ping prevents connection hijacking. |
| T-ui-04 | Tampering | `/api/connection/upload` | medium | mitigate | Uploaded SQLite files are validated for `.db`/`.sqlite` extensions, written to isolated temporary files via `tempfile.NamedTemporaryFile`, and checked with SQLite header validation before mounting. |
| T-ui-05 | Denial of Service | `/api/query/ask` | medium | mitigate | Query execution is capped at 500 rows maximum (`max_rows=500` in `execute_query`). AST parsing runs before DB execution to catch unbounded cartesian joins or invalid syntax early. |
| T-ui-06 | Repudiation | `query_engine/audit_logger.py` | low | mitigate | Every query attempt (ready, refused, rejected, or error) is persistently logged with UUID `query_id`, ISO timestamp, prompt, SQL, and stage latencies in `data/query_audit_logs.sqlite`. |
| T-ui-SC | Tampering | npm / pip dependencies | high | mitigate | Only official Python packages from PyPI (`fastapi`, `uvicorn`, `python-multipart`, `pytest`, `httpx`) installed. No untrusted packages. |
</threat_model>

<verification>
.venv\Scripts\python.exe -m pytest tests/test_api_server.py -v
</verification>

<success_criteria>
FastAPI backend bridge passes all unit tests, adheres to UI-SPEC Section 8 contract, and exposes all 6 REST endpoints reliably.
</success_criteria>

<output>
Create `.planning/phases/ui/01-backend-bridge-SUMMARY.md` when execution completes.
</output>
