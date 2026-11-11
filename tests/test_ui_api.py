"""
tests/test_ui_api.py
--------------------
End-to-End integration test suite for the DataMind Modern React UI backend endpoints.
Verifies contract requirements UI-04, UI-05, and UI-06:
1. GET /api/health
2. GET /api/schema
3. POST /api/query/ask (valid query)
4. POST /api/query/ask (policy refusal on sensitive column)
5. GET /api/audit/logs
"""

import os
import sys
from typing import Any, Optional
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import pytest
from sqlalchemy import create_engine

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
)
from query_engine.db_manager import get_or_create_demo_sqlite


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
    """Direct dispatch test client for offline/sandboxed test execution."""

    __test__ = False

    def __init__(self, app_instance):
        self.app = app_instance

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def get(self, url: str, params: Optional[dict] = None):
        return self._dispatch("GET", url, params=params)

    def post(self, url: str, json: Optional[dict] = None):
        return self._dispatch("POST", url, json_data=json)

    def _dispatch(
        self,
        method: str,
        url: str,
        params: Optional[dict] = None,
        json_data: Optional[dict] = None,
    ):
        parsed = urlparse(url)
        path = parsed.path
        query = parse_qs(parsed.query)
        if params:
            for k, v in params.items():
                query[k] = [str(v)]

        from fastapi import HTTPException
        from pydantic import ValidationError

        try:
            if path == "/api/health" and method == "GET":
                return TestResponse(200, get_health())

            elif path == "/api/schema" and method == "GET":
                refresh_val = query.get("refresh", ["false"])[0].lower() in ("true", "1")
                return TestResponse(200, get_schema(refresh=refresh_val))

            elif path == "/api/connection/connect" and method == "POST":
                req = ConnectRequest(**(json_data or {}))
                return TestResponse(200, connect_database(req))

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


def _get_test_client():
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


TestClient = _get_test_client()


@pytest.fixture(scope="module", autouse=True)
def setup_test_demo_db():
    sqlite_uri = get_or_create_demo_sqlite()
    eng = create_engine(sqlite_uri)
    db_state.set_engine(eng, "sqlite", "Local HR ERP (SQLite Demo)", is_default=True)
    yield


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Test 1: GET /api/health
# ---------------------------------------------------------------------------
def test_get_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "2.4.0"
    assert data["database_connected"] is True
    assert data["dialect"] == "sqlite"


# ---------------------------------------------------------------------------
# Test 2: GET /api/schema
# ---------------------------------------------------------------------------
def test_get_schema(client):
    response = client.get("/api/schema?refresh=true")
    assert response.status_code == 200
    data = response.json()
    assert "tables" in data
    table_names = [t["name"] for t in data["tables"]]

    # Verify all 4 canonical demo tables are present
    assert "employees_clean" in table_names
    assert "departments" in table_names
    assert "projects" in table_names
    assert "project_assignments" in table_names

    # Check employees_clean metadata details
    emp_table = next(t for t in data["tables"] if t["name"] == "employees_clean")
    assert "employee_id" in emp_table["columns"]
    assert "full_name" in emp_table["columns"]
    assert "role" in emp_table["columns"]
    assert "column_types" in emp_table
    assert emp_table["row_count"] > 0
    assert len(emp_table["sample_rows"]) > 0


# ---------------------------------------------------------------------------
# Test 3: POST /api/query/ask (Valid Query)
# ---------------------------------------------------------------------------
def test_ask_valid_query(client):
    def mock_ask_func(question, **kwargs):
        tracker = kwargs.get("tracker")
        if tracker:
            tracker.set_retrieval(18.5, 5)
            tracker.set_generation("SELECT COUNT(*) FROM employees_clean WHERE role = 'Civil Engineer' AND employee_status = 'active';", 420.0)
            tracker.set_execution(1, 2.5)
        return "SELECT COUNT(*) FROM employees_clean WHERE role = 'Civil Engineer' AND employee_status = 'active';", ["count"], [[14]]

    with patch("query_engine.api_server.ask", side_effect=mock_ask_func):
        response = client.post(
            "/api/query/ask",
            json={
                "question": "How many active civil engineers are there?",
                "use_few_shot": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["is_valid"] is True
        assert "SELECT COUNT(*)" in data["generated_sql"]
        assert data["columns"] == ["count"]
        assert data["rows"] == [[14]]
        assert data["error_message"] is None
        assert data["telemetry"]["total_latency_ms"] > 0


# ---------------------------------------------------------------------------
# Test 4: POST /api/query/ask (Policy Refusal on Salary)
# ---------------------------------------------------------------------------
def test_ask_salary_policy_refusal(client):
    def mock_ask_refusal(question, **kwargs):
        tracker = kwargs.get("tracker")
        if tracker:
            tracker.set_retrieval(12.0, 5)
            tracker.set_generation("REFUSED: sensitive financial data", 310.0)
            tracker.set_validation_failed("Policy Refusal: sensitive financial data requested (column 'salary' is restricted).")
        return "REFUSED: sensitive financial data", None, None

    with patch("query_engine.api_server.ask", side_effect=mock_ask_refusal):
        response = client.post(
            "/api/query/ask",
            json={
                "question": "What is the average salary?",
                "blocked_columns": ["salary", "bonus", "compensation"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "refused"
        assert data["is_valid"] is False
        assert "REFUSED" in data["generated_sql"]
        assert data["columns"] is None
        assert data["rows"] is None
        assert "salary" in data["error_message"].lower() or "policy refusal" in data["error_message"].lower()


# ---------------------------------------------------------------------------
# Test 5: GET /api/audit/logs
# ---------------------------------------------------------------------------
def test_get_audit_logs(client):
    response = client.get("/api/audit/logs?limit=10&offset=0&status=all")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "logs" in data
    assert isinstance(data["logs"], list)

    # Check that audit logs reflect previously asked queries
    if len(data["logs"]) > 0:
        first_entry = data["logs"][0]
        assert "query_id" in first_entry
        assert "question" in first_entry
        assert "status" in first_entry
        assert "generated_sql" in first_entry
        assert "total_latency_ms" in first_entry
