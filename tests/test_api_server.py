"""
test_api_server.py
------------------
Comprehensive automated test suite for DataMind FastAPI REST API Bridge.
Tests all endpoints conforming to the UI-SPEC Section 8 contract.
"""

import io
import os
import sys
import sqlite3
import tempfile
from typing import Any, Optional
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

# Force test execution to use local SQLite demo database without network lag
os.environ["DATABASE_URL"] = ""

import pytest
from fastapi import HTTPException, UploadFile
from pydantic import ValidationError

# Ensure root directory and query_engine are on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "query_engine")))

from query_engine.api_server import (
    ConnectRequest,
    QueryRequest,
    app,
    ask_query,
    connect_database,
    db_state,
    get_audit_logs,
    get_health,
    get_schema,
    upload_sqlite_database,
)
from query_engine.db_manager import get_or_create_demo_sqlite
from sqlalchemy import create_engine


# ---------------------------------------------------------------------------
# Robust Test Client (supports both standard FastAPI TestClient and Direct Dispatch)
# ---------------------------------------------------------------------------
class TestResponse:
    __test__ = False

    def __init__(self, status_code: int, data: Any):
        self.status_code = status_code
        self._data = data

    def json(self):
        return self._data

    @property
    def text(self):
        import json
        return json.dumps(self._data)


class DirectAPITestClient:
    """Direct-dispatch test client for sandboxed environments where loopback socket binding is restricted."""

    __test__ = False

    def __init__(self, app_instance):
        self.app = app_instance

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def get(self, url: str, params: Optional[dict] = None):
        return self._dispatch("GET", url, params=params)

    def post(self, url: str, json: Optional[dict] = None, files: Optional[dict] = None):
        return self._dispatch("POST", url, json_data=json, files=files)

    def _dispatch(
        self,
        method: str,
        url: str,
        params: Optional[dict] = None,
        json_data: Optional[dict] = None,
        files: Optional[dict] = None,
    ):
        parsed = urlparse(url)
        path = parsed.path
        query = parse_qs(parsed.query)
        if params:
            for k, v in params.items():
                query[k] = [str(v)]

        try:
            if path == "/api/health" and method == "GET":
                return TestResponse(200, get_health())

            elif path == "/api/schema" and method == "GET":
                refresh_val = query.get("refresh", ["false"])[0].lower() in ("true", "1")
                return TestResponse(200, get_schema(refresh=refresh_val))

            elif path == "/api/connection/connect" and method == "POST":
                req = ConnectRequest(**(json_data or {}))
                return TestResponse(200, connect_database(req))

            elif path == "/api/connection/upload" and method == "POST":
                if not files or "file" not in files:
                    return TestResponse(400, {"detail": "File is required."})
                file_tuple = files["file"]
                filename, bio = file_tuple[0], file_tuple[1]
                upload_file = UploadFile(file=bio, filename=filename)
                return TestResponse(200, upload_sqlite_database(upload_file))

            elif path == "/api/query/ask" and method == "POST":
                req = QueryRequest(**(json_data or {}))
                return TestResponse(200, ask_query(req))

            elif path == "/api/audit/logs" and method == "GET":
                limit = int(query.get("limit", [50])[0])
                offset = int(query.get("offset", [0])[0])
                status = query.get("status", ["all"])[0]
                return TestResponse(200, get_audit_logs(limit=limit, offset=offset, status=status))

            return TestResponse(404, {"detail": f"Route not found: {path}"})

        except HTTPException as he:
            return TestResponse(he.status_code, {"detail": he.detail})
        except ValidationError as ve:
            return TestResponse(400, {"detail": str(ve)})
        except Exception as e:
            return TestResponse(500, {"detail": f"Internal Server Error: {e}"})


# Use standard FastAPI TestClient when loopback sockets are permitted; fallback to DirectAPITestClient in sandboxes
def _get_test_client_class():
    try:
        import socket
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        s.listen(1)
        c = socket.socket()
        c.settimeout(0.3)
        c.connect(("127.0.0.1", s.getsockname()[1]))
        c.close()
        s.close()
        from fastapi.testclient import TestClient as _FastAPITestClient
        return _FastAPITestClient
    except Exception:
        return DirectAPITestClient


