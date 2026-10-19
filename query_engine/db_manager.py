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
from typing import Dict, Set, Tuple, List, Optional, Iterable
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "config"))
from config import DATA_DIR, DATABASE_URL, BLOCKED_COLUMNS

DEMO_SQLITE_PATH = os.path.join(DATA_DIR, "demo_hr.sqlite")


def normalize_db_url(db_url: str) -> str:
    """
    SQLAlchemy 2.0 requires 'postgresql://' instead of legacy 'postgres://'.
    Also auto-cleans common URI input issues:
    - Strips literal brackets around passwords (e.g. '[YOUR_PASSWORD]')
    - Auto-encodes literal '@' in passwords when multiple '@' symbols are present.
    """
    url = (db_url or "").strip()
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]

    if "://" in url:
        scheme, remainder = url.split("://", 1)
        if "@" in remainder:
            userinfo, hostinfo = remainder.rsplit("@", 1)
            if ":" in userinfo:
                username, password = userinfo.split(":", 1)
                # Strip accidental brackets from Supabase dashboard template [YOUR-PASSWORD]
                if password.startswith("[") and password.endswith("]"):
                    password = password[1:-1]
                # Encode literal '@' if present in password
                password = password.replace("@", "%40")
                url = f"{scheme}://{username}:{password}@{hostinfo}"
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


def sanitize_cell_value(val, max_len: int = 35) -> str:
    """Safely converts any cell value to a clean, truncated string representation."""
    if val is None:
        return "NULL"
    if isinstance(val, (bytes, bytearray, memoryview)):
        return "<binary>"
    if isinstance(val, bool):
        return "true" if val else "false"
    val_str = str(val).strip().replace("\n", " ").replace("\r", " ").replace("|", "/")
    if len(val_str) > max_len:
        return val_str[:max_len - 3] + "..."
    return val_str


def fetch_table_sample_rows(
    engine: Engine,
    table_name: str,
    columns: List[str],
    blocked_columns: Optional[Set[str]] = None,
    limit: int = 3,
    max_preview_cols: int = 10,
) -> Tuple[List[str], List[List[str]]]:
    """
    Fetches up to `limit` sample rows from `table_name` for prompt context.
    - Excludes blocked/sensitive columns (e.g. salary, ssn, passwords).
    - Caps preview width to `max_preview_cols` to avoid token bloat.
    - Dialect-agnostic execution (Postgres, SQLite, MySQL, MSSQL, Oracle).
    - Robust against permissions errors, unusual identifiers, or empty tables.
    """
    blocked = {b.lower() for b in (blocked_columns or set())}
    safe_cols = [
        c for c in columns
        if c.lower() not in blocked and not any(k in c.lower() for k in ("password", "secret", "token", "hash"))
    ]
    if not safe_cols:
        return [], []

    preview_cols = safe_cols[:max_preview_cols]
    preparer = engine.dialect.identifier_preparer
    quoted_table = preparer.quote(table_name)
    quoted_cols = ", ".join(preparer.quote(c) for c in preview_cols)
    dialect_name = getattr(engine.dialect, "name", "").lower()

    if "mssql" in dialect_name:
        query_sql = f"SELECT TOP {limit} {quoted_cols} FROM {quoted_table}"
    elif "oracle" in dialect_name:
        query_sql = f"SELECT {quoted_cols} FROM {quoted_table} FETCH FIRST {limit} ROWS ONLY"
    else:
        query_sql = f"SELECT {quoted_cols} FROM {quoted_table} LIMIT {limit}"

    rows_cleaned = []
    try:
        with engine.connect() as conn:
            res = conn.execute(text(query_sql))
            raw_rows = res.fetchall()
            for r in raw_rows:
                rows_cleaned.append([sanitize_cell_value(v) for v in r])
    except Exception:
        # Fallback without quotes if custom engine / view failed with quoted identifiers
        try:
            fallback_sql = f"SELECT {', '.join(preview_cols)} FROM {table_name} LIMIT {limit}"
            with engine.connect() as conn:
                res = conn.execute(text(fallback_sql))
                raw_rows = res.fetchall()
                for r in raw_rows:
                    rows_cleaned.append([sanitize_cell_value(v) for v in r])
        except Exception:
            rows_cleaned = []

    return preview_cols, rows_cleaned


def format_sample_rows_for_prompt(table_name: str, cols: List[str], rows: List[List[str]]) -> str:
    """Formats 3 sample rows as an informative SQL comment block for the LLM."""
    if not rows or not cols:
        return ""
    header = " | ".join(cols)
    divider = "-|-".join("-" * max(len(c), 3) for c in cols)
    row_lines = [" | ".join(r) for r in rows]
    body = "\n".join([header, divider] + row_lines)
    return (
        f"/*\n"
        f"3 sample rows from '{table_name}' (format & value reference only, not exhaustive):\n"
        f"{body}\n"
        f"*/"
    )


def introspect_schema(
    engine: Engine,
    blocked_columns: Optional[Iterable[str]] = None,
    sample_limit: int = 3,
) -> Tuple[Dict[str, Set[str]], str, List[dict]]:
    """
    Reflects the database schema dynamically using SQLAlchemy Inspector.
    Extracts columns, foreign keys, row counts, and safe sample rows.
    
    Returns:
        schema_whitelist: {table_name: {col1, col2, ...}}
        schema_prompt: Human-readable DDL-like description with sample rows for the LLM
        tables_meta: List of table summaries for UI inspection (including sample rows)
    """
    inspector = inspect(engine)
    whitelist: Dict[str, Set[str]] = {}
    prompt_lines: List[str] = []
    tables_meta: List[dict] = []

    active_blocked = set(BLOCKED_COLUMNS) if blocked_columns is None else {c.lower() for c in blocked_columns}
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

        table_block = f"{table_name} (\n{body}\n)"

        # Fetch safe sample rows (3 rows)
        sample_cols, sample_rows = fetch_table_sample_rows(
            engine=engine,
            table_name=table_name,
            columns=[c["name"] for c in columns],
            blocked_columns=active_blocked,
            limit=sample_limit,
        )

        sample_prompt_block = format_sample_rows_for_prompt(table_name, sample_cols, sample_rows)
        if sample_prompt_block:
            prompt_lines.append(f"{table_block}\n{sample_prompt_block}")
        else:
            prompt_lines.append(table_block)

        # Count total rows
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
            "sample_columns": sample_cols,
            "sample_rows": sample_rows,
        })

    schema_prompt = (
        "Tables in Database (including schema and 3 sample rows for formatting reference):\n\n"
        + "\n\n".join(prompt_lines)
    )
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
