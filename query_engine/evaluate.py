"""
evaluate.py
-----------
Day 6: evaluation harness. Turns everything built in Days 3-5 into
concrete, measurable numbers — this is what produces your resume's
headline metrics, not just claims.

Three measurements:

  1. Query validity, 0-shot vs 5-shot (data/eval_set.json)
     -- reuses the few-shot toggle built in Day 4 to produce a direct
        before/after comparison, same shape as the reference paper's
        Table II (0-Shot vs 5-Shot query validity)

  2. Safety layer effectiveness (data/adversarial_set.json)
     -- measures block rate on attack attempts (should all be blocked)
        AND false-positive rate on legitimate control queries (should
        NOT be blocked) — both numbers matter; a safety layer that
        blocks everything isn't useful, it just LOOKS safe

  3. Per-category breakdown (simple filters vs joins vs subqueries)
     -- shows WHERE the system is strong/weak, which is a more honest
        and more interesting story than a single aggregate accuracy
        number

IMPORTANT — read this before running against a real LLM:
"Query validity" here means the generated SQL passes validators.py
(parses, correct statement type, schema-compliant, no blocked columns)
AND executes without a database error. It does NOT mean the RESULT is
semantically correct (i.e. actually answers the question correctly) —
verifying that would require either a human check against expected_sql,
or running both the generated and expected_sql against a live database
and comparing row-for-row output. This harness measures and reports
validity/safety, and leaves a clear TODO + instructions for you to add
semantic accuracy checking once you have a live database to test against
(see check_semantic_accuracy() below).

Run:
    python evaluation/evaluate.py
"""

import json
import os
import sys
import time
from dataclasses import dataclass, field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "config"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "query_engine"))
from config import DATA_DIR

EVAL_SET_PATH = os.path.join(DATA_DIR, "eval_set.json")
ADVERSARIAL_SET_PATH = os.path.join(DATA_DIR, "adversarial_set.json")
RESULTS_PATH = os.path.join(DATA_DIR, "eval_results.json")


@dataclass
class EvalRow:
    id: str
    question: str
    category: str = ""
    difficulty: str = ""
    generated_sql: str = ""
    passed_validation: bool = False
    executed_ok: bool = False
    error: str = ""
    latency_s: float = 0.0


@dataclass
class AdversarialRow:
    id: str
    question: str
    attack_type: str
    should_be_blocked: bool
    was_blocked: bool
    correct: bool = False
    generated_sql: str = ""


def load_json(path):
    with open(path) as f:
        return json.load(f)


def run_query_validity_eval(ask_fn, llm, use_few_shot: bool):
    """Runs eval_set.json through ask_fn (chain.ask) in the given mode,
    recording whether each generated query passed validation and
    executed successfully. This is the "0-shot vs 5-shot" comparison."""
    questions = load_json(EVAL_SET_PATH)
    results = []

    for q in questions:
        row = EvalRow(id=q["id"], question=q["question"],
                       category=q.get("category", ""), difficulty=q.get("difficulty", ""))
        start = time.time()
        try:
            sql, columns, rows_or_error = ask_fn(q["question"], llm=llm, use_few_shot=use_few_shot)
            row.generated_sql = sql
            row.latency_s = time.time() - start

            if sql.startswith("REFUSED"):
                row.passed_validation = False
                row.error = "refused by business rules (unexpected on a normal eval question)"
            elif columns is None and isinstance(rows_or_error, str):
                row.passed_validation = False
                row.error = rows_or_error  # validator rejection reason
            else:
                row.passed_validation = True
                row.executed_ok = True
        except Exception as e:
            row.latency_s = time.time() - start
            row.error = f"exception: {e}"

        results.append(row)

    return results


def run_safety_eval(ask_fn, llm):
    """Runs adversarial_set.json and checks whether each attack was
    correctly blocked, AND whether legitimate control queries were
    correctly allowed through (false-positive check)."""
    cases = load_json(ADVERSARIAL_SET_PATH)
    results = []

    for c in cases:
        try:
            sql, columns, rows_or_error = ask_fn(c["question"], llm=llm, use_few_shot=True)
        except Exception as e:
            sql, columns, rows_or_error = "", None, f"exception: {e}"

        was_blocked = sql.startswith("REFUSED") or (columns is None and isinstance(rows_or_error, str))
        correct = was_blocked == c["should_be_blocked"]

        results.append(AdversarialRow(
            id=c["id"], question=c["question"], attack_type=c["attack_type"],
            should_be_blocked=c["should_be_blocked"], was_blocked=was_blocked,
            correct=correct, generated_sql=sql,
        ))

    return results


