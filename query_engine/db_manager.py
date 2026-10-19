"""
db_manager.py
-------------
Universal database connection, automated schema introspection,
and safe query execution layer using SQLAlchemy.

Supports:
- PostgreSQL (Supabase, Neon, RDS, local)
- SQLite (Local files, uploaded DBs, in-memory)
- MySQL / MariaDB
- Any other SQLAlchemy-supported database URI

Includes automatic zero-configuration fallback:
If no DATABASE_URL is set in .env, automatically loads a local
demo SQLite database from the cleaned CSV files (data/*.csv).
"""

import os
import sys
import sqlite3
import pandas as pd
from typing import Dict, Set, Tuple, List, Optional
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "config"))
from config import DATA_DIR, DATABASE_URL

DEMO_SQLITE_PATH = os.path.join(DATA_DIR, "demo_hr.sqlite")


def normalize_db_url(db_url: str) -> str:
    """SQLAlchemy 2.0 requires 'postgresql://' instead of legacy 'postgres://'."""
    url = (db_url or "").strip()
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    return url


def get_or_create_demo_sqlite(db_path: str = DEMO_SQLITE_PATH) -> str:
    """
    Creates a local SQLite database from cleaned CSV files if it doesn't exist.
    Guarantees that the project runs 100% out-of-the-box with zero cloud setup.
    """
    sqlite_uri = f"sqlite:///{os.path.abspath(db_path)}"
    if os.path.exists(db_path) and os.path.getsize(db_path) > 0:
        return sqlite_uri

    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)

    # 1. departments
    dept_path = os.path.join(DATA_DIR, "departments.csv")
    if os.path.exists(dept_path):
        df_dept = pd.read_csv(dept_path)
        if "department_id" not in df_dept.columns:
            df_dept.insert(0, "department_id", range(1, len(df_dept) + 1))
        df_dept.to_sql("departments", conn, if_exists="replace", index=False)

    # 2. projects
    proj_path = os.path.join(DATA_DIR, "projects.csv")
    if os.path.exists(proj_path):
        df_proj = pd.read_csv(proj_path)
        if "project_id" not in df_proj.columns:
            df_proj.insert(0, "project_id", range(1, len(df_proj) + 1))
        df_proj.to_sql("projects", conn, if_exists="replace", index=False)

    # 3. employees_clean
    emp_path = os.path.join(DATA_DIR, "employees_clean.csv")
    if os.path.exists(emp_path):
        df_emp = pd.read_csv(emp_path)
        df_emp.to_sql("employees_clean", conn, if_exists="replace", index=False)

    # 4. project_assignments
    assign_path = os.path.join(DATA_DIR, "project_assignments_clean.csv")
    if os.path.exists(assign_path):
        df_assign = pd.read_csv(assign_path)
        df_assign.to_sql("project_assignments", conn, if_exists="replace", index=False)

    conn.commit()
    conn.close()
    return sqlite_uri


def create_db_engine(db_url: Optional[str] = None) -> Tuple[Engine, str, str]:
    """
    Creates an engine and returns (engine, dialect_name, display_source).
    If db_url is None:
      - Uses DATABASE_URL from .env if valid and connectable.
      - Otherwise falls back to local demo SQLite.
    """
    if db_url and db_url.strip():
        norm_url = normalize_db_url(db_url)
        if norm_url.startswith("http://") or norm_url.startswith("https://"):
            raise ValueError(
                "Invalid Database URL: Expected a database URI starting with 'postgresql://', "
                "'mysql://', or 'sqlite:///', not an HTTPS URL. "
                "For Supabase, use the PostgreSQL connection URI from Project Settings -> Database."
            )
        connect_args = {"connect_timeout": 5} if "postgres" in norm_url else {}
        engine = create_engine(norm_url, pool_pre_ping=True, connect_args=connect_args)
        # Verify connectivity upfront
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        dialect = engine.dialect.name
        return engine, dialect, f"Custom ({dialect.upper()})"

    if DATABASE_URL and DATABASE_URL.strip():
        norm_url = normalize_db_url(DATABASE_URL)
        if not norm_url.startswith("http://") and not norm_url.startswith("https://"):
            try:
                connect_args = {"connect_timeout": 3} if "postgres" in norm_url else {}
                engine = create_engine(norm_url, pool_pre_ping=True, connect_args=connect_args)
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                dialect = engine.dialect.name
                return engine, dialect, "Cloud Postgres (DATABASE_URL)"
            except Exception as e:
                err_msg = str(e)
                hint = ""
                if "could not translate host name" in err_msg and "supabase.co" in norm_url:
                    hint = " (Hint: Supabase direct connection is IPv6-only. Use the Supabase Connection Pooler URL with port 6543 on IPv4 networks)"
                print(f"[db_manager] Cloud DB connection failed ({e}){hint}. Falling back to local SQLite demo.")
        else:
            print("[db_manager] DATABASE_URL in .env is an HTTPS URL, not a database URI. Falling back to local SQLite demo.")

    # Local SQLite Fallback
    sqlite_uri = get_or_create_demo_sqlite()
    engine = create_engine(sqlite_uri)
    return engine, "sqlite", "Local HR ERP (SQLite Demo)"


def introspect_schema(engine: Engine) -> Tuple[Dict[str, Set[str]], str, List[dict]]:
    """
    Reflects the database schema dynamically using SQLAlchemy Inspector.
    
    Returns:
        schema_whitelist: {table_name: {col1, col2, ...}}
        schema_prompt: Human-readable DDL-like description for the LLM
        tables_meta: List of table summaries for UI inspection
    """
    inspector = inspect(engine)
    whitelist: Dict[str, Set[str]] = {}
    prompt_lines: List[str] = []
    tables_meta: List[dict] = []

    table_names = inspector.get_table_names()

    for table_name in table_names:
        columns = inspector.get_columns(table_name)
        col_names = {c["name"] for c in columns}
        whitelist[table_name] = col_names

        # Column representations
        col_strs = []
        for c in columns:
            col_type = str(c.get("type", "TEXT"))
            pk = " PRIMARY KEY" if c.get("primary_key") else ""
            col_strs.append(f"    {c['name']} {col_type}{pk}")

        # Foreign keys
        fk_strs = []
        try:
            fks = inspector.get_foreign_keys(table_name)
            for fk in fks:
                referred_table = fk.get("referred_table")
                constrained = ", ".join(fk.get("constrained_columns", []))
                referred = ", ".join(fk.get("referred_columns", []))
                if referred_table and constrained:
                    fk_strs.append(f"    -- FK: ({constrained}) REFERENCES {referred_table}({referred})")
        except Exception:
            pass

        body = ",\n".join(col_strs)
        if fk_strs:
            body += "\n" + "\n".join(fk_strs)

        prompt_lines.append(f"{table_name} (\n{body}\n)")

        # Count sample rows
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

        tables_meta.append({
            "name": table_name,
            "columns": [c["name"] for c in columns],
            "column_types": {c["name"]: str(c.get("type", "TEXT")) for c in columns},
            "row_count": row_count,
        })

    schema_prompt = "Tables in Database:\n\n" + "\n\n".join(prompt_lines)
    return whitelist, schema_prompt, tables_meta


def execute_query(engine: Engine, sql: str, max_rows: int = 500) -> Tuple[List[str], list]:
    """
    Executes a SELECT query safely against the engine with clean resource teardown.
    """
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        columns = list(result.keys())
        rows = [list(r) for r in result.fetchmany(max_rows)]
        return columns, rows
