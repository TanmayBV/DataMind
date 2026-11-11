"""
clean_data.py
-------------
Data cleaning & entity normalization pipeline.

Four-stage pipeline:
  1. Normalization   — trim whitespace, collapse casing
  2. Entity merging   — fuzzy-match each raw value against canonical reference lists (rapidfuzz)
  3. FK resolution    — map cleaned department name -> department_id
  4. Validation       — flag rows that fail business rules instead of silently dropping

Reads from data/employees_raw.csv (+ departments.csv, project_assignments_raw.csv, projects.csv) and writes:
    data/employees_clean.csv
    data/project_assignments_clean.csv
    data/flagged_records.csv          -> rows that failed validation
    data/before_after_examples.csv    -> sample transformations for audit

Run:
    python data_pipeline/clean_data.py
"""

import csv
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "config"))
from config import (
    DATA_DIR, FUZZY_THRESHOLD,
    CANONICAL_CITIES, CANONICAL_ROLES, CANONICAL_STATUSES,
    CANONICAL_DEPARTMENTS, CANONICAL_PROJECTS
)

from rapidfuzz import fuzz, process

# ---------------------------------------------------------------
# Alias tables: exact, curated abbreviation -> canonical mappings.
# English enterprise aliases handling abbreviations and colloquial terms.
# ---------------------------------------------------------------

CITY_ALIASES = {
    "nyc": "New York", "new york city": "New York", "n.y.c.": "New York",
    "istambul": "Istanbul",
    "moskva": "Moscow",
    "dubai, uae": "Dubai", "dubai uae": "Dubai",
    "london, uk": "London", "london uk": "London",
}

DEPARTMENT_ALIASES = {
    "hr": "Human Resources", "h.r.": "Human Resources",
    "hr dept": "Human Resources", "personnel": "Human Resources", "human res": "Human Resources",
    "eng": "Engineering", "eng.": "Engineering", "eng dept": "Engineering",
    "fin": "Finance", "fin.": "Finance", "finance dept": "Finance",
    "pm": "Project Management", "pmo": "Project Management", "pm lead": "Project Management",
    "it": "IT", "i.t.": "IT", "information technology": "IT",
}

ROLE_ALIASES = {
    "sw engineer": "Software Engineer",
    "software eng.": "Software Engineer",
    "software engr": "Software Engineer",
    "civil eng.": "Civil Engineer",
    "pm lead": "Project Manager",
}

# ---------------------------------------------------------------
# SymSpell Spelling Corrector (Stage 2)
# Initialized with canonical enterprise domain terms
# ---------------------------------------------------------------
_sym_spell = None


def get_symspell():
    global _sym_spell
    if _sym_spell is None:
        try:
            from symspellpy import SymSpell, Verbosity
            _sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
            # Seed with all canonical words and aliases
            all_terms = (
                CANONICAL_CITIES + CANONICAL_ROLES + CANONICAL_STATUSES +
                list(CITY_ALIASES.values()) + list(DEPARTMENT_ALIASES.values()) +
                ["Engineering", "Finance", "Human Resources", "Project Management", "IT"]
            )
            for term in all_terms:
                _sym_spell.create_dictionary_entry(term.lower(), 100)
        except Exception:
            _sym_spell = False
    return _sym_spell


def normalize_whitespace_case(value: str) -> str:
    """Stage 1: basic normalization — trim, collapse whitespace."""
    if value is None:
        return ""
    return " ".join(value.strip().split())


def correct_spelling(value: str) -> str:
    """Stage 2: SymSpell spelling correction using domain dictionary."""
    if not value:
        return value
    sym = get_symspell()
    if not sym:
        return value
    try:
        from symspellpy import Verbosity
        suggestions = sym.lookup(value.lower(), Verbosity.CLOSEST, max_edit_distance=2)
        if suggestions:
            return suggestions[0].term
    except Exception:
        pass
    return value


def resolve_value(raw_value: str, canonical_list: list[str], alias_table: dict):
    """
    Stage 3: entity merging:
      a) exact alias lookup (case-insensitive)      -> handles abbreviations
      b) spell-corrected alias lookup               -> handles typo'd abbreviations
      c) fuzzy match against canonical list         -> handles phrasing/typos
    Returns (canonical_value_or_None, method, score)
    """
    cleaned = normalize_whitespace_case(raw_value)
    if not cleaned:
        return None, "empty", 0

    # Pass a: exact alias match (case-insensitive)
    alias_hit = alias_table.get(cleaned.lower())
    if alias_hit:
        return alias_hit, "alias", 100

    # Also treat exact match to a canonical value as a hit
    for canon in canonical_list:
        if cleaned.lower() == canon.lower():
            return canon, "exact_ci", 100

    # Pass b: SymSpell spelling correction check
    corrected = correct_spelling(cleaned)
    if corrected != cleaned.lower():
        if corrected in alias_table:
            return alias_table[corrected], "symspell_alias", 95
        for canon in canonical_list:
            if corrected == canon.lower():
                return canon, "symspell", 95

    # Pass c: fuzzy match against canonical list
    match = process.extractOne(
        cleaned, canonical_list, scorer=fuzz.token_sort_ratio
    )
    if match is None:
        return None, "no_match", 0

    best_value, score, _ = match
    if score >= FUZZY_THRESHOLD:
        return best_value, "fuzzy", score
    return None, "below_threshold", score


