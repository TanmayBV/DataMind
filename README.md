# NL2SQL RAG — Enterprise Data Governance Project

A free-tier, scaled-down implementation of RAG-driven natural-language-to-SQL
querying over a deliberately messy synthetic HR dataset — inspired by
production patterns from enterprise data governance research (data cleaning
pipeline → schema-constrained few-shot RAG → safety-validated SQL generation).

## Project structure

```
nl2sql-rag/
├── .env.example         # template for secrets — copy to .env, never commit .env
├── .gitignore
├── requirements.txt
├── README.md             # you are here
│
├── config/
│   ├── __init__.py
│   └── config.py         # all settings in one place: DB URL, thresholds,
│                          # API keys, paths — every script imports from here
│
├── sql/
│   └── schema.sql         # employees_raw / employees_clean / departments /
│                          # projects / project_assignments table definitions
│
├── scripts/
│   ├── generate_data.py    # Day 1 — synthetic messy dataset generator
│   ├── load_to_postgres.py # Day 1 — loads schema + raw data into Supabase/Neon
│   ├── clean_data.py       # Day 2 — cleaning pipeline (alias + fuzzy match + validation)
│   │
│   │   -- add these as you progress through the build plan --
│   ├── nl2sql_chain.py     # Day 3 — baseline LangChain + Groq/Gemini NL2SQL chain
│   ├── build_faiss_index.py# Day 4 — embeds + indexes few-shot examples
│   ├── validators.py       # Day 5 — schema whitelist + safety rule checks
│   ├── evaluate.py         # Day 6 — ablation study / accuracy metrics
│   └── app.py               # Day 7 — Streamlit front-end
│
├── data/
│   ├── employees_raw.csv            # intentionally messy (Day 1 output)
│   ├── employees_clean.csv          # cleaned + validated (Day 2 output)
│   ├── flagged_records.csv          # records needing manual review
│   ├── before_after_examples.csv    # sample transformations — your README table
│   ├── departments.csv / projects.csv / project_assignments_*.csv
│   │
│   │   -- added later --
│   ├── few_shot_examples.jsonl      # Day 4 — curated question→SQL pairs
│   └── eval_set.jsonl               # Day 6 — ground-truth eval questions
│
└── docs/
    ├── DAY1_README.md       # detailed notes per day, kept as build history
    └── DAY2_README.md
```

## Why it's organized this way

- **`config/` centralizes settings** — as you add Groq, FAISS, and Streamlit in
  later days, every new script pulls from the same place instead of
  re-reading environment variables everywhere. Change a threshold once, it
  applies everywhere.
- **`scripts/` is one file per pipeline stage** — makes it obvious which file
  to open for which part of the system, and lets you re-run any single stage
  independently (e.g. re-clean data without regenerating it).
- **`data/` separates raw from clean from derived** — you always have the
  original messy source available to re-process if you improve the cleaning
  logic later.
- **`docs/` keeps a build log** — when you write your final portfolio README,
  you'll want the "before" story (what broke, what you fixed) as much as the
  "after" result. Keeping day-by-day notes now saves you from having to
  reconstruct that story later.

## Setup

```bash
git clone <your-repo-url>
cd nl2sql-rag
pip install -r requirements.txt --break-system-packages

cp .env.example .env
# edit .env: add your DATABASE_URL from Supabase or Neon

export $(cat .env | xargs)   # or use python-dotenv / direnv
```

## Run the pipeline so far (Days 1-2)

```bash
# 1. Generate synthetic messy data
python scripts/generate_data.py --n_employees 3000

# 2. Load schema + raw data into your free Postgres
python scripts/load_to_postgres.py

# 3. Clean the data
python scripts/clean_data.py
```

Expected output: ~88% of records cleaned successfully, ~12% flagged for
review (this is realistic — the generator injects genuinely unresolvable
noise on purpose, see `docs/DAY2_README.md` for why).

## Current status

- [x] Day 1 — messy synthetic dataset + Postgres schema
- [x] Day 2 — cleaning pipeline (alias table + fuzzy match + validation)
- [ ] Day 3 — baseline LangChain NL2SQL chain
- [ ] Day 4 — FAISS few-shot retrieval
- [ ] Day 5 — validation & safety layer
- [ ] Day 6 — evaluation / ablation study
- [ ] Day 7 — deployment + writeup

## Maintaining this project going forward

- Every new pipeline stage gets its own file in `scripts/` — don't grow
  `clean_data.py` or `generate_data.py` into a monolith.
- Any new setting (API key, threshold, model name) goes in `config/config.py`,
  not hardcoded in a script.
- Keep a `docs/DAYx_README.md` for each stage — this becomes the backbone of
  your final portfolio writeup and your LinkedIn build-in-public posts.
- Before moving to the next day, re-run the previous day's script to confirm
  nothing broke — each stage depends on the last (Day 3 depends on
  `employees_clean` existing, Day 4 depends on the NL2SQL chain running, etc.)
