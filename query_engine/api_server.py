"""
api_server.py
-------------
Production-grade FastAPI REST API server bridge for the DataMind Universal
NL2SQL Data Governance Engine.

Exposes RESTful endpoints conforming to UI-SPEC Section 8:
- GET  /api/health            -> Server health, provider, model & DB connectivity
- POST /api/connection/connect -> Switch to Demo or Custom database
- POST /api/connection/upload  -> Upload SQLite DB (.db, .sqlite) safely
- GET  /api/schema            -> Dynamic schema introspection with caching
- POST /api/query/ask         -> Natural language query through 5-stage AST safety pipeline
- GET  /api/audit/logs        -> Query audit trail inspection & telemetry
"""

import os
import sys
import time
import shutil
import tempfile
import threading
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, HTTPException, Query, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

# Ensure config and query_engine modules can be imported
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "config"))

from config import (
    BLOCKED_COLUMNS,
    DATA_DIR,
    DATABASE_URL,
    GEMINI_API_KEY,
    GROQ_API_KEY,
    GROQ_MODEL,
    LLM_MODEL,
    LLM_PROVIDER,
)
from db_manager import (
    create_db_engine,
    fetch_table_sample_rows,
    get_or_create_demo_sqlite,
    introspect_schema,
    normalize_db_url,
)
from sqlalchemy import create_engine as sa_create_engine
from nl2sql_chain import (
    DEFAULT_BUSINESS_RULES,
    DEFAULT_SCHEMA_DESCRIPTION,
    ask,
    get_default_engine,
)
from audit_logger import (
    QueryTracker,
    get_audit_logs_count,
    get_recent_audit_logs,
    init_audit_db,
)
from validators import SCHEMA_WHITELIST

# ---------------------------------------------------------------------------
# App Initialization & CORS
# ---------------------------------------------------------------------------
app = FastAPI(
    title="DataMind API",
    version="2.4.0",
    description="Universal NL2SQL Data Governance & Natural Language Query Engine REST Bridge",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Thread-safe Database State Manager
# ---------------------------------------------------------------------------
class DatabaseManager:
    """Manages active database connection, dialect, and schema cache thread-safely."""

    def __init__(self):
        self._lock = threading.Lock()
        self._engine: Optional[Engine] = None
        self._dialect: str = "sqlite"
        self._display_name: str = "Local HR ERP (SQLite Demo)"
        self._is_default_schema: bool = True
        self._cached_schema: Optional[List[Dict[str, Any]]] = None
        self._cached_whitelist: Optional[Dict[str, set]] = None
        self._cached_description: Optional[str] = None

    def get_engine_info(self):
        with self._lock:
            if self._engine is None:
                self._init_default_under_lock()
            return self._engine, self._dialect, self._display_name, self._is_default_schema

    def _init_default_under_lock(self):
        eng, dialect, disp = create_db_engine()
        self._engine = eng
        self._dialect = dialect
        self._display_name = disp
        self._is_default_schema = (
            (dialect == "sqlite" and "Demo" in disp) or ("DATABASE_URL" in disp)
        )
        self._cached_schema = None
        self._cached_whitelist = None
        self._cached_description = None

    def set_engine(self, engine: Engine, dialect: str, display_name: str, is_default: bool = False):
        with self._lock:
            self._engine = engine
            self._dialect = dialect
            self._display_name = display_name
            self._is_default_schema = is_default
            self._cached_schema = None
            self._cached_whitelist = None
            self._cached_description = None

    def get_schema(self, refresh: bool = False) -> List[Dict[str, Any]]:
        with self._lock:
            if self._engine is None:
                self._init_default_under_lock()

            if not refresh and self._cached_schema is not None:
                return self._cached_schema

            engine = self._engine
            inspector = inspect(engine)
            tables = []

            for table_name in inspector.get_table_names():
                cols = inspector.get_columns(table_name)
                col_names = [c["name"] for c in cols]
                col_types = {c["name"]: str(c.get("type", "TEXT")) for c in cols}

                pk_constraint = inspector.get_pk_constraint(table_name) or {}
                primary_keys = pk_constraint.get("constrained_columns", [])

                fk_list = inspector.get_foreign_keys(table_name) or []
                foreign_keys = [
                    {
                        "constrained": fk.get("constrained_columns", []),
                        "referred_table": fk.get("referred_table", ""),
                        "referred_columns": fk.get("referred_columns", []),
                    }
                    for fk in fk_list
                ]

                # Row count
                row_count = None
                try:
                    with engine.connect() as conn:
                        res = conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
                        row_count = res.scalar()
                except Exception:
                    try:
                        with engine.connect() as conn:
                            res = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                            row_count = res.scalar()
                    except Exception:
                        row_count = None

                # Safe sample rows (excludes blocked/sensitive columns)
                sample_cols, sample_rows = fetch_table_sample_rows(
                    engine=engine,
                    table_name=table_name,
                    columns=col_names,
                    blocked_columns=set(BLOCKED_COLUMNS),
                    limit=3,
                )

                tables.append({
                    "name": table_name,
                    "columns": col_names,
                    "column_types": col_types,
                    "primary_keys": primary_keys,
                    "foreign_keys": foreign_keys,
                    "row_count": row_count,
                    "sample_columns": sample_cols,
                    "sample_rows": sample_rows,
                })

            self._cached_schema = tables
            return tables


db_state = DatabaseManager()


# ---------------------------------------------------------------------------
# Helper serialization functions
# ---------------------------------------------------------------------------
def _serialize_cell(val: Any) -> Any:
    """Ensures row cells are JSON serializable."""
    if val is None:
        return None
    if isinstance(val, (int, float, bool, str)):
        return val
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, (bytes, bytearray)):
        return "<binary>"
    return str(val)


