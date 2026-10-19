"""
nl2sql_chain.py
----------------
Natural-language-to-SQL generation chain.

Designed to be universal and schema-agnostic:
- Connects to any database (Postgres, SQLite, MySQL, etc.) via SQLAlchemy
- Uses dynamic schema introspection and dialect-aware generation
- Validates queries against schema whitelists and safety policies via sqlglot
- Supports few-shot FAISS retrieval on trained schemas and zero-shot on custom schemas
"""

import os
import re
import sys
import time

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "config"))
from config import (
    DATABASE_URL, GEMINI_API_KEY, GROQ_API_KEY, LLM_MODEL, GROQ_MODEL, LLM_PROVIDER,
    CANONICAL_CITIES, CANONICAL_ROLES, CANONICAL_STATUSES, CANONICAL_DEPARTMENTS, CANONICAL_PROJECTS
)

from langchain_core.messages import HumanMessage, SystemMessage

from db_manager import create_db_engine, introspect_schema, execute_query
from retriever import retrieve_examples, format_examples_for_prompt
from validators import validate_query, DEFAULT_DIALECT, SCHEMA_WHITELIST

# ---------------------------------------------------------------
# Default HR Schema description + business rules
# (Synchronized with data cleaning canonical dictionaries)
# ---------------------------------------------------------------

DEFAULT_SCHEMA_DESCRIPTION = f"""
Tables & Columns:

employees_clean (
    employee_id     INTEGER PRIMARY KEY,
    full_name       TEXT,
    role            TEXT,
    city            TEXT,
    department_id   INTEGER REFERENCES departments(department_id),
    is_payroll      BOOLEAN,    -- true = payroll employee, false = contractor
    employee_status TEXT,       -- EXACT VALUES: 'active' or 'terminated' (strictly lowercase)
    hire_date       DATE
)
/*
3 sample rows from 'employees_clean' (format & value reference only, not exhaustive):
employee_id | full_name | role | city | department_id | is_payroll | employee_status | hire_date
1 | Allison Hill | Project Manager | Dubai | 1 | true | active | 2015-05-03
2 | Noah Rhodes | Accountant | Istanbul | 5 | true | terminated | 2019-09-28
3 | Angie Henderson | Civil Engineer | New York | 2 | true | terminated | 2016-05-26
*/
-- NOTE: employees_clean does NOT include salary or compensation.

departments (
    department_id   INTEGER PRIMARY KEY,
    department_name TEXT        -- Canonical: 'Human Resources', 'Engineering', 'Finance', 'Project Management', 'IT'
)
/*
3 sample rows from 'departments':
department_id | department_name
1 | Human Resources
2 | Engineering
3 | Finance
*/

projects (
    project_id   INTEGER PRIMARY KEY,
    project_code TEXT,        -- Canonical: 'GPP', 'Skyline Tower', 'Metro Expansion', 'Cloud Migration'
    project_name TEXT
)
/*
3 sample rows from 'projects':
project_id | project_code | project_name
1 | GPP | GPP
2 | Skyline Tower | Skyline Tower
3 | Metro Expansion | Metro Expansion
*/

project_assignments (
    assignment_id INTEGER PRIMARY KEY,
    employee_id   INTEGER REFERENCES employees_clean(employee_id),
    project_id    INTEGER REFERENCES projects(project_id)
)
/*
3 sample rows from 'project_assignments':
assignment_id | employee_id | project_id
1 | 1 | 3
2 | 4 | 1
3 | 5 | 4
*/

Exact Canonical Values in Database:
- employee_status : Strictly 'active' or 'terminated' (lowercase only, NEVER 'Active')
- role            : {', '.join(repr(r) for r in CANONICAL_ROLES)}
- city            : {', '.join(repr(c) for c in CANONICAL_CITIES)}
- department_name : {', '.join(repr(d) for d in CANONICAL_DEPARTMENTS)}
- project_code    : {', '.join(repr(p) for p in CANONICAL_PROJECTS)}
"""

DEFAULT_BUSINESS_RULES = """
Business Rules & Casing Standards (Paper Section V-B):
1. "Active employees" or "current staff" means employee_status = 'active' (strictly lowercase 'active').
2. Unless the question explicitly asks about contractors, assume is_payroll = true (exclude contractors from general staff counts).
3. Text Casing Rule: Always use the exact canonical values and casing shown above (e.g. employee_status = 'active', role = 'Civil Engineer') OR use LOWER(column) = LOWER('...') to guarantee case-insensitive matching.
4. NEVER generate a query that references salary, bonus, compensation, wage, or national_id. If asked, respond with exactly: REFUSED: sensitive financial data
5. Only generate SELECT statements. Never generate INSERT, UPDATE, DELETE, DROP, ALTER, or data-modifying queries.
6. Always JOIN through department_id / project_id — never guess that department or project name exists as a column on employees_clean.
"""

GENERIC_BUSINESS_RULES = """
Rules:
1. Only generate valid SELECT statements. Never generate INSERT, UPDATE, DELETE, DROP, ALTER, or data-modifying queries.
2. Return ONLY the executable SQL query — no markdown code fences, no explanations.
3. If the question asks for sensitive or restricted data, respond with: REFUSED: sensitive data requested
"""

