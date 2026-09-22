# Day 6 — Evaluation Harness

## What this produces

`evaluation/evaluate.py` turns Days 3-5 into concrete numbers instead of
claims. Three measurements:

1. **Query validity, 0-shot vs 5-shot** (`data/eval_set.json`, 15
   questions across 11 categories: simple filters, joins, group-bys,
   subqueries, outer joins) — reuses the Day 4 few-shot toggle for a
   direct before/after comparison, the same shape as the reference
   paper's Table II
2. **Safety layer effectiveness** (`data/adversarial_set.json`, 10
   cases: 8 attacks + 2 legitimate control queries) — measures both the
   attack block rate (want ~100%) AND the false-positive rate on
   legitimate queries (want ~0%). A safety layer that blocks everything
   isn't actually safe, it's just useless — the false-positive check is
   what makes this a real evaluation instead of security theater
3. **Per-category breakdown** — shows where the system is strong/weak
   (e.g. simple filters vs. multi-table joins), which is a more honest
   and more interesting resume story than one aggregate number

## What "query validity" measures here — read this before quoting a number

Validity means the generated SQL passes `validators.py` (parses, correct
statement type, schema-compliant, no blocked columns) **and** executes
without a database error. It does **not** mean the result is
semantically correct — i.e. it doesn't verify the SQL actually answers
the question right, only that it's safe and runs.

Checking semantic correctness requires comparing the generated SQL's
output against `expected_sql`'s output on a live database — the eval set
already carries `expected_sql` for exactly this, but `evaluate.py`
leaves it as a documented, unimplemented `check_semantic_accuracy()`
rather than faking a number. Once you have `DATABASE_URL` set and
`employees_clean` populated, this is a small addition:

```python
gen_cols, gen_rows = run_query(generated_sql)
exp_cols, exp_rows = run_query(expected_sql)
match = sorted(gen_rows) == sorted(exp_rows)
```

Add this yourself once you're running against a real database — it's
flagged as the natural next step, not left out by accident.

## What I actually verified (mechanics, not real numbers)

This sandbox can't reach Groq or a live Postgres instance, so I couldn't
produce real accuracy numbers here. What I did verify: ran the actual
`evaluate.py` functions (`run_query_validity_eval`, `run_safety_eval`,
`summarize_validity`, `summarize_safety`) against a **simulated**
`ask_fn` designed to behave realistically (few-shot succeeding more
often than zero-shot, safety layer correctly blocking all 8 attacks and
allowing both legitimate controls). Confirmed:

- Per-category pass rates compute correctly (11 categories tracked
  independently)
- The safety summary correctly separates attack block rate from
  false-positive rate on controls — both showed 100% correct in the
  simulation
- Failure reporting correctly surfaces which specific questions failed
  and why
- The headline 0-shot vs 5-shot delta calculation is correct arithmetic

The simulated run happened to show 0-shot slightly *beating* 5-shot —
that's just random noise from the fake test function on a small sample,
**not a real result**. Don't use that number for anything; it only
proves the harness computes correctly, not what your actual system will
score.

## Run it for real

```bash
python evaluation/evaluate.py
```

Requires `GROQ_API_KEY` and `DATABASE_URL` set, and `employees_clean`
populated (Days 1-2). Writes full results to `data/eval_results.json`.

## What to do with the real numbers

Once you have real output, this is your resume material:
- "Built a NL2SQL system achieving X% query validity, improved to Y%
  with few-shot retrieval (+Z points)"
- "Safety layer blocked N/N adversarial attempts with zero false
  positives on legitimate queries"
- Per-category breakdown is a strong interview talking point: "simple
  filters hit ~95%, multi-table joins were the weak point at ~70%,
  which is exactly what the paper's own error analysis found too"

## Next: Day 7

Wrap the query engine in a Streamlit UI, deploy it publicly (Streamlit
Community Cloud or HF Spaces), and write the final README pulling
together the architecture diagram, the cleaning pipeline's before/after
table, and this evaluation's headline numbers.