TestClient = _get_test_client_class()


@pytest.fixture(scope="module", autouse=True)
def setup_demo_db():
    sqlite_uri = get_or_create_demo_sqlite()
    eng = create_engine(sqlite_uri)
    db_state.set_engine(eng, "sqlite", "Local HR ERP (SQLite Demo)", is_default=True)
    yield


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# 1. Health Probe Endpoint
# ---------------------------------------------------------------------------
def test_get_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "2.4.0"
    assert "llm_provider" in data
    assert "llm_model" in data
    assert data["database_connected"] is True
    assert data["dialect"] in ("sqlite", "postgresql", "mysql")


# ---------------------------------------------------------------------------
# 2. Schema Introspection Endpoint
# ---------------------------------------------------------------------------
def test_get_schema(client):
    response = client.get("/api/schema?refresh=true")
    assert response.status_code == 200
    data = response.json()
    assert "tables" in data
    table_names = [t["name"] for t in data["tables"]]

    for expected_table in ["employees_clean", "departments", "projects", "project_assignments"]:
        assert expected_table in table_names, f"Expected table '{expected_table}' in reflected schema"

    emp_table = next(t for t in data["tables"] if t["name"] == "employees_clean")
    assert "employee_id" in emp_table["columns"]
    assert "full_name" in emp_table["columns"]
    assert "column_types" in emp_table
    assert "primary_keys" in emp_table
    assert "foreign_keys" in emp_table
    assert "sample_columns" in emp_table
    assert "sample_rows" in emp_table


