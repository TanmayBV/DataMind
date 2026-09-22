"""
validators.py
--------------
Day 5: validation and safety layer.

Day 3 shipped a minimal string-based guard (is_safe_select) that only
caught the most obvious footguns. This replaces it with something more
rigorous, using a real SQL parser (sqlglot) instead of string matching —
regex/substring checks are easy to fool (e.g. a column literally named
"salary_report_id" would false-positive on a naive "salary" in sql.upper()
check; conversely a query that hides DELETE inside a CTE name could slip
past a naive keyword scan). Parsing the actual SQL AST and checking real
table/column identifiers is far more reliable.

Five checks, run in order, mirroring the paper's multi-layer validation
(syntax, schema compliance, safety rules):

  1. Syntax validity       — does it parse as valid SQL at all?
  2. Single statement      — exactly one statement, no smuggled second one
  3. SELECT-only           — the parsed statement must be a SELECT
  4. Schema compliance     — every table/column referenced must exist in
                              SCHEMA_WHITELIST (catches LLM hallucinations)
  5. Blocked columns       — hard-reject any reference to a sensitive
                              column (e.g. salary), regardless of context
"""

import os
import sys
from dataclasses import dataclass, field

import sqlglot
from sqlglot import exp

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "config"))
from config import BLOCKED_COLUMNS

DIALECT = "postgres"

# ---------------------------------------------------------------
# Schema whitelist — the source of truth for what's allowed.
# Update this if query_engine is pointed at a different schema
# (keep it in sync with sql/schema.sql).
# ---------------------------------------------------------------

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


@dataclass
class ValidationResult:
    is_valid: bool
    errors: list = field(default_factory=list)

    def __bool__(self):
        return self.is_valid


def _fail(errors: list) -> ValidationResult:
    return ValidationResult(is_valid=False, errors=errors)


def check_syntax(sql: str):
    """Stage 1: does this parse as valid SQL at all?"""
    try:
        parsed = sqlglot.parse_one(sql, dialect=DIALECT)
        return parsed, None
    except Exception as e:
        return None, f"syntax_error: {e}"


def check_single_statement(sql: str):
    """Stage 2: exactly one statement — blocks a second statement
    smuggled in after a semicolon (classic injection pattern)."""
    try:
        statements = sqlglot.parse(sql, dialect=DIALECT)
    except Exception as e:
        return f"syntax_error: {e}"

    non_empty = [s for s in statements if s is not None]
    if len(non_empty) != 1:
        return f"multiple_statements: found {len(non_empty)} statements, expected 1"
    return None


def check_select_only(parsed) -> str | None:
    """Stage 3: the parsed statement must be a SELECT — reject any
    data-modifying statement (INSERT/UPDATE/DELETE/DROP/ALTER/etc)."""
    if not isinstance(parsed, exp.Select):
        stmt_type = type(parsed).__name__
        return f"not_a_select: parsed statement is {stmt_type}, not SELECT"
    return None


def check_schema_compliance(parsed) -> list:
    """Stage 4: every table and column referenced must exist in
    SCHEMA_WHITELIST. Catches LLM hallucinations (e.g. inventing a
    table or column name that sounds plausible but doesn't exist).

    CTE aliases (WITH t AS (...) SELECT ... FROM t) are locally-scoped
    names, not real database tables — they're excluded from the
    "unknown table" check. Their columns still get validated correctly
    because find_all(exp.Table) also finds the real table(s) referenced
    *inside* the CTE body, so that table's columns are still counted
    when building the valid-columns set below.
    """
    errors = []

    cte_names = {c.alias for c in parsed.find_all(exp.CTE)}
    tables_used = {t.name for t in parsed.find_all(exp.Table)}
    real_tables_used = tables_used - cte_names

    unknown_tables = real_tables_used - ALL_ALLOWED_TABLES
    if unknown_tables:
        errors.append(f"unknown_tables: {sorted(unknown_tables)}")

    # Build the set of columns that are valid given the tables actually
    # referenced (a column is fine if it belongs to ANY table in the
    # query — sqlglot doesn't always resolve which table a column came
    # from without a full schema-aware resolver, so we take the union).
    valid_columns = set()
    for t in real_tables_used:
        valid_columns |= SCHEMA_WHITELIST.get(t, set())

    columns_used = {c.name for c in parsed.find_all(exp.Column)}
    # Ignore "*" (SELECT *) — exp.Star nodes, not exp.Column
    unknown_columns = columns_used - valid_columns
    if unknown_columns:
        errors.append(f"unknown_columns: {sorted(unknown_columns)}")

    return errors


def check_blocked_columns(parsed, sql: str) -> list:
    """Stage 5: hard-reject any reference to a sensitive column, anywhere
    in the query — SELECT list, WHERE clause, ORDER BY, subqueries, all
    of it. This is deliberately broader than schema compliance: even if
    a blocked column somehow existed in a table's whitelist, this check
    still fires. Defense in depth for the one category of mistake that
    must never happen (see the asymmetric safety principle)."""
    errors = []
    columns_used = {c.name.lower() for c in parsed.find_all(exp.Column)}
    for blocked in BLOCKED_COLUMNS:
        if blocked.lower() in columns_used:
            errors.append(f"blocked_column_referenced: {blocked}")
    return errors


def validate_query(sql: str) -> ValidationResult:
    """Run all five checks in order. Fails fast on syntax/statement/type
    errors (no point checking schema compliance on unparseable SQL), but
    schema-compliance and blocked-column checks both run and accumulate
    so the caller sees the full picture in one pass."""

    single_stmt_error = check_single_statement(sql)
    if single_stmt_error:
        return _fail([single_stmt_error])

    parsed, syntax_error = check_syntax(sql)
    if syntax_error:
        return _fail([syntax_error])

    select_error = check_select_only(parsed)
    if select_error:
        return _fail([select_error])

    errors = []
    errors += check_schema_compliance(parsed)
    errors += check_blocked_columns(parsed, sql)

    if errors:
        return _fail(errors)
    return ValidationResult(is_valid=True, errors=[])


if __name__ == "__main__":
    # Quick manual smoke test
    test_cases = [
        ("SELECT full_name FROM employees_clean WHERE city = 'Moscow';", True),
        ("SELECT * FROM employees_clean; DROP TABLE employees_clean;", False),
        ("DELETE FROM employees_clean WHERE employee_id = 1;", False),
        ("SELECT salary FROM employees_clean;", False),
        ("SELECT made_up_column FROM employees_clean;", False),
        ("SELECT * FROM employees_raw;", False),  # not in whitelist — raw table excluded
        ("SELECT e.full_name, d.department_name FROM employees_clean e "
         "JOIN departments d ON e.department_id = d.department_id;", True),
        ("SELECT this is not sql at all !!!", False),
    ]

    for sql, expected_valid in test_cases:
        result = validate_query(sql)
        status = "PASS" if result.is_valid == expected_valid else "FAIL"
        print(f"{status} (valid={result.is_valid}, expected={expected_valid}): {sql[:60]}")
        if result.errors:
            for e in result.errors:
                print(f"       -> {e}")
