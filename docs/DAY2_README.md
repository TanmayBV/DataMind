# NL2SQL RAG Project — Day 2: Data Cleaning Pipeline

## What this does

`scripts/clean_data.py` transforms `employees_raw.csv` (messy, decentralized-entry-style
data from Day 1) into `employees_clean.csv`, using a two-pass entity resolution
approach:

1. **Normalization** — trim whitespace, collapse casing differences
2. **Alias lookup (exact match)** — a curated table resolves abbreviations that
   fuzzy matching structurally cannot (`"HR"` → `"Human Resources"` share almost
   no characters, so string-similarity alone fails here — this is a real
   limitation worth knowing, not a bug)
3. **Fuzzy fallback (`rapidfuzz`)** — catches typos, casing, and minor spelling
   variants that aren't in the alias table
4. **Validation** — rows where a field can't be resolved by either pass are
   **flagged for manual review**, not silently guessed. This mirrors the
   reference paper's approach: wrong-but-confident guesses are worse than an
   honest "couldn't resolve this."

## Run it

```bash
python scripts/clean_data.py
```

Outputs (in `data/`):
- `employees_clean.csv` — successfully resolved records, ready to load into
  `employees_clean` table (see `sql/schema.sql`)
- `flagged_records.csv` — records that failed resolution, with an `issues`
  column stating exactly why (`unresolved_city`, `invalid_status`, etc.)
- `before_after_examples.csv` — 15 sample transformations, with the `method`
  column showing whether it was resolved via `alias`, `exact_ci`, or `fuzzy`
  matching — this is your **Table I equivalent** for the final README
- `project_assignments_clean.csv` — project assignments with unresolved
  project names dropped

## This run's results

```
Total raw employee records : 3,000
Successfully cleaned       : 2,655 (88.5%)
Flagged for manual review  : 345 (11.5%)
Project assignments dropped: 329 (unresolved project names)
```

Note: this is deliberately **not** 100%. Day 1's generator injects ~4% per-field
noise (`"N/A"`, `"???"`, `"TBD"`, empty strings) that no reasonable alias table
or fuzzy match should resolve — a pipeline that "cleans" 100% of intentionally
garbage data is a red flag, not a win. Having a real, non-zero flagged-records
count is a stronger story for your README than a suspiciously perfect number.

## Key design decision worth mentioning in interviews

Fuzzy matching alone (`rapidfuzz` against a canonical list) initially resolved
only ~13% of records, because abbreviations like `"HR"`, `"PM"`, `"IT"` don't
share enough characters with their expansions to score above any reasonable
similarity threshold. Adding a curated **alias table as a first pass**, with
fuzzy matching as a fallback for typos/casing, brought resolution up to 88.5%.
This mirrors the reference paper's point that generative/fuzzy techniques alone
can't substitute for explicit encoded business logic — you need both.

## Next: Day 3

Set up LangChain with Groq or Gemini Flash (free tier) and build the baseline
zero-shot NL2SQL chain against `employees_clean`, `departments`, `projects`,
and `project_assignments`. Get a simple question → SQL → execute → result loop
working before adding retrieval (Day 4).