def canonicalize_status(raw_status: str):
    cleaned = normalize_whitespace_case(raw_status).lower()
    if cleaned in CANONICAL_STATUSES:
        return cleaned
    return None


def load_department_lookup():
    path = os.path.join(DATA_DIR, "departments.csv")
    depts = []
    dept_to_id = {}
    with open(path) as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            name = row["department_name"]
            depts.append(name)
            dept_to_id[name] = int(row.get("department_id", i + 1))
    return depts, dept_to_id


def load_project_lookup():
    path = os.path.join(DATA_DIR, "projects.csv")
    projects = []
    project_to_id = {}
    with open(path) as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            name = row["project_name"]
            projects.append(name)
            project_to_id[name] = int(row.get("project_id", i + 1))
    return projects, project_to_id


def clean_employees():
    canonical_depts, dept_to_id = load_department_lookup()

    in_path = os.path.join(DATA_DIR, "employees_raw.csv")
    clean_rows = []
    flagged_rows = []
    before_after = []

    with open(in_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            city, city_method, city_score = resolve_value(row["city_raw"], CANONICAL_CITIES, CITY_ALIASES)
            role, role_method, role_score = resolve_value(row["role_raw"], CANONICAL_ROLES, ROLE_ALIASES)
            dept, dept_method, dept_score = resolve_value(row["department_raw"], canonical_depts, DEPARTMENT_ALIASES)
            status = canonicalize_status(row["employee_status"])

            issues = []
            if city is None:
                issues.append("unresolved_city")
            if role is None:
                issues.append("unresolved_role")
            if dept is None:
                issues.append("unresolved_department")
            if status is None:
                issues.append("invalid_status")

            if issues:
                flagged_rows.append({**row, "issues": ";".join(issues)})
                continue

            clean_rows.append({
                "employee_id": row["employee_id"],
                "full_name": row["full_name"],
                "role": role,
                "city": city,
                "department_id": dept_to_id[dept],
                "is_payroll": row["is_payroll"],
                "employee_status": status,
                "hire_date": row["hire_date"],
                # salary intentionally excluded from employees_clean
            })

            # collect a few illustrative before/after rows for the README
            if len(before_after) < 15:
                before_after.append({
                    "field": "city", "raw": row["city_raw"],
                    "cleaned": city, "method": city_method, "match_score": city_score,
                })
                before_after.append({
                    "field": "role", "raw": row["role_raw"],
                    "cleaned": role, "method": role_method, "match_score": role_score,
                })
                before_after.append({
                    "field": "department", "raw": row["department_raw"],
                    "cleaned": dept, "method": dept_method, "match_score": dept_score,
                })

    return clean_rows, flagged_rows, before_after


PROJECT_ALIASES = {}  # projects in this dataset don't need acronym expansion


def clean_project_assignments():
    canonical_projects, project_to_id = load_project_lookup()

    in_path = os.path.join(DATA_DIR, "project_assignments_raw.csv")
    clean_rows = []
    dropped = 0

    with open(in_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            project, method, score = resolve_value(
                row["project_name_raw"], canonical_projects, PROJECT_ALIASES
            )
            if project is None:
                dropped += 1
                continue
            clean_rows.append({
                "assignment_id": row["assignment_id"],
                "employee_id": row["employee_id"],
                "project_id": project_to_id[project],
            })

    return clean_rows, dropped


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows):,} rows -> {path}")


def main():
    clean_rows, flagged_rows, before_after = clean_employees()
    write_csv(
        os.path.join(DATA_DIR, "employees_clean.csv"),
        clean_rows,
        fieldnames=["employee_id", "full_name", "role", "city", "department_id",
                    "is_payroll", "employee_status", "hire_date"],
    )

    if flagged_rows:
        write_csv(
            os.path.join(DATA_DIR, "flagged_records.csv"),
            flagged_rows,
            fieldnames=list(flagged_rows[0].keys()),
        )

    write_csv(
        os.path.join(DATA_DIR, "before_after_examples.csv"),
        before_after,
        fieldnames=["field", "raw", "cleaned", "method", "match_score"],
    )

    assignments_clean, dropped = clean_project_assignments()
    write_csv(
        os.path.join(DATA_DIR, "project_assignments_clean.csv"),
        assignments_clean,
        fieldnames=["assignment_id", "employee_id", "project_id"],
    )

    # ---- Summary stats: your Day 6 ablation table starts here ----
    total = len(clean_rows) + len(flagged_rows)
    accuracy = len(clean_rows) / total * 100 if total else 0
    print("\n=== Cleaning Pipeline Summary ===")
    print(f"Total raw employee records : {total:,}")
    print(f"Successfully cleaned       : {len(clean_rows):,} ({accuracy:.1f}%)")
    print(f"Flagged for manual review  : {len(flagged_rows):,} ({100 - accuracy:.1f}%)")
    print(f"Project assignments dropped: {dropped:,} (unresolved project names)")
    print("\nSee data/before_after_examples.csv for your README's Table I equivalent.")
    print("See data/flagged_records.csv for records needing manual review.")


if __name__ == "__main__":
    main()
