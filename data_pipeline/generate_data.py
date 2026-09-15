"""
generate_data.py
-----------------
Generates a synthetic, intentionally MESSY HR dataset for the
NL2SQL RAG project (Day 1 of the build plan).

Produces CSVs in /data that mirror the kind of real-world
inconsistencies described in the reference paper: mixed casing,
city-name variants, department name variants, and duplicate
project-code spellings across "languages" (simulated, not real
translation — just realistic string variation).

Run:
    python scripts/generate_data.py --n_employees 3000
"""

import argparse
import csv
import os
import random
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "config"))
from config import DATA_DIR as OUT_DIR

from faker import Faker

fake = Faker()
random.seed(42)
Faker.seed(42)

os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------------------------------------------
# Reference data with deliberate "messiness" variants per value.
# Each canonical value maps to several ways it might appear in
# a real, decentralized-entry ERP system.
# ---------------------------------------------------------------

CITY_VARIANTS = {
    "Moscow": ["Moscow", "Moskva", "moscow", "MOSCOW", "Moskva "],
    "Istanbul": ["Istanbul", "istanbul", "ISTANBUL", "Istambul", "Istanbul "],
    "New York": ["New York", "new york", "NYC", "New York City", "NEW YORK"],
    "London": ["London", "london", "LONDON", "London, UK"],
    "Berlin": ["Berlin", "berlin", "BERLIN", "Berlin "],
    "Dubai": ["Dubai", "dubai", "DUBAI", "Dubai, UAE"],
}

DEPARTMENT_VARIANTS = {
    "Human Resources": ["Human Resources", "human resources", "HR", "H.R.", "İnsan Kaynakları"],
    "Engineering": ["Engineering", "engineering", "ENG", "Eng."],
    "Finance": ["Finance", "finance", "FIN", "Fin."],
    "Project Management": ["Project Management", "project management", "PM", "PMO"],
    "IT": ["IT", "it", "I.T.", "Information Technology"],
}

ROLE_VARIANTS = {
    "Civil Engineer": ["civil engineer", "Civil Engineer", "CIVIL ENGINEER", "civil Engineer"],
    "HR Analyst": ["hr analyst", "HR Analyst", "HR ANALYST", "Hr Analyst"],
    "Project Manager": ["project manager", "Project Manager", "PROJECT MANAGER"],
    "Software Engineer": ["software engineer", "Software Engineer", "SW Engineer", "Software eng."],
    "Accountant": ["accountant", "Accountant", "ACCOUNTANT"],
    "Data Analyst": ["data analyst", "Data Analyst", "DATA ANALYST", "data Analyst"],
}

PROJECT_VARIANTS = {
    "GPP": ["GPP", "Gpp", "gpp", "GPP project", "Gpp Project"],
    "Skyline Tower": ["Skyline Tower", "skyline tower", "SKYLINE TOWER", "Skyline-Tower"],
    "Metro Expansion": ["Metro Expansion", "metro expansion", "METRO EXPANSION"],
    "Cloud Migration": ["Cloud Migration", "cloud migration", "Cloud-Migration"],
}

STATUS_VARIANTS = {
    "active": ["active", "Active", "ACTIVE", "Active "],
    "terminated": ["terminated", "Terminated", "TERMINATED"],
}

LANGUAGES = ["en", "ru", "tr"]

ROLE_SALARY_RANGE = {
    "Civil Engineer": (55000, 95000),
    "HR Analyst": (45000, 70000),
    "Project Manager": (70000, 120000),
    "Software Engineer": (65000, 130000),
    "Accountant": (50000, 80000),
    "Data Analyst": (55000, 90000),
}


def messy_choice(variants_map):
    """Pick a canonical key, then return (canonical, messy_variant)."""
    canonical = random.choice(list(variants_map.keys()))
    variant = random.choice(variants_map[canonical])
    return canonical, variant


def random_date(start_year=2015, end_year=2024):
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def generate_employees(n):
    rows = []
    for emp_id in range(1, n + 1):
        _, city_variant = messy_choice(CITY_VARIANTS)
        _, dept_variant = messy_choice(DEPARTMENT_VARIANTS)
        role_canonical, role_variant = messy_choice(ROLE_VARIANTS)
        _, status_variant = messy_choice(STATUS_VARIANTS)

        is_payroll = random.random() > 0.15  # ~15% contractors
        salary_lo, salary_hi = ROLE_SALARY_RANGE[role_canonical]
        salary = round(random.uniform(salary_lo, salary_hi), 2)

        # Inject ~4% genuinely unresolvable noise per field, mirroring
        # real-world free-text entry errors that no reasonable fuzzy
        # match / alias table should silently resolve (mirrors the
        # paper's own 2.2% residual error rate after cleaning).
        if random.random() < 0.04:
            city_variant = random.choice(["N/A", "unknown", "???", "", "TBD"])
        if random.random() < 0.04:
            role_variant = random.choice(["misc", "n/a", "various", "TBD", ""])
        if random.random() < 0.04:
            dept_variant = random.choice(["misc", "unassigned", "???", ""])

        rows.append({
            "employee_id": emp_id,
            "full_name": fake.name(),
            "role_raw": role_variant,
            "city_raw": city_variant,
            "department_raw": dept_variant,
            "project_raw": "",  # filled via project_assignments
            "is_payroll": is_payroll,
            "employee_status": status_variant,
            "salary": salary,
            "hire_date": random_date().isoformat(),
            "source_language": random.choice(LANGUAGES),
        })
    return rows


def generate_project_assignments(n_employees, n_projects_per_emp_max=2):
    rows = []
    assignment_id = 1
    project_names = list(PROJECT_VARIANTS.keys())
    for emp_id in range(1, n_employees + 1):
        n_assignments = random.randint(0, n_projects_per_emp_max)
        chosen = random.sample(project_names, k=min(n_assignments, len(project_names)))
        for proj in chosen:
            rows.append({
                "assignment_id": assignment_id,
                "employee_id": emp_id,
                "project_name_raw": random.choice(PROJECT_VARIANTS[proj]),
            })
            assignment_id += 1
    return rows


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows):,} rows -> {path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n_employees", type=int, default=3000)
    args = parser.parse_args()

    employees = generate_employees(args.n_employees)
    write_csv(
        os.path.join(OUT_DIR, "employees_raw.csv"),
        employees,
        fieldnames=list(employees[0].keys()),
    )

    assignments = generate_project_assignments(args.n_employees)
    write_csv(
        os.path.join(OUT_DIR, "project_assignments_raw.csv"),
        assignments,
        fieldnames=list(assignments[0].keys()),
    )

    # Reference tables (clean, small)
    departments = [{"department_name": d} for d in DEPARTMENT_VARIANTS.keys()]
    write_csv(os.path.join(OUT_DIR, "departments.csv"), departments, ["department_name"])

    projects = [{"project_code": p, "project_name": p} for p in PROJECT_VARIANTS.keys()]
    write_csv(os.path.join(OUT_DIR, "projects.csv"), projects, ["project_code", "project_name"])

    print("\nDay 1 dataset generation complete.")
    print("Next: load these CSVs into a free Postgres instance (Supabase/Neon)")
    print("using the schema in sql/schema.sql, then move to Day 2 (cleaning pipeline).")


if __name__ == "__main__":
    main()
