"""
audit_logger.py
---------------
Lifecycle state tracking and persistent query audit logging layer.
Replicates Algorithm 1 (Phase 7) and Section III-B.4 from the paper:
Tracks query lifecycle states (loading -> retrieving -> generating -> validating -> executing -> ready/rejected),
recording fine-grained latency per stage for transparency and auditability at $0 cost.
"""

import os
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "config"))
from config import DATA_DIR

AUDIT_DB_PATH = os.path.join(DATA_DIR, "query_audit_logs.sqlite")


def init_audit_db():
    """Initializes the query audit log table."""
    conn = sqlite3.connect(AUDIT_DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS query_audit_logs (
            query_id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            question TEXT NOT NULL,
            status TEXT NOT NULL,
            generated_sql TEXT,
            is_valid INTEGER DEFAULT 0,
            error_message TEXT,
            rows_returned INTEGER DEFAULT 0,
            retrieval_latency_ms REAL DEFAULT 0.0,
            llm_latency_ms REAL DEFAULT 0.0,
            exec_latency_ms REAL DEFAULT 0.0,
            total_latency_ms REAL DEFAULT 0.0,
            retrieved_examples_count INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


@dataclass
class QueryTracker:
    question: str
    query_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    status: str = "loading"
    generated_sql: str = ""
    is_valid: bool = False
    error_message: str = ""
    rows_returned: int = 0
    retrieval_latency_ms: float = 0.0
    llm_latency_ms: float = 0.0
    exec_latency_ms: float = 0.0
    total_latency_ms: float = 0.0
    retrieved_examples_count: int = 0
    _start_time: float = field(default_factory=time.time)

    def set_retrieval(self, latency_ms: float, count: int):
        self.status = "generating_query"
        self.retrieval_latency_ms = latency_ms
        self.retrieved_examples_count = count

    def set_generation(self, sql: str, latency_ms: float):
        self.generated_sql = sql
        self.llm_latency_ms = latency_ms
        self.status = "validating"

    def set_validation_failed(self, error: str):
        self.status = "refused" if error.startswith("REFUSED") else "invalid"
        self.error_message = error
        self.is_valid = False
        self._finish()

    def set_execution(self, rows_count: int, latency_ms: float):
        self.status = "ready"
        self.is_valid = True
        self.rows_returned = rows_count
        self.exec_latency_ms = latency_ms
        self._finish()

    def set_execution_error(self, error: str, latency_ms: float):
        self.status = "error"
        self.is_valid = False
        self.error_message = error
        self.exec_latency_ms = latency_ms
        self._finish()

    def _finish(self):
        self.total_latency_ms = (time.time() - self._start_time) * 1000.0
        self.log_to_db()

    def log_to_db(self):
        try:
            init_audit_db()
            conn = sqlite3.connect(AUDIT_DB_PATH)
            cur = conn.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO query_audit_logs (
                    query_id, timestamp, question, status, generated_sql,
                    is_valid, error_message, rows_returned,
                    retrieval_latency_ms, llm_latency_ms, exec_latency_ms,
                    total_latency_ms, retrieved_examples_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.query_id,
                datetime.utcnow().isoformat(),
                self.question,
                self.status,
                self.generated_sql,
                1 if self.is_valid else 0,
                self.error_message,
                self.rows_returned,
                self.retrieval_latency_ms,
                self.llm_latency_ms,
                self.exec_latency_ms,
                self.total_latency_ms,
                self.retrieved_examples_count,
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            # Audit logging should never crash the main application
            pass


def get_recent_audit_logs(limit: int = 50) -> List[Dict[str, Any]]:
    """Fetches the most recent query audit logs for display in UI."""
    init_audit_db()
    conn = sqlite3.connect(AUDIT_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM query_audit_logs
        ORDER BY timestamp DESC
        LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows
