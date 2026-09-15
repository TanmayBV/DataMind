"""
load_to_postgres.py
--------------------
Loads the generated CSVs into your free Postgres instance
(Supabase or Neon) using the schema in sql/schema.sql.

Setup:
    1. Create a free project at https://supabase.com or https://neon.tech
    2. Copy your connection string (looks like:
       postgresql://user:password@host:port/dbname)
    3. Set it as an environment variable:
           export DATABASE_URL="postgresql://...your connection string..."
    4. Run:
           python scripts/load_to_postgres.py
"""

import csv
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "config"))
from config import DATABASE_URL, SQL_DIR, require_database_url

import psycopg2

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
SCHEMA_FILE = os.path.join(SQL_DIR, "schema.sql")


def get_connection():
    require_database_url()
    return psycopg2.connect(DATABASE_URL)


def run_schema(conn):
    with open(SCHEMA_FILE, "r") as f:
        schema_sql = f.read()
    with conn.cursor() as cur:
        cur.execute(schema_sql)
    conn.commit()
    print("Schema applied.")


def load_departments(conn):
    with open(os.path.join(DATA_DIR, "departments.csv")) as f:
        reader = csv.DictReader(f)
        rows = [(r["department_name"],) for r in reader]
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO departments (department_name) VALUES (%s)", rows
        )
    conn.commit()
    print(f"Loaded {len(rows)} departments.")


def load_projects(conn):
    with open(os.path.join(DATA_DIR, "projects.csv")) as f:
        reader = csv.DictReader(f)
        rows = [(r["project_code"], r["project_name"]) for r in reader]
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO projects (project_code, project_name) VALUES (%s, %s)", rows
        )
    conn.commit()
    print(f"Loaded {len(rows)} projects.")


def load_employees_raw(conn):
    with open(os.path.join(DATA_DIR, "employees_raw.csv")) as f:
        reader = csv.DictReader(f)
        rows = [
            (
                int(r["employee_id"]),
                r["full_name"],
                r["role_raw"],
                r["city_raw"],
                r["department_raw"],
                r["is_payroll"] == "True",
                r["employee_status"],
                float(r["salary"]),
                r["hire_date"],
                r["source_language"],
            )
            for r in reader
        ]
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO employees_raw
                (employee_id, full_name, role_raw, city_raw, department_raw,
                 is_payroll, employee_status, salary, hire_date, source_language)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            rows,
        )
    conn.commit()
    print(f"Loaded {len(rows)} raw employee records.")


def main():
    conn = get_connection()
    try:
        run_schema(conn)
        load_departments(conn)
        load_projects(conn)
        load_employees_raw(conn)
        print("\nDay 1 load complete. employees_raw is populated and intentionally messy.")
        print("employees_clean is empty — that's what you build in Day 2.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
