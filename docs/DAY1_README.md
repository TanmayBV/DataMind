# NL2SQL RAG Project — Day 1: Domain & Messy Dataset

A scaled-down, free-tier version of a RAG-driven NL2SQL system for a
synthetic HR ERP domain — inspired by production patterns like
schema-constrained few-shot retrieval, data cleaning pipelines, and
safety-layered query generation.

## What's in this repo so far

```
nl2sql-rag/
├── sql/
│   └── schema.sql              # employees_raw / employees_clean / departments / projects / project_assignments
├── scripts/
│   ├── generate_data.py        # generates synthetic MESSY data (Day 1)
│   └── load_to_postgres.py     # loads CSVs into free Postgres (Supabase/Neon)
├── data/                       # generated CSVs (gitignore this in a real repo if large)
└── requirements.txt
```

## Day 1 checklist

- [x] Schema designed: 5 tables, intentional messiness in `employees_raw`
      (casing variants, city/department/role/status spelling variants)
      and a `salary` column that should later be blocked from NL access
- [x] Synthetic dataset generated: 3,000 employees, ~3,000 project
      assignments, reproducible via fixed random seed
- [ ] **Your turn:** stand up a free Postgres instance and load the data

## Setting up free Postgres (5-10 minutes)

Pick one:

**Option A — Supabase** (recommended, has a nice web SQL editor too)
1. Go to https://supabase.com → New project (free tier)
2. Project Settings → Database → copy the connection string (URI, not the pooled one for this)

**Option B — Neon**
1. Go to https://neon.tech → New project (free tier)
2. Copy the connection string from the dashboard

Then:

```bash
export DATABASE_URL="postgresql://your-connection-string-here"

pip install -r requirements.txt --break-system-packages

# regenerate data if you want a different size:
python scripts/generate_data.py --n_employees 3000

# load schema + data into your free Postgres:
python scripts/load_to_postgres.py
```

## Sanity check after loading

Run this in Supabase's SQL editor (or `psql`) to confirm the messiness
is really there — this is the exact kind of inconsistency your Day 2
cleaning pipeline needs to resolve:

```sql
SELECT DISTINCT city_raw FROM employees_raw ORDER BY city_raw;
-- You should see: Moscow, Moskva, moscow, MOSCOW, "Moskva " (trailing space) etc.

SELECT DISTINCT department_raw FROM employees_raw ORDER BY department_raw;
-- Human Resources, human resources, HR, H.R., İnsan Kaynakları
```

If you see that variation, Day 1 is done — you have a realistic,
reproducible "dirty" enterprise dataset to clean in Day 2.

## What's NOT done yet (by design)

- `employees_clean` table exists but is empty — populated in Day 2
- No LLM/LangChain code yet — starts Day 3
- No FAISS index — starts Day 4
- `salary` is loaded but should never be exposed via NL query later —
  this is intentional, to give you a safety-layer test case in Day 5

## Next: Day 2

Build the cleaning pipeline: normalize casing, fuzzy-match city/dept/role
variants to canonical values (`rapidfuzz` or `Levenshtein`), resolve
`department_raw` → `department_id` foreign key, and write the cleaned
rows into `employees_clean`. Save a handful of before/after examples —
this becomes the "Table I" of your own README once the project is done.
