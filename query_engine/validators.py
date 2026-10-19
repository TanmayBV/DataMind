"""
validators.py
--------------
Multi-stage validation and safety layer using sqlglot AST parsing.

Supports:
- Dynamic schema whitelist verification (against any database)
- Multi-dialect SQL syntax parsing (Postgres, SQLite, MySQL, etc.)
- AST-level SELECT-only enforcement
- AST-level blocked sensitive columns detection
- Multi-statement injection defense
"""

import os
import sys
from dataclasses import dataclass, field
from typing import Dict, Set, List, Optional

import sqlglot
from sqlglot import exp

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "config"))
from config import BLOCKED_COLUMNS

# Default dialect and whitelist (backward-compatible with baseline HR schema)
DEFAULT_DIALECT = "postgres"

SCHEMA_WHITELIST = {
    "employees_clean": {
        "employee_id", "full_name", "role", "city", "department_id",
        "is_payroll", "employee_status", "hire_date",
    },
    "departments": {"department_id", "department_name"},
    "projects": {"project_id", "project_code", "project_name"},
    "project_assignments": {"assignment_id", "employee_id", "project_id"},
}

ALL_ALLOWED_TABLES = set(SCHEMA_WHITELIST.keys())

DIALECT_MAP = {
    "postgresql": "postgres",
    "postgres": "postgres",
    "sqlite": "sqlite",
    "mysql": "mysql",
    "mssql": "tsql",
    "oracle": "oracle",
    "snowflake": "snowflake",
    "duckdb": "duckdb",
}


def to_sqlglot_dialect(dialect: Optional[str]) -> str:
    """Normalizes SQLAlchemy dialect names to sqlglot dialect names."""
    if not dialect:
        return "postgres"
    return DIALECT_MAP.get(dialect.lower(), dialect.lower())


@dataclass
class ValidationResult:
    is_valid: bool
    errors: list = field(default_factory=list)

    def __bool__(self):
        return self.is_valid


def _fail(errors: list) -> ValidationResult:
    return ValidationResult(is_valid=False, errors=errors)


def check_syntax(sql: str, dialect: str = DEFAULT_DIALECT):
    """Stage 1: does this parse as valid SQL for the target dialect?"""
    glot_dialect = to_sqlglot_dialect(dialect)
    try:
        parsed = sqlglot.parse_one(sql, dialect=glot_dialect)
        return parsed, None
    except Exception as e:
        return None, f"syntax_error: {e}"


def check_single_statement(sql: str, dialect: str = DEFAULT_DIALECT):
    """Stage 2: exactly one statement — blocks multiple statements/injection."""
    glot_dialect = to_sqlglot_dialect(dialect)
    try:
        statements = sqlglot.parse(sql, dialect=glot_dialect)
    except Exception as e:
        return f"syntax_error: {e}"

    non_empty = [s for s in statements if s is not None]
    if len(non_empty) != 1:
        return f"multiple_statements: found {len(non_empty)} statements, expected 1"
    return None


def check_select_only(parsed) -> Optional[str]:
    """Stage 3: parsed statement must be a SELECT — rejects INSERT/UPDATE/DELETE/DROP/etc."""
    if not isinstance(parsed, exp.Select):
        stmt_type = type(parsed).__name__
        return f"not_a_select: parsed statement is {stmt_type}, not SELECT"
    return None


def check_schema_compliance(parsed, schema_whitelist: Optional[Dict[str, Set[str]]] = None) -> list:
    """Stage 4: every table and column referenced must exist in the schema whitelist."""
    whitelist = schema_whitelist if schema_whitelist is not None else SCHEMA_WHITELIST
    allowed_tables = set(whitelist.keys())
    errors = []

    cte_names = {c.alias for c in parsed.find_all(exp.CTE)}
    tables_used = {t.name for t in parsed.find_all(exp.Table)}
    real_tables_used = tables_used - cte_names

    unknown_tables = real_tables_used - allowed_tables
    if unknown_tables:
        errors.append(f"unknown_tables: {sorted(unknown_tables)}")

    valid_columns = set()
    for t in real_tables_used:
        valid_columns |= whitelist.get(t, set())

    columns_used = {c.name for c in parsed.find_all(exp.Column)}
    unknown_columns = columns_used - valid_columns
    if unknown_columns:
        errors.append(f"unknown_columns: {sorted(unknown_columns)}")

    return errors


def check_blocked_columns(parsed, sql: str, blocked_columns: Optional[List[str]] = None) -> list:
    """Stage 5: hard-reject any reference to a sensitive/blocked column."""
    blocked = blocked_columns if blocked_columns is not None else BLOCKED_COLUMNS
    errors = []
    columns_used = {c.name.lower() for c in parsed.find_all(exp.Column)}
    for b in blocked:
        if b.lower() in columns_used:
            errors.append(f"blocked_column_referenced: {b}")
    return errors


def validate_query(
    sql: str,
    schema_whitelist: Optional[Dict[str, Set[str]]] = None,
    dialect: str = DEFAULT_DIALECT,
    blocked_columns: Optional[List[str]] = None,
) -> ValidationResult:
    """
    Runs all 5 validation checks in order. Supports dynamic schema and dialect.
    """
    single_stmt_error = check_single_statement(sql, dialect=dialect)
    if single_stmt_error:
        return _fail([single_stmt_error])

    parsed, syntax_error = check_syntax(sql, dialect=dialect)
    if syntax_error:
        return _fail([syntax_error])

    select_error = check_select_only(parsed)
    if select_error:
        return _fail([select_error])

    errors = []
    errors += check_schema_compliance(parsed, schema_whitelist=schema_whitelist)
    errors += check_blocked_columns(parsed, sql, blocked_columns=blocked_columns)

    if errors:
        return _fail(errors)
    return ValidationResult(is_valid=True, errors=[])


if __name__ == "__main__":
    # Smoke test: validates default HR schema
    test_cases = [
        ("SELECT full_name FROM employees_clean WHERE city = 'Moscow';", True),
        ("SELECT * FROM employees_clean; DROP TABLE employees_clean;", False),
        ("DELETE FROM employees_clean WHERE employee_id = 1;", False),
        ("SELECT salary FROM employees_clean;", False),
        ("SELECT made_up_column FROM employees_clean;", False),
        ("SELECT * FROM employees_raw;", False),
        ("SELECT e.full_name, d.department_name FROM employees_clean e JOIN departments d ON e.department_id = d.department_id;", True),
        ("SELECT this is not sql at all !!!", False),
    ]

    for sql, expected_valid in test_cases:
        result = validate_query(sql)
        status = "PASS" if result.is_valid == expected_valid else "FAIL"
        print(f"{status} (valid={result.is_valid}, expected={expected_valid}): {sql[:60]}")
        if result.errors:
            for e in result.errors:
                print(f"       -> {e}")