_default_engine_info = None


def get_default_engine():
    """Lazily initializes the default database engine (cloud Postgres or local SQLite demo)."""
    global _default_engine_info
    if _default_engine_info is None:
        _default_engine_info = create_db_engine()
    return _default_engine_info


def get_llm(provider: str = None):
    """
    Returns an LLM client. Supports both Groq and Google Gemini at $0 cost.
    Defaults to Groq (ultra-fast, generous free quota) or Gemini Flash.
    """
    prov = (provider or LLM_PROVIDER or "groq").lower()

    if prov == "groq" and GROQ_API_KEY:
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=GROQ_MODEL,
            groq_api_key=GROQ_API_KEY,
            temperature=0,
        )
    elif GEMINI_API_KEY and prov != "groq":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=LLM_MODEL,
            google_api_key=GEMINI_API_KEY,
            temperature=0,
        )
    elif GROQ_API_KEY:
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=GROQ_MODEL,
            groq_api_key=GROQ_API_KEY,
            temperature=0,
        )
    elif GEMINI_API_KEY:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=LLM_MODEL,
            google_api_key=GEMINI_API_KEY,
            temperature=0,
        )
    else:
        raise RuntimeError("Neither GROQ_API_KEY nor GEMINI_API_KEY is configured in .env.")


def build_system_prompt(
    question: str,
    use_few_shot: bool = True,
    schema_description: str = None,
    business_rules: str = None,
    dialect: str = "postgres",
    is_default_schema: bool = True,
) -> str:
    """
    Constructs the system prompt with dialect constraints, schema metadata,
    business policies, and optional few-shot examples.
    """
    dialect_clean = dialect.upper() if dialect else "SQL"
    schema_text = schema_description or DEFAULT_SCHEMA_DESCRIPTION
    rules_text = business_rules or (DEFAULT_BUSINESS_RULES if is_default_schema else GENERIC_BUSINESS_RULES)

    prompt = (
        f"You are an expert SQL generation assistant for a {dialect_clean} database.\n"
        f"Given a natural language question, generate ONE valid {dialect_clean} SELECT\n"
        f"query that answers it. Return ONLY the SQL query — no explanation, no\n"
        f"markdown code fences, no commentary.\n\n"
        f"{schema_text}\n\n"
        f"{rules_text}\n"
    )

    if dialect and dialect.lower() == "sqlite":
        prompt += (
            "\nSQLite Specific Guidelines:\n"
            "- Text comparison in SQLite is case-sensitive by default. When filtering text values (like roles, cities, statuses), match exact casing (e.g. 'active', 'terminated') or use LOWER(col) = LOWER('value').\n"
            "- Do NOT use PostgreSQL-specific syntax like ILIKE, EXTRACT, or SERIAL.\n"
        )

    # Inject few-shot examples when available and relevant
    if use_few_shot and is_default_schema:
        try:
            examples = retrieve_examples(question)
            examples_block = format_examples_for_prompt(examples)
            if examples_block:
                prompt += f"\n{examples_block}"
        except Exception:
            pass

    return prompt


def generate_sql(
    question: str,
    llm,
    use_few_shot: bool = True,
    schema_description: str = None,
    business_rules: str = None,
    dialect: str = "postgres",
    is_default_schema: bool = True,
) -> str:

    system_prompt = build_system_prompt(
        question,
        use_few_shot=use_few_shot,
        schema_description=schema_description,
        business_rules=business_rules,
        dialect=dialect,
        is_default_schema=is_default_schema,
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=question),
    ]

    max_retries = 3
    response = None

    for attempt in range(max_retries):
        try:
            response = llm.invoke(messages)
            break
        except Exception as e:
            err_str = str(e)
            if ("429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower()) and GROQ_API_KEY:
                # Automatic failover from Gemini to Groq
                from langchain_groq import ChatGroq
                fallback = ChatGroq(model=GROQ_MODEL, groq_api_key=GROQ_API_KEY, temperature=0)
                response = fallback.invoke(messages)
                break
            elif "503" in err_str or "UNAVAILABLE" in err_str:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                else:
                    raise
            else:
                raise

    content = response.content

    if isinstance(content, list):
        sql = "".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    else:
        sql = content

    sql = sql.strip()

    sql = re.sub(
        r"^```(?:sql)?\s*|\s*```$",
        "",
        sql,
        flags=re.IGNORECASE
    ).strip()

    return sql


def is_safe_select(sql: str) -> bool:
    """DEPRECATED — kept for backward compatibility. Use validators.validate_query instead."""
    normalized = sql.strip().rstrip(";").upper()
    if not normalized.startswith("SELECT"):
        return False
    if ";" in sql.strip().rstrip(";"):
        return False
    forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "GRANT"]
    return not any(word in normalized for word in forbidden)


from audit_logger import QueryTracker

PII_COLUMNS = {"adines_number", "national_id", "ssn", "phone", "id_number", "passport_number"}


