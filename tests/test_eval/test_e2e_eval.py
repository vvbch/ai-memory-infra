"""Integration test for eval runner over bundled gold data."""

from __future__ import annotations

from pathlib import Path

from eval.reporters import render_markdown_report
from eval.runners import check_thresholds, run_all_suites

_GOLD = Path(__file__).resolve().parents[2] / "src" / "eval" / "gold_standard"


def test_run_all_suites_on_bundled_gold() -> None:
    results = run_all_suites(_GOLD)
    assert results["retrieval"]["cases"] == 2
    assert results["extraction"]["cases"] == 2
    assert results["categorization"]["cases"] == 3
    assert "precision@5" in results["retrieval"]["metrics"]


def test_threshold_check_passes_on_bundled_gold() -> None:
    results = run_all_suites(_GOLD)
    failures = check_thresholds(
        results,
        thresholds={
            "retrieval_precision@5": 0.5,
            "extraction_recall": 0.5,
            "categorization_accuracy": 0.5,
        },
    )
    assert failures == []


def test_adr007_default_thresholds_pass_on_bundled_gold() -> None:
    """Synthetic gold must satisfy the CI eval gate (scripts/run_eval_gate.py)."""
    from eval.runners import DEFAULT_THRESHOLDS

    results = run_all_suites(_GOLD)
    assert check_thresholds(results, DEFAULT_THRESHOLDS) == []


def test_markdown_report_renders_suite_output() -> None:
    results = run_all_suites(_GOLD)
    report = render_markdown_report(results)
    assert "retrieval" in report.lower()
    assert "extraction" in report.lower()