def check_semantic_accuracy():
    """
    TODO (not implemented — needs a live database):
    To measure whether generated SQL actually answers the question
    correctly (not just validly), execute both the generated SQL and
    the eval set's expected_sql against your loaded Postgres instance
    and compare the returned rows. A simple approach:

        gen_cols, gen_rows = run_query(generated_sql)
        exp_cols, exp_rows = run_query(expected_sql)
        match = sorted(gen_rows) == sorted(exp_rows)

    This requires DATABASE_URL to be set and employees_clean populated
    (Days 1-2). Left as a clearly-marked next step rather than faked,
    since fabricating this number would be dishonest.
    """
    raise NotImplementedError(
        "Semantic accuracy checking requires a live database connection. "
        "See the docstring above for how to implement it once you have one."
    )


def summarize_validity(results, label: str):
    total = len(results)
    passed = sum(r.passed_validation for r in results)
    avg_latency = sum(r.latency_s for r in results) / total if total else 0

    print(f"\n=== Query Validity — {label} ===")
    print(f"Passed validation + executed: {passed}/{total} ({passed/total*100:.1f}%)")
    print(f"Average latency: {avg_latency:.2f}s")

    by_category = {}
    for r in results:
        by_category.setdefault(r.category, []).append(r.passed_validation)
    print("\nBy category:")
    for cat, outcomes in sorted(by_category.items()):
        rate = sum(outcomes) / len(outcomes) * 100
        print(f"  {cat:<20} {sum(outcomes)}/{len(outcomes)}  ({rate:.0f}%)")

    failures = [r for r in results if not r.passed_validation]
    if failures:
        print(f"\nFailures ({len(failures)}):")
        for r in failures:
            print(f"  [{r.id}] {r.question}")
            print(f"      -> {r.error}")

    return {"label": label, "passed": passed, "total": total,
            "pass_rate": passed / total if total else 0, "avg_latency_s": avg_latency}


def summarize_safety(results):
    total = len(results)
    correct = sum(r.correct for r in results)

    attacks = [r for r in results if r.should_be_blocked]
    controls = [r for r in results if not r.should_be_blocked]

    attack_block_rate = sum(r.was_blocked for r in attacks) / len(attacks) if attacks else 0
    false_positive_rate = sum(r.was_blocked for r in controls) / len(controls) if controls else 0

    print(f"\n=== Safety Layer Evaluation ===")
    print(f"Overall correct: {correct}/{total} ({correct/total*100:.1f}%)")
    print(f"Attack block rate: {sum(r.was_blocked for r in attacks)}/{len(attacks)} "
          f"({attack_block_rate*100:.1f}%)  <- want this near 100%")
    print(f"False positive rate on legit queries: {sum(r.was_blocked for r in controls)}/{len(controls)} "
          f"({false_positive_rate*100:.1f}%)  <- want this near 0%")

    misses = [r for r in results if not r.correct]
    if misses:
        print(f"\nIncorrect outcomes ({len(misses)}):")
        for r in misses:
            expected = "should block" if r.should_be_blocked else "should allow"
            actual = "blocked" if r.was_blocked else "allowed"
            print(f"  [{r.id}] {r.attack_type}: {expected}, actually {actual}")
            print(f"      Q: {r.question}")

    return {"total": total, "correct": correct,
            "attack_block_rate": attack_block_rate,
            "false_positive_rate": false_positive_rate}


def main():
    # Imported here (not at module level) so this file can be inspected/
    # tested without requiring a Groq API key or database connection.
    import nl2sql_chain as chain

    llm = chain.get_llm()

    zero_shot_results = run_query_validity_eval(chain.ask, llm, use_few_shot=False)
    few_shot_results = run_query_validity_eval(chain.ask, llm, use_few_shot=True)
    safety_results = run_safety_eval(chain.ask, llm)

    zero_shot_summary = summarize_validity(zero_shot_results, "0-shot (Day 3 baseline)")
    few_shot_summary = summarize_validity(few_shot_results, "5-shot (Day 4 retrieval)")
    safety_summary = summarize_safety(safety_results)

    print(f"\n=== Headline comparison ===")
    print(f"0-shot query validity: {zero_shot_summary['pass_rate']*100:.1f}%")
    print(f"5-shot query validity: {few_shot_summary['pass_rate']*100:.1f}%")
    delta = (few_shot_summary['pass_rate'] - zero_shot_summary['pass_rate']) * 100
    print(f"Improvement from few-shot retrieval: {delta:+.1f} points")

    with open(RESULTS_PATH, "w") as f:
        json.dump({
            "zero_shot": zero_shot_summary,
            "few_shot": few_shot_summary,
            "safety": safety_summary,
        }, f, indent=2)
    print(f"\nFull results written to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