def _serialize_rows(rows: Optional[List[Any]]) -> Optional[List[List[Any]]]:
    if rows is None:
        return None
    serialized = []
    for r in rows:
        if isinstance(r, (list, tuple)):
            serialized.append([_serialize_cell(c) for c in r])
        else:
            serialized.append([_serialize_cell(r)])
    return serialized


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------
class ConnectRequest(BaseModel):
    mode: str = Field(..., description="Connection mode: 'demo' or 'custom'")
    custom_uri: Optional[str] = Field(None, description="Custom database connection URI")


class QueryRequest(BaseModel):
    question: str = Field(..., description="Natural language question to translate to SQL")
    use_few_shot: bool = Field(False, description="Enable few-shot semantic retrieval")
    blocked_columns: Optional[List[str]] = Field(None, description="List of columns blocked by policy")
    custom_rules: Optional[str] = Field(None, description="Custom prompt / business rules override")


# ---------------------------------------------------------------------------
# Global Exception Handlers
# ---------------------------------------------------------------------------
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Internal Server Error: {str(exc)}"},
    )


# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------
@app.get("/api/health")
def get_health():
    """Engine health, LLM provider info, and active database connection probe."""
    engine, dialect, _, _ = db_state.get_engine_info()
    db_connected = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_connected = True
    except Exception:
        db_connected = False

    provider = LLM_PROVIDER or ("groq" if GROQ_API_KEY else "gemini")
    model = GROQ_MODEL if provider == "groq" else LLM_MODEL

    return {
        "status": "healthy",
        "version": "2.4.0",
        "llm_provider": provider,
        "llm_model": model,
        "database_connected": db_connected,
        "dialect": dialect,
    }


@app.post("/api/connection/connect")
def connect_database(req: ConnectRequest):
    """Connect to Demo SQLite or custom database URI."""
    mode = (req.mode or "").strip().lower()
    if mode == "demo":
        try:
            sqlite_uri = get_or_create_demo_sqlite()
            eng = sa_create_engine(sqlite_uri)
            dialect = "sqlite"
            disp = "Local HR ERP (SQLite Demo)"
            db_state.set_engine(eng, dialect, disp, is_default=True)
            tables = db_state.get_schema(refresh=True)
            return {
                "success": True,
                "dialect": dialect,
                "display_name": disp,
                "table_count": len(tables),
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Connection Failed: Could not initialize demo database ({e})",
            )

    elif mode == "custom":
        if not req.custom_uri or not req.custom_uri.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Custom URI is required when mode is 'custom'.",
            )
        try:
            eng, dialect, disp = create_db_engine(req.custom_uri.strip())
            db_state.set_engine(eng, dialect, disp, is_default=False)
            tables = db_state.get_schema(refresh=True)
            return {
                "success": True,
                "dialect": dialect,
                "display_name": disp,
                "table_count": len(tables),
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Connection Failed: Could not connect to '{req.custom_uri}'. ({e})",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid mode '{req.mode}'. Expected 'demo' or 'custom'.",
        )


