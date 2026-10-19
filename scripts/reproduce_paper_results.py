"""
reproduce_paper_results.py
--------------------------
Automated replication script for the research paper:
"RAG-Driven Data Quality Governance for Enterprise ERP Systems"
(Sedat Bin Vedat et al., Hagia Labs, arXiv:2511.16700)

Replicates:
1. Table I: Examples of Record Normalization (Data Cleaning Pipeline)
2. Table II: Effect of Few-Shot Learning on NL2SQL Performance (0-Shot vs 5-Shot)
3. Safety Evaluation (Section VII): Attack block rate & false positive rate on legitimate controls
"""

import os
import sys
import json
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "config"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "query_engine"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data_pipeline"))

from config import DATA_DIR
import nl2sql_chain as chain
import evaluate


def print_table_1():
    """Table I: Examples of Record Normalization from the Cleaning Pipeline."""
    before_after_path = os.path.join(DATA_DIR, "before_after_examples.csv")
    print("\n" + "="*70)
    print("Table I: Examples of Record Normalization (Data Cleaning Pipeline)")
    print("="*70)
    if os.path.exists(before_after_path):
        df = pd.read_csv(before_after_path)
        sample = df.head(8)
        print(f"{'Field':<15} {'Raw Input':<22} {'Normalized Output':<25} {'Method':<10}")
        print("-" * 72)
        for _, r in sample.iterrows():
            print(f"{r['field']:<15} {str(r['raw']):<22} {str(r['cleaned']):<25} {r['method']:<10}")
    else:
        print("Run `python data_pipeline/clean_data.py` first to generate before_after_examples.csv")
    print("="*70)


def print_table_2_and_safety():
    """Table II & Safety Evaluation: Replicating Section V & VI of the paper."""
    print("\nRunning live evaluation across 0-Shot vs 5-Shot and Adversarial Sets...")
    evaluate.main()


def main():
    print("="*70)
    print("  RAG-Driven Data Quality Governance for Enterprise ERP Systems")
    print("               Paper Results Replication Benchmark             ")
    print("="*70)
    
    # 1. Table I: Data Cleaning
    print_table_1()

    # 2. Table II: Evaluation & Safety
    print_table_2_and_safety()


if __name__ == "__main__":
    main()
