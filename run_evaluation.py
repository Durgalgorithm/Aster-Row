#!/usr/bin/env python3
"""
CLI entry point to run the Aster & Row Support Agent Evaluation Suite.
Usage:
    python3 run_evaluation.py
"""

import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.evaluation.evaluator import EvaluationRunner

def main():
    print("=" * 70)
    print("  ASTER & ROW AI SUPPORT AGENT - EVALUATION SUITE")
    print("=" * 70)

    runner = EvaluationRunner(cases_file="evaluation/visible-cases.json")
    try:
        report = runner.run_all()
    except Exception as e:
        print(f"Error running evaluation: {e}")
        sys.exit(1)

    print(f"\nExecuted {report['total_cases']} cases in {report['duration_seconds']}s.")
    print("-" * 70)
    print(f"{'CASE ID':<40} | {'CATEGORY':<15} | {'RESULT':<8}")
    print("-" * 70)

    for case in report["case_results"]:
        status = "PASSED" if case["passed"] else "FAILED"
        print(f"{case['case_id']:<40} | {case['category']:<15} | {status:<8}")
        if not case["passed"]:
            for reason in case["failure_reasons"]:
                print(f"   └── [ASSERTION ERROR] {reason}")

    print("=" * 70)
    print("CATEGORY BREAKDOWN:")
    print("-" * 70)
    for cat, stats in report["category_stats"].items():
        pass_rate = round((stats["passed"] / stats["total"]) * 100, 1) if stats["total"] > 0 else 0
        print(f"  • {cat:<24}: {stats['passed']}/{stats['total']} passed ({pass_rate}%)")

    print("-" * 70)
    print(f"OVERALL SCORE: {report['total_passed']}/{report['total_cases']} PASSED ({report['overall_accuracy']}%)")
    print("=" * 70)

    if report["overall_accuracy"] < 100.0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