@app.post("/api/connection/upload")
def upload_sqlite_database(file: UploadFile = File(...)):
    """Accepts uploaded SQLite database file (.db, .sqlite), validates header, and mounts as active engine."""
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".db", ".sqlite", ".sqlite3"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only SQLite database files (.db, .sqlite, .sqlite3) are supported.",
        )

    # Persist uploaded file securely to a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite")
    try:
        shutil.copyfileobj(file.file, temp_file)
        temp_file.close()
    except Exception as e:
        if os.path.exists(temp_file.name):
            os.remove(temp_file.name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to persist uploaded database file: {e}",
        )

    # Validate SQLite header magic bytes
    try:
        with open(temp_file.name, "rb") as f:
            header = f.read(16)
        if not header.startswith(b"SQLite format 3\x00"):
            os.remove(temp_file.name)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is not a valid SQLite database (header mismatch).",
            )
    except HTTPException:
        raise
    except Exception as e:
        if os.path.exists(temp_file.name):
            os.remove(temp_file.name)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read uploaded database header: {e}",
        )

    # Mount SQLite engine
    try:
        sqlite_uri = f"sqlite:///{os.path.abspath(temp_file.name)}"
        eng, dialect, _ = create_db_engine(sqlite_uri)
        disp_name = f"Uploaded SQLite ({filename})"
        db_state.set_engine(eng, dialect, disp_name, is_default=False)
        tables = db_state.get_schema(refresh=True)
        return {
            "success": True,
            "dialect": "sqlite",
            "display_name": disp_name,
            "table_count": len(tables),
        }
    except Exception as e:
        if os.path.exists(temp_file.name):
            os.remove(temp_file.name)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to mount uploaded SQLite database: {e}",
        )


@app.get("/api/schema")
def get_schema(refresh: bool = Query(False, description="Force fresh SQLAlchemy schema reflection")):
    """Returns reflected database schema, columns, primary keys, foreign keys, row counts, and safe sample rows."""
    try:
        tables = db_state.get_schema(refresh=refresh)
        return {"tables": tables}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Schema introspection failed: {e}",
        )


@app.post("/api/query/ask")
def ask_query(req: QueryRequest):
    """Executes natural language query through the 5-stage AST safety pipeline and returns telemetry."""
    if not req.question or not req.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query question cannot be empty.",
        )

    engine, dialect, _, is_default = db_state.get_engine_info()
    tracker = QueryTracker(question=req.question.strip())

    try:
        sql, columns, rows = ask(
            question=req.question.strip(),
            use_few_shot=req.use_few_shot,
            engine=engine,
            dialect=dialect,
            business_rules=req.custom_rules,
            blocked_columns=req.blocked_columns,
            is_default_schema=is_default,
            tracker=tracker,
        )
    except Exception as e:
        tracker.set_execution_error(str(e), 0.0)
        sql = ""
        columns = None
        rows = f"EXECUTION_ERROR: {e}"

    # Determine status and payload
    is_valid = tracker.is_valid
    error_message: Optional[str] = tracker.error_message or None

    if tracker.status == "refused" or (sql and sql.startswith("REFUSED")):
        query_status = "refused"
        is_valid = False
        if not error_message:
            error_message = "Policy Refusal: sensitive financial or personal data requested."
        columns = None
        rows = None
    elif tracker.status in ("invalid", "rejected") or (
        columns is None and isinstance(rows, str) and rows.startswith("REJECTED")
    ):
        query_status = "invalid"
        is_valid = False
        if not error_message:
            error_message = rows if isinstance(rows, str) else "AST Validation Failed."
        columns = None
        rows = None
    elif tracker.status == "error" or (
        columns is None and isinstance(rows, str) and rows.startswith("EXECUTION_ERROR")
    ):
        query_status = "error"
        is_valid = False
        if not error_message:
            error_message = rows if isinstance(rows, str) else "Query execution failed."
        columns = None
        rows = None
    else:
        query_status = "ready"
        is_valid = True
        error_message = None

    stage_sum = round(
        tracker.retrieval_latency_ms + tracker.llm_latency_ms + tracker.exec_latency_ms, 2
    )
    total_ms = round(tracker.total_latency_ms, 2)
    if total_ms < stage_sum:
        total_ms = stage_sum

    telemetry = {
        "retrieval_latency_ms": round(tracker.retrieval_latency_ms, 2),
        "llm_latency_ms": round(tracker.llm_latency_ms, 2),
        "exec_latency_ms": round(tracker.exec_latency_ms, 2),
        "total_latency_ms": total_ms,
        "retrieved_examples_count": tracker.retrieved_examples_count,
    }

    serialized_rows = _serialize_rows(rows) if isinstance(rows, list) else None

    return {
        "query_id": tracker.query_id,
        "question": req.question.strip(),
        "status": query_status,
        "is_valid": is_valid,
        "generated_sql": sql,
        "columns": columns,
        "rows": serialized_rows,
        "error_message": error_message,
        "telemetry": telemetry,
    }


@app.get("/api/audit/logs")
def get_audit_logs(
    limit: int = Query(50, ge=1, le=500, description="Max logs to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    status: Optional[str] = Query("all", description="Status filter: all, ready, refused, invalid, error"),
):
    """Fetch query audit trail records with fine-grained stage latency telemetry."""
    try:
        init_audit_db()
        filter_status = None if (not status or status.lower() == "all") else status
        total = get_audit_logs_count(status=filter_status)
        logs = get_recent_audit_logs(limit=limit, offset=offset, status=filter_status)
        return {
            "total": total,
            "logs": logs,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch audit logs: {e}",
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
