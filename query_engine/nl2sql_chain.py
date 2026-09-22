"""
nl2sql_chain.py
----------------
Day 3: baseline natural-language-to-SQL chain.

Design note (important): this is written to be schema-agnostic where
possible — the SCHEMA_DESCRIPTION and BUSINESS_RULES below are the only
things you'd need to change to point this at a *different* company's
already-clean database. The query_engine/ folder is meant to be reusable;
data_pipeline/ (Day 1-2) is a separate, optional component that exists so
this repo can be demoed without needing your own production database.

Flow (zero-shot for now — few-shot retrieval is added in Day 4):
    user question (English)
        -> LLM generates SQL, constrained by schema + business rules
        -> basic guard: reject anything that isn't a single SELECT
        -> execute against Postgres
        -> return formatted result

Run interactively:
    python query_engine/nl2sql_chain.py
"""

import os
import re
import sys
import time

from dotenv import load_dotenv

load_dotenv()  # load .env file if present

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "config"))
from config import DATABASE_URL, GEMINI_API_KEY, LLM_MODEL, require_database_url

import psycopg2
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

from retriever import retrieve_examples, format_examples_for_prompt
from validators import validate_query
from validators import validate_query

# ---------------------------------------------------------------
# Schema description + business rules.
# This is the "policy layer" the reference paper describes — the
# explicit encoding of things that aren't obvious from column names
# alone. Update this if you point the engine at a different schema.
# ---------------------------------------------------------------

SCHEMA_DESCRIPTION = """
Tables:

employees_clean (
    employee_id     INTEGER PRIMARY KEY,
    full_name       TEXT,
    role            TEXT,       -- e.g. 'Civil Engineer', 'HR Analyst'
    city            TEXT,       -- e.g. 'Moscow', 'Istanbul'
    department_id   INTEGER REFERENCES departments(department_id),
    is_payroll      BOOLEAN,    -- true = payroll employee, false = contractor
    employee_status TEXT,       -- 'active' or 'terminated'
    hire_date       DATE
)
-- NOTE: employees_clean does NOT include salary. Never assume a salary
-- column exists on this table.

departments (
    department_id   SERIAL PRIMARY KEY,
    department_name TEXT
)

projects (
    project_id   SERIAL PRIMARY KEY,
    project_code TEXT,
    project_name TEXT
)

project_assignments (
    assignment_id INTEGER PRIMARY KEY,
    employee_id   INTEGER REFERENCES employees_clean(employee_id),
    project_id    INTEGER REFERENCES projects(project_id)
)
"""

BUSINESS_RULES = """
Business rules (apply these even if not explicitly stated in the question):
1. "Active employees" or "current staff" means employee_status = 'active'.
2. Unless the question explicitly asks about contractors, assume
   is_payroll = true (i.e. exclude contractors from general staff counts).
3. NEVER generate a query that references a salary, bonus, compensation,
   or wage column. No such column exists in employees_clean — if asked,
   respond with exactly: REFUSED: sensitive financial data
4. Only generate SELECT statements. Never generate INSERT, UPDATE,
   DELETE, DROP, ALTER, or any other data-modifying statement.
5. Always JOIN through department_id / project_id — never guess at a
   department or project name existing as a free-text column on
   employees_clean.
"""

SYSTEM_PROMPT_BASE = f"""You are a SQL generation assistant for a PostgreSQL database.
Given a natural language question, generate ONE valid PostgreSQL SELECT
query that answers it. Return ONLY the SQL query — no explanation, no
markdown code fences, no commentary.

{SCHEMA_DESCRIPTION}

{BUSINESS_RULES}
"""


def get_llm():
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add your Gemini API key to .env"
        )

    return ChatGoogleGenerativeAI(
        model=LLM_MODEL,
        google_api_key=GEMINI_API_KEY,
        temperature=0,
    )


def build_system_prompt(question: str, use_few_shot: bool = True) -> str:
    """
    Day 4: if use_few_shot is True, retrieve the top-k most similar
    validated examples from the FAISS index and inject them into the
    prompt. This is the key difference from Day 3's zero-shot baseline —
    run evaluate.py (Day 6) to see the measured accuracy difference.
    """
    if not use_few_shot:
        return SYSTEM_PROMPT_BASE

    examples = retrieve_examples(question)
    examples_block = format_examples_for_prompt(examples)
    return f"{SYSTEM_PROMPT_BASE}\n{examples_block}"


def generate_sql(
    question: str,
    llm,
    use_few_shot: bool = True
) -> str:

    system_prompt = build_system_prompt(
        question,
        use_few_shot=use_few_shot
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=question),
    ]

    max_retries = 3

    for attempt in range(max_retries):
        try:
            response = llm.invoke(messages)
            break

        except Exception as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(
                        f"Gemini temporarily unavailable. "
                        f"Retrying in {wait_time}s..."
                    )
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
        r"^```sql\s*|\s*```$",
        "",
        sql,
        flags=re.IGNORECASE
    ).strip()

    return sql


def is_safe_select(sql: str) -> bool:
    """
    DEPRECATED as of Day 5 — kept only for reference/comparison against
    validators.validate_query(), which replaces this with real SQL
    parsing (schema whitelist + blocked-column checks + proper statement
    typing) instead of string/regex matching. See docs/DAY5_README.md
    for why the string-based approach here is insufficient on its own.
    """
    normalized = sql.strip().rstrip(";").upper()
    if not normalized.startswith("SELECT"):
        return False
    if ";" in sql.strip().rstrip(";"):  # a second statement smuggled in
        return False
    forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "GRANT"]
    if any(word in normalized for word in forbidden):
        return False
    return True


def run_query(sql: str):
    require_database_url()
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
        return columns, rows
    finally:
        conn.close()


def ask(question: str, llm=None, use_few_shot: bool = True):
    """Main entry point: question in, (sql, columns, rows) or error out.

    As of Day 5, generated SQL goes through the full validation layer
    (validators.validate_query) instead of the old string-based guard —
    schema whitelist checking and blocked-column detection via real SQL
    parsing, not substring matching.
    """
    llm = llm or get_llm()
    sql = generate_sql(question, llm, use_few_shot=use_few_shot)

    if sql.startswith("REFUSED"):
        return sql, None, None

    validation = validate_query(sql)
    if not validation.is_valid:
        error_summary = "; ".join(validation.errors)
        return sql, None, f"REJECTED: {error_summary}"

    columns, rows = run_query(sql)
    return sql, columns, rows

def main():
    print("NL2SQL chain (Day 5: schema-validated + few-shot) — type a question, or 'exit' to quit.")
    print("Type 'toggle' to switch between few-shot and zero-shot mode.\n")
    llm = get_llm()
    use_few_shot = True
    while True:
        question = input("> ").strip()
        if question.lower() in ("exit", "quit"):
            break
        if question.lower() == "toggle":
            use_few_shot = not use_few_shot
            print(f"few-shot mode: {'ON' if use_few_shot else 'OFF'}\n")
            continue
        if not question:
            continue

        try:
            sql, columns, rows = ask(question, llm=llm, use_few_shot=use_few_shot)
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