# ---------------------------------------------------------------------------
# 3. Connection Management Endpoints
# ---------------------------------------------------------------------------
def test_connect_demo_database(client):
    response = client.post("/api/connection/connect", json={"mode": "demo"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["dialect"] == "sqlite"
    assert "display_name" in data
    assert data["table_count"] >= 4


def test_connect_invalid_mode(client):
    response = client.post("/api/connection/connect", json={"mode": "invalid_mode"})
    assert response.status_code == 400
    assert "Invalid mode" in response.json()["detail"]


def test_connect_custom_without_uri(client):
    response = client.post("/api/connection/connect", json={"mode": "custom", "custom_uri": None})
    assert response.status_code == 400
    assert "Custom URI is required" in response.json()["detail"]


# ---------------------------------------------------------------------------
# 4. SQLite Database Upload Endpoint
# ---------------------------------------------------------------------------
def test_upload_sqlite_database_success(client):
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as tmp:
        tmp_name = tmp.name

    conn = sqlite3.connect(tmp_name)
    conn.execute("CREATE TABLE upload_test (id INTEGER PRIMARY KEY, note TEXT)")
    conn.execute("INSERT INTO upload_test VALUES (1, 'DataMind Test')")
    conn.commit()
    conn.close()

    with open(tmp_name, "rb") as f:
        file_bytes = f.read()
    os.remove(tmp_name)

    response = client.post(
        "/api/connection/upload",
        files={"file": ("test_upload.sqlite", io.BytesIO(file_bytes), "application/octet-stream")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["dialect"] == "sqlite"
    assert "Uploaded SQLite" in data["display_name"]
    assert data["table_count"] >= 1

    # Restore demo database connection
    client.post("/api/connection/connect", json={"mode": "demo"})


def test_upload_invalid_extension(client):
    response = client.post(
        "/api/connection/upload",
        files={"file": ("malicious.exe", io.BytesIO(b"MZ..."), "application/octet-stream")},
    )
    assert response.status_code == 400
    assert "Only SQLite database files" in response.json()["detail"]


def test_upload_corrupt_header(client):
    corrupt_bytes = b"NOT_A_SQLITE_FILE_AT_ALL_EXTRA_BYTES_123"
    response = client.post(
        "/api/connection/upload",
        files={"file": ("corrupt.db", io.BytesIO(corrupt_bytes), "application/octet-stream")},
    )
    assert response.status_code == 400
    assert "header mismatch" in response.json()["detail"]


# ---------------------------------------------------------------------------
# 5. Natural Language Query Execution Endpoint
# ---------------------------------------------------------------------------
def test_ask_empty_question(client):
    response = client.post("/api/query/ask", json={"question": ""})
    assert response.status_code == 400
    assert "cannot be empty" in response.json()["detail"]


def test_ask_valid_query(client):
    def fake_ask(question, **kwargs):
        tracker = kwargs.get("tracker")
        if tracker:
            tracker.set_retrieval(15.2, 5)
            tracker.set_generation("SELECT COUNT(*) FROM employees_clean WHERE role = 'Civil Engineer';", 420.5)
            tracker.set_execution(1, 3.1)
        return "SELECT COUNT(*) FROM employees_clean WHERE role = 'Civil Engineer';", ["count"], [[14]]

    with patch("query_engine.api_server.ask", side_effect=fake_ask):
        response = client.post(
            "/api/query/ask",
            json={
                "question": "How many active civil engineers are there?",
                "use_few_shot": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "query_id" in data
        assert data["question"] == "How many active civil engineers are there?"
        assert data["status"] == "ready"
        assert data["is_valid"] is True
        assert "SELECT COUNT(*)" in data["generated_sql"]
        assert data["columns"] == ["count"]
        assert data["rows"] == [[14]]
        assert data["error_message"] is None
        assert "telemetry" in data
        assert data["telemetry"]["retrieved_examples_count"] == 5
        assert data["telemetry"]["total_latency_ms"] > 0


def test_ask_blocked_query_policy_refusal(client):
    def fake_ask_blocked(question, **kwargs):
        tracker = kwargs.get("tracker")
        if tracker:
            tracker.set_retrieval(10.0, 5)
            tracker.set_generation("REFUSED: sensitive financial data", 350.0)
            tracker.set_validation_failed("REFUSED: sensitive financial data requested")
        return "REFUSED: sensitive financial data", None, None

    with patch("query_engine.api_server.ask", side_effect=fake_ask_blocked):
        response = client.post(
            "/api/query/ask",
            json={
                "question": "Show me employee salaries",
                "blocked_columns": ["salary", "bonus"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "query_id" in data
        assert data["status"] == "refused"
        assert data["is_valid"] is False
        assert "REFUSED" in data["generated_sql"]
        assert data["columns"] is None
        assert data["rows"] is None
        assert "Policy Refusal" in data["error_message"] or "REFUSED" in data["error_message"]


def test_ask_invalid_ast_rejection(client):
    def fake_ask_invalid(question, **kwargs):
        tracker = kwargs.get("tracker")
        if tracker:
            tracker.set_retrieval(10.0, 5)
            tracker.set_generation("SELECT nonexistent_col FROM employees_clean;", 300.0)
            tracker.set_validation_failed("REJECTED: Column 'nonexistent_col' does not exist")
        return "SELECT nonexistent_col FROM employees_clean;", None, "REJECTED: Column 'nonexistent_col' does not exist"

    with patch("query_engine.api_server.ask", side_effect=fake_ask_invalid):
        response = client.post(
            "/api/query/ask",
            json={
                "question": "Show me unknown things",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "invalid"
        assert data["is_valid"] is False
        assert "REJECTED" in data["error_message"]


# ---------------------------------------------------------------------------
# 6. Audit Trail Telemetry Logs Endpoint
# ---------------------------------------------------------------------------
def test_get_audit_logs(client):
    response = client.get("/api/audit/logs?limit=10&offset=0&status=all")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "logs" in data
    assert isinstance(data["total"], int)
    assert isinstance(data["logs"], list)
    assert data["total"] >= 0


def test_get_audit_logs_with_filter(client):
    response = client.get("/api/audit/logs?limit=5&offset=0&status=ready")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "logs" in data
    for log in data["logs"]:
        assert log["status"] == "ready"