def mask_pii_data(columns: list, rows: list) -> list:
    """Stage 6: Masks sensitive PII fields (national ID, SSN, phone) in query result tables."""
    if not columns or not rows:
        return rows
    pii_indices = [i for i, col in enumerate(columns) if col.lower() in PII_COLUMNS]
    if not pii_indices:
        return rows
    masked_rows = []
    for row in rows:
        row_list = list(row)
        for idx in pii_indices:
            row_list[idx] = "***REDACTED***"
        masked_rows.append(tuple(row_list))
    return masked_rows


def run_query(sql: str, engine=None):
    """Executes SQL against either the provided engine or default engine."""
    if engine is None:
        engine, _, _ = get_default_engine()
    return execute_query(engine, sql)


def ask(
    question: str,
    llm=None,
    use_few_shot: bool = True,
    engine=None,
    schema_whitelist=None,
    schema_description=None,
    dialect=None,
    business_rules=None,
    blocked_columns=None,
    is_default_schema: bool = True,
):
    """
    Main entry point: question in -> (sql, columns, rows) or error out.
    Supports both default HR database and any external database.
    Integrates query lifecycle tracking and PII masking.
    """
    llm = llm or get_llm()
    tracker = QueryTracker(question=question)

    # Determine database engine and metadata
    if engine is None:
        engine, detected_dialect, _ = get_default_engine()
        dialect = dialect or detected_dialect
        if schema_whitelist is None:
            schema_whitelist = SCHEMA_WHITELIST
        if schema_description is None:
            schema_description = DEFAULT_SCHEMA_DESCRIPTION
    else:
        # Custom engine passed: auto-introspect if metadata not provided
        if dialect is None:
            dialect = getattr(engine.dialect, "name", "postgres")
        if schema_whitelist is None or schema_description is None:
            introspected_wl, introspected_desc, _ = introspect_schema(engine, blocked_columns=blocked_columns)
            schema_whitelist = schema_whitelist or introspected_wl
            schema_description = schema_description or introspected_desc
            is_default_schema = False

    # Track retrieval
    retrieval_t0 = time.time()
    retrieved_count = 0
    if use_few_shot and is_default_schema:
        try:
            exs = retrieve_examples(question)
            retrieved_count = len(exs)
        except Exception:
            pass
    retrieval_ms = (time.time() - retrieval_t0) * 1000.0
    tracker.set_retrieval(retrieval_ms, retrieved_count)

    # Track generation
    gen_t0 = time.time()
    sql = generate_sql(
        question,
        llm,
        use_few_shot=use_few_shot,
        schema_description=schema_description,
        business_rules=business_rules,
        dialect=dialect,
        is_default_schema=is_default_schema,
    )
    gen_ms = (time.time() - gen_t0) * 1000.0
    tracker.set_generation(sql, gen_ms)

    if sql.startswith("REFUSED"):
        tracker.set_validation_failed("REFUSED: Sensitive data requested")
        return sql, None, None

    validation = validate_query(
        sql,
        schema_whitelist=schema_whitelist,
        dialect=dialect,
        blocked_columns=blocked_columns,
    )

    if not validation.is_valid:
        error_summary = "; ".join(validation.errors)
        tracker.set_validation_failed(f"REJECTED: {error_summary}")
        return sql, None, f"REJECTED: {error_summary}"

    # Track execution & mask PII
    exec_t0 = time.time()
    try:
        columns, rows = execute_query(engine, sql)
        exec_ms = (time.time() - exec_t0) * 1000.0
        if rows is not None:
            rows = mask_pii_data(columns, rows)
            tracker.set_execution(len(rows), exec_ms)
        else:
            tracker.set_execution(0, exec_ms)
        return sql, columns, rows
    except Exception as e:
        exec_ms = (time.time() - exec_t0) * 1000.0
        tracker.set_execution_error(str(e), exec_ms)
        return sql, None, f"EXECUTION_ERROR: {e}"


def main():
    print("Universal NL2SQL Chain — type a question, or 'exit' to quit.")
    print("Type 'toggle' to switch between few-shot and zero-shot mode.\n")

    engine, dialect, source_desc = get_default_engine()
    print(f"Connected to: {source_desc} (Dialect: {dialect})\n")

    llm = get_llm()
    use_few_shot = True

    while True:
        question = input("> ").strip()
        if question.lower() in ("exit", "quit"):
            break
        if question.lower() == "toggle":
            use_few_shot = not use_few_shot
            print(f"Few-shot mode: {'ON' if use_few_shot else 'OFF'}\n")
            continue
        if not question:
            continue

        try:
            sql, columns, rows = ask(
                question,
                llm=llm,
                use_few_shot=use_few_shot,
                engine=engine,
                dialect=dialect
            )
        except Exception as e:
            print(f"Error: {e}\n")
            continue

        print(f"\nGenerated SQL:\n  {sql}\n")

        if columns is None and isinstance(rows, str):
            print(f"{rows}\n")
        elif sql.startswith("REFUSED"):
            print("Query blocked by business rules.\n")
        else:
            print(f"Columns: {columns}")
            for row in rows[:20]:
                print(f"  {row}")
            if len(rows) > 20:
                print(f"  ... and {len(rows) - 20} more rows")
            print()


if __name__ == "__main__":
    main()
