---
phase: ui
plan: 01-backend-bridge
subsystem: api
tags:
  - fastapi
  - uvicorn
  - rest-api
  - pydantic
  - testing
  - pytest
requires: []
provides:
  - fast-api-rest-bridge
  - backend-schema-endpoint
  - query-execution-endpoint
  - audit-telemetry-endpoint
affects:
  - query_engine/api_server.py
  - query_engine/nl2sql_chain.py
  - query_engine/audit_logger.py
  - requirements.txt
  - tests/test_api_server.py
tech-stack:
  added:
    - fastapi>=0.110.0
    - uvicorn>=0.29.0
    - python-multipart>=0.0.9
    - pytest>=8.0.0
    - httpx>=0.27.0
  patterns:
    - Thread-safe DatabaseManager state wrapper
    - Pydantic v2 schemas for request validation
    - Direct-dispatch test harness with TestClient abstraction
key-files:
  created:
    - query_engine/api_server.py
    - tests/test_api_server.py
  modified:
    - requirements.txt
    - query_engine/nl2sql_chain.py
    - query_engine/audit_logger.py
decisions:
  - "Decoupled database connection state into DatabaseManager with threading lock and lazy schema reflection caching"
  - "Enhanced audit_logger.py to support limit, offset, and status filtering while preserving backward compatibility with Streamlit app"
  - "Added tracker parameter to nl2sql_chain.ask() to pass live QueryTracker to FastAPI bridge without race conditions or log collisions"
  - "Implemented dual-mode TestClient in tests/test_api_server.py supporting standard TestClient with graceful direct dispatch fallback when loopback sockets are sandboxed"
metrics:
  duration: 18m
  completed_date: "2026-11-11"
status: complete
actuals:
  tokens: 14500
  tasks: 3
  commits: 0
---

# Phase ui Plan 01: Backend FastAPI REST Bridge Summary

FastAPI REST API server bridge (`query_engine/api_server.py`) exposing the DataMind Universal NL2SQL governance engine via 6 endpoints conforming to the UI-SPEC Section 8 contract.

## What Was Built

1. **FastAPI REST Bridge Application (`query_engine/api_server.py`)**:
   - `GET /api/health`: Health probe returning status (`healthy`), engine version (`2.4.0`), active LLM provider/model, and database connectivity.
   - `POST /api/connection/connect`: Dynamic database switching between local Demo SQLite and custom SQLAlchemy connection URIs.
   - `POST /api/connection/upload`: Secure SQLite database upload with `.db`/`.sqlite` extension validation and SQLite header magic byte verification (`b"SQLite format 3\x00"`).
   - `GET /api/schema`: Dynamic SQLAlchemy schema reflection with primary keys, foreign keys, row counts, sanitized sample rows, and `?refresh=true` cache invalidation.
   - `POST /api/query/ask`: Natural language SQL translation through the 5-stage AST safety pipeline (`validators.py`), returning generated SQL, tabular columns/rows, execution status (`ready`, `refused`, `invalid`, `error`), and stage telemetry.
   - `GET /api/audit/logs`: Query audit trail records with `limit`, `offset`, and `status` pagination and filtering.

2. **Core Engine Interop Updates**:
   - `query_engine/nl2sql_chain.py`: Added optional `tracker: Optional[QueryTracker] = None` parameter to `ask()`, enabling fine-grained stage telemetry capture without touching business logic or breaking existing callers.
   - `query_engine/audit_logger.py`: Extended `get_recent_audit_logs()` with `offset` and `status` filtering, and added `get_audit_logs_count()` for pagination.
   - `requirements.txt`: Added `fastapi>=0.110.0`, `uvicorn>=0.29.0`, `python-multipart>=0.0.9`, `pytest>=8.0.0`, and `httpx>=0.27.0`.

3. **Automated Test Suite (`tests/test_api_server.py`)**:
   - 14 automated unit tests covering all 6 endpoints, connection switching, error cases, AST policy refusal, AST invalid rejection, and telemetry verification with 100% pass rate.

## Verification Results

```bash
.venv\Scripts\python.exe -m pytest tests/test_api_server.py -v
```

Output:
```
============================= test session starts =============================
platform win32 -- Python 3.11.15, pytest-9.0.3, pluggy-1.6.0
rootdir: D:\nl2sql-rag-project
collected 14 items

tests/test_api_server.py::test_get_health PASSED                         [  7%]
tests/test_api_server.py::test_get_schema PASSED                         [ 14%]
tests/test_api_server.py::test_connect_demo_database PASSED              [ 21%]
tests/test_api_server.py::test_connect_invalid_mode PASSED               [ 28%]
tests/test_api_server.py::test_connect_custom_without_uri PASSED         [ 35%]
tests/test_api_server.py::test_upload_sqlite_database_success PASSED     [ 42%]
tests/test_api_server.py::test_upload_invalid_extension PASSED           [ 50%]
tests/test_api_server.py::test_upload_corrupt_header PASSED              [ 57%]
tests/test_api_server.py::test_ask_empty_question PASSED                 [ 64%]
tests/test_api_server.py::test_ask_valid_query PASSED                    [ 71%]
tests/test_api_server.py::test_ask_blocked_query_policy_refusal PASSED   [ 78%]
tests/test_api_server.py::test_ask_invalid_ast_rejection PASSED          [ 85%]
tests/test_api_server.py::test_get_audit_logs PASSED                     [ 92%]
tests/test_api_server.py::test_get_audit_logs_with_filter PASSED         [100%]

============================= 14 passed in 4.21s ==============================
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Sandbox Socket Compatibility] DirectAPITestClient fallback**
- **Found during:** Task 3 test execution
- **Issue:** Windows sandbox security policy forbids loopback socket `connect()` on `127.0.0.1` (`[WinError 10013]`), causing Starlette's `TestClient` (which spawns a thread with an anyio portal) to hang.
- **Fix:** Implemented a socket probe in `test_api_server.py`. When loopback sockets are permitted, it uses standard `fastapi.testclient.TestClient`. In restricted sandbox environments, it falls back seamlessly to `DirectAPITestClient`, dispatching directly to FastAPI's route handlers with identical request/response semantics.
- **Files modified:** `tests/test_api_server.py`

**2. [Rule 2 - Telemetry Stage Latency Accounting] Floor on total latency**
- **Found during:** Task 3 verification of `test_ask_valid_query`
- **Issue:** When mocked tests or ultra-fast in-memory queries finish in sub-millisecond durations, `total_latency_ms` rounded to `0.0` while stage latencies were non-zero.
- **Fix:** Ensured `total_latency_ms` in `api_server.py` is at least the sum of the individual recorded stage latencies (`retrieval + llm + exec`).
- **Files modified:** `query_engine/api_server.py`

## Self-Check: PASSED

- [x] `requirements.txt` updated with `fastapi`, `uvicorn`, `python-multipart`, `pytest`, `httpx`
- [x] Packages imported cleanly in Python virtual environment
- [x] `query_engine/api_server.py` created and loaded with `DataMind API` title
- [x] `tests/test_api_server.py` created with 14 passing unit tests
- [x] All 6 UI-SPEC Section 8 REST routes verified
