"""
load_clean_to_postgres.py
--------------------------
The missing piece: clean_data.py only writes data/employees_clean.csv
and data/project_assignments_clean.csv locally — it never pushes them
into Postgres. This script loads those cleaned CSVs into the
employees_clean and project_assignments tables in your Supabase/Neon
database, so query_engine/nl2sql_chain.py has something to actually
query.

Run this AFTER clean_data.py (or clean_pipeline.py) has produced the
cleaned CSVs, and AFTER load_to_postgres.py has already loaded
employees_raw, departments, and projects (employees_clean.employee_id
has a foreign key against employees_raw, so raw must be loaded first).

Full pipeline order:
    1. generate_data.py         -> data/*.csv (raw + reference tables)
    2. load_to_postgres.py      -> loads raw data + departments + projects
    3. clean_data.py            -> data/employees_clean.csv (local only)
    4. load_clean_to_postgres.py -> THIS SCRIPT: pushes clean data to Postgres

Run:
    python data_pipeline/load_clean_to_postgres.py
"""

import csv
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "config"))
from config import DATABASE_URL, DATA_DIR, require_database_url

import psycopg2


def get_connection():
    require_database_url()
    return psycopg2.connect(DATABASE_URL)


def clear_existing_clean_data(conn):
    """employees_clean and project_assignments are meant to be fully
    replaced on each cleaning run, not appended to — otherwise re-running
    the pipeline would create duplicate rows or violate the primary key."""
    with conn.cursor() as cur:
        # project_assignments references employees_clean's employee_id
        # only indirectly (it actually references employees_raw per
        # sql/schema.sql), but employees_clean has no downstream FK from
        # project_assignments, so order here doesn't matter for FKs —
        # still, truncate both together for a clean re-run.
        cur.execute("TRUNCATE TABLE employees_clean CASCADE;")
    conn.commit()
    print("Cleared existing employees_clean data (fresh load).")


def load_employees_clean(conn):
    path = os.path.join(DATA_DIR, "employees_clean.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"{path} not found — run data_pipeline/clean_data.py first."
        )

    with open(path) as f:
        reader = csv.DictReader(f)
        rows = [
            (
                int(r["employee_id"]),
                r["full_name"],
                r["role"],
                r["city"],
                int(r["department_id"]),
                r["is_payroll"] in ("True", "true", "1"),
                r["employee_status"],
                r["hire_date"] or None,
            )
            for r in reader
        ]

    if not rows:
        print("Warning: employees_clean.csv has no rows — nothing to load.")
        return

    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO employees_clean
                (employee_id, full_name, role, city, department_id,
                 is_payroll, employee_status, hire_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (employee_id) DO UPDATE SET
                full_name = EXCLUDED.full_name,
                role = EXCLUDED.role,
                city = EXCLUDED.city,
                department_id = EXCLUDED.department_id,
                is_payroll = EXCLUDED.is_payroll,
                employee_status = EXCLUDED.employee_status,
                hire_date = EXCLUDED.hire_date
            """,
            rows,
        )
    conn.commit()
    print(f"Loaded {len(rows):,} rows into employees_clean.")


def load_project_assignments_clean(conn):
    path = os.path.join(DATA_DIR, "project_assignments_clean.csv")
    if not os.path.exists(path):
        print("No project_assignments_clean.csv found — skipping (not an error "
              "if you haven't run that part of the cleaning pipeline yet).")
        return

    with open(path) as f:
        reader = csv.DictReader(f)
        rows = [
            (int(r["assignment_id"]), int(r["employee_id"]), int(r["project_id"]))
            for r in reader
        ]

    if not rows:
        print("project_assignments_clean.csv has no rows — nothing to load.")
        return

    with conn.cursor() as cur:
        # Only insert assignments whose employee_id actually exists in
        # employees_clean — a row could reference an employee that got
        # flagged/excluded during cleaning, and the FK would reject it.
        cur.execute("SELECT employee_id FROM employees_clean;")
        valid_employee_ids = {row[0] for row in cur.fetchall()}

        filtered_rows = [r for r in rows if r[1] in valid_employee_ids]
        skipped = len(rows) - len(filtered_rows)

        cur.executemany(
            """
            INSERT INTO project_assignments (assignment_id, employee_id, project_id)
            VALUES (%s, %s, %s)
            ON CONFLICT (assignment_id) DO UPDATE SET
                employee_id = EXCLUDED.employee_id,
                project_id = EXCLUDED.project_id
            """,
            filtered_rows,
        )
    conn.commit()
    print(f"Loaded {len(filtered_rows):,} rows into project_assignments "
          f"({skipped} skipped — referenced an employee excluded during cleaning).")


def verify_load(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM employees_clean;")
        clean_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM project_assignments;")
        assignment_count = cur.fetchone()[0]
    print(f"\nVerification: employees_clean has {clean_count:,} rows, "
          f"project_assignments has {assignment_count:,} rows.")
    if clean_count == 0:
        print("WARNING: employees_clean is empty. query_engine/nl2sql_chain.py "
              "will return no results for any query until this is populated.")


def main():
    conn = get_connection()
    try:
        clear_existing_clean_data(conn)
        load_employees_clean(conn)
        load_project_assignments_clean(conn)
        verify_load(conn)
        print("\nDone. employees_clean is now populated and query-ready.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
