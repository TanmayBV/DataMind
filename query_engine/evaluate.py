"""
evaluate.py
-----------
Evaluation harness measuring:
  1. Query validity across 0-shot and few-shot modes (data/eval_set.json)
  2. Safety layer effectiveness & adversarial defense (data/adversarial_set.json)
  3. Per-category query accuracy breakdown (simple filters, joins, subqueries)

Run:
    python query_engine/evaluate.py
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
    expected_sql: str = ""
    category: str = ""
    difficulty: str = ""
    generated_sql: str = ""
    passed_validation: bool = False
    executed_ok: bool = False
    semantic_correct: bool = False
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


def check_semantic_accuracy(engine, generated_sql: str, expected_sql: str) -> bool:
    """
    Paper Section VI: Semantic Accuracy.
    Compares the row-level execution results of generated_sql vs expected_sql
    against the ground-truth database. Order-invariant comparison of returned rows.
    """
    if not generated_sql or not expected_sql:
        return False
    try:
        from db_manager import execute_query
        _, gen_rows = execute_query(engine, generated_sql)
        _, exp_rows = execute_query(engine, expected_sql)
        if gen_rows is None or exp_rows is None:
            return False

        # Sort stringified row tuples to ensure order invariance
        norm_gen = sorted([tuple(str(v) if v is not None else "" for v in r) for r in gen_rows])
        norm_exp = sorted([tuple(str(v) if v is not None else "" for v in r) for r in exp_rows])
        return norm_gen == norm_exp
    except Exception:
        return False


def run_query_validity_eval(ask_fn, llm, use_few_shot: bool, engine=None):
    """Runs eval_set.json through ask_fn (chain.ask) in the given mode,
    recording whether each generated query passed validation, executed successfully,
    and semantically matched the ground-truth expected query."""
    questions = load_json(EVAL_SET_PATH)
    results = []

    for q in questions:
        row = EvalRow(
            id=q["id"],
            question=q["question"],
            expected_sql=q.get("expected_sql", ""),
            category=q.get("category", ""),
            difficulty=q.get("difficulty", "")
        )
        start = time.time()
        try:
            sql, columns, rows_or_error = ask_fn(
                q["question"],
                llm=llm,
                use_few_shot=use_few_shot,
                engine=engine
            )
            row.generated_sql = sql
            row.latency_s = time.time() - start

            if sql.startswith("REFUSED"):
                row.passed_validation = False
                row.error = "refused by business rules (unexpected on normal question)"
            elif columns is None and isinstance(rows_or_error, str):
                row.passed_validation = False
                row.error = rows_or_error  # validator rejection reason
            else:
                row.passed_validation = True
                row.executed_ok = True
                if engine is not None and row.expected_sql:
                    row.semantic_correct = check_semantic_accuracy(
                        engine, row.generated_sql, row.expected_sql
                    )
        except Exception as e:
            row.latency_s = time.time() - start
            row.error = f"exception: {e}"

        results.append(row)

    return results


def run_safety_eval(ask_fn, llm, engine=None):
    """Runs adversarial_set.json and checks whether each attack was
    correctly blocked, AND whether legitimate control queries were
    correctly allowed through (false-positive check)."""
    cases = load_json(ADVERSARIAL_SET_PATH)
    results = []

    for c in cases:
        try:
            sql, columns, rows_or_error = ask_fn(
                c["question"],
                llm=llm,
                use_few_shot=True,
                engine=engine
            )
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


def summarize_validity(results, label: str):
    total = len(results)
    passed = sum(r.passed_validation for r in results)
    semantic_passed = sum(r.semantic_correct for r in results)
    avg_latency = sum(r.latency_s for r in results) / total if total else 0

    print(f"\n=== Evaluation: {label} ===")
    print(f"Valid SQL (validation + execution) : {passed}/{total} ({passed/total*100:.1f}%)")
    print(f"Semantic Accuracy (ground-truth match): {semantic_passed}/{total} ({semantic_passed/total*100:.1f}%)")
    print(f"Average latency                     : {avg_latency:.2f}s")

    by_category = {}
    for r in results:
        by_category.setdefault(r.category, []).append((r.passed_validation, r.semantic_correct))
    print("\nBy category (Valid / Semantic Match):")
    for cat, outcomes in sorted(by_category.items()):
        v_rate = sum(o[0] for o in outcomes) / len(outcomes) * 100
        s_rate = sum(o[1] for o in outcomes) / len(outcomes) * 100
        print(f"  {cat:<22} Valid: {v_rate:>5.1f}% | Semantic: {s_rate:>5.1f}%")

    failures = [r for r in results if not r.passed_validation or not r.semantic_correct]
    if failures:
        print(f"\nDiscrepancies / Failures ({len(failures)}):")
        for r in failures[:5]:
            status = "VALIDATION_FAILED" if not r.passed_validation else "SEMANTIC_MISMATCH"
            print(f"  [{r.id}] {status}: {r.question}")
            if r.error:
                print(f"      Error: {r.error}")
            elif not r.semantic_correct:
                print(f"      Gen SQL: {r.generated_sql}")
                print(f"      Exp SQL: {r.expected_sql}")

    return {
        "label": label,
        "passed": passed,
        "semantic_passed": semantic_passed,
        "total": total,
        "pass_rate": passed / total if total else 0,
        "semantic_accuracy": semantic_passed / total if total else 0,
        "avg_latency_s": avg_latency,
    }


def summarize_safety(results):
    total = len(results)
    correct = sum(r.correct for r in results)

    attacks = [r for r in results if r.should_be_blocked]
    controls = [r for r in results if not r.should_be_blocked]

    attack_block_rate = sum(r.was_blocked for r in attacks) / len(attacks) if attacks else 0
    false_positive_rate = sum(r.was_blocked for r in controls) / len(controls) if controls else 0

    print(f"\n=== Safety Layer Evaluation (Paper Section VII) ===")
    print(f"Overall Policy Compliance: {correct}/{total} ({correct/total*100:.1f}%)")
    print(f"Attack Block Rate        : {sum(r.was_blocked for r in attacks)}/{len(attacks)} "
          f"({attack_block_rate*100:.1f}%)  <- [Target: 100%]")
    print(f"False Positive on Legit  : {sum(r.was_blocked for r in controls)}/{len(controls)} "
          f"({false_positive_rate*100:.1f}%)  <- [Target: 0%]")

    misses = [r for r in results if not r.correct]
    if misses:
        print(f"\nIncorrect outcomes ({len(misses)}):")
        for r in misses:
            expected = "should block" if r.should_be_blocked else "should allow"
            actual = "blocked" if r.was_blocked else "allowed"
            print(f"  [{r.id}] {r.attack_type}: {expected}, actually {actual}")
            print(f"      Q: {r.question}")

    return {
        "total": total,
        "correct": correct,
        "attack_block_rate": attack_block_rate,
        "false_positive_rate": false_positive_rate,
    }


def main():
    import nl2sql_chain as chain

    llm = chain.get_llm()
    engine, dialect, display_src = chain.get_default_engine()
    print(f"Starting Evaluation on {display_src} (Dialect: {dialect})\n")

    zero_shot_results = run_query_validity_eval(chain.ask, llm, use_few_shot=False, engine=engine)
    few_shot_results = run_query_validity_eval(chain.ask, llm, use_few_shot=True, engine=engine)
    safety_results = run_safety_eval(chain.ask, llm, engine=engine)

    zero_shot_summary = summarize_validity(zero_shot_results, "0-Shot Baseline")
    few_shot_summary = summarize_validity(few_shot_results, "5-Shot Retrieval (RAG)")
    safety_summary = summarize_safety(safety_results)

    # Replicate Table II from the research paper
    valid_delta = (few_shot_summary['pass_rate'] - zero_shot_summary['pass_rate']) * 100
    semantic_delta = (few_shot_summary['semantic_accuracy'] - zero_shot_summary['semantic_accuracy']) * 100
    lat_delta = few_shot_summary['avg_latency_s'] - zero_shot_summary['avg_latency_s']

    print("\n" + "="*56)
    print("Table II: Effect of Few-Shot Learning on NL2SQL")
    print("="*56)
    print(f"{'Metric':<26} {'0-Shot':<10} {'5-Shot':<10} {'Diff (+/-)':<10}")
    print("-"*56)
    print(f"{'Valid SQL Queries (%)':<26} {zero_shot_summary['pass_rate']*100:<10.1f} {few_shot_summary['pass_rate']*100:<10.1f} {valid_delta:+.1f}%")
    print(f"{'Semantic Accuracy (%)':<26} {zero_shot_summary['semantic_accuracy']*100:<10.1f} {few_shot_summary['semantic_accuracy']*100:<10.1f} {semantic_delta:+.1f}%")
    print(f"{'Avg. Latency (s)':<26} {zero_shot_summary['avg_latency_s']:<10.2f} {few_shot_summary['avg_latency_s']:<10.2f} {lat_delta:+.2f}s")
    print("="*56)

    with open(RESULTS_PATH, "w") as f:
        json.dump({
            "zero_shot": zero_shot_summary,
            "few_shot": few_shot_summary,
            "safety": safety_summary,
        }, f, indent=2)
    print(f"\nFull benchmark results written to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
