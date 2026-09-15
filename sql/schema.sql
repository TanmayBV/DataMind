-- ============================================================
-- Synthetic HR ERP Schema (mirrors the multi-table, messy-field
-- structure described in the RAG-driven data governance paper)
-- ============================================================

DROP TABLE IF EXISTS project_assignments CASCADE;
DROP TABLE IF EXISTS employees_raw CASCADE;
DROP TABLE IF EXISTS employees_clean CASCADE;
DROP TABLE IF EXISTS departments CASCADE;
DROP TABLE IF EXISTS projects CASCADE;

-- Departments (kept clean, small reference table)
CREATE TABLE departments (
    department_id   SERIAL PRIMARY KEY,
    department_name TEXT NOT NULL
);

-- Projects (kept clean, small reference table)
CREATE TABLE projects (
    project_id   SERIAL PRIMARY KEY,
    project_code TEXT NOT NULL,
    project_name TEXT NOT NULL
);

-- RAW employee table: intentionally messy, mirrors real-world
-- decentralized manual HR entry (mixed casing, city variants,
-- inconsistent role naming, duplicate contractor rows).
CREATE TABLE employees_raw (
    employee_id     SERIAL PRIMARY KEY,
    full_name       TEXT,
    role_raw        TEXT,           -- e.g. "civil engineer", "Civil Engineer", "CIVIL ENGINEER"
    city_raw        TEXT,           -- e.g. "Moscow", "Moskva", "moscow "
    department_raw  TEXT,           -- e.g. "Human Resources", "human resources", "HR"
    project_raw     TEXT,           -- e.g. "GPP", "Gpp project", "gpp"
    is_payroll      BOOLEAN,
    employee_status TEXT,           -- 'active' / 'Active' / 'ACTIVE' / 'terminated'
    salary          NUMERIC,        -- sensitive field — must be excluded from NL2SQL access
    hire_date       DATE,
    source_language TEXT            -- 'en', 'ru', 'tr' — which language the raw entry was made in
);

-- CLEAN employee table: output of your Day 2 cleaning pipeline.
-- Same shape, normalized values, foreign keys resolved.
CREATE TABLE employees_clean (
    employee_id     INTEGER PRIMARY KEY REFERENCES employees_raw(employee_id),
    full_name       TEXT NOT NULL,
    role            TEXT NOT NULL,
    city            TEXT NOT NULL,
    department_id   INTEGER REFERENCES departments(department_id),
    is_payroll      BOOLEAN NOT NULL,
    employee_status TEXT NOT NULL,
    hire_date       DATE
    -- NOTE: salary intentionally omitted — safety layer should
    -- reject any NL query that tries to reach financial data.
);

CREATE TABLE project_assignments (
    assignment_id INTEGER PRIMARY KEY,
    employee_id   INTEGER REFERENCES employees_raw(employee_id),
    project_id    INTEGER REFERENCES projects(project_id)
);
