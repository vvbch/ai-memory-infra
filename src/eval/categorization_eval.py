"""Categorization eval using migration categorizer (Phase 7)."""

from __future__ import annotations

from typing import Any

from migration.categorizer import infer_ventures


def score_categorization_case(
    *,
    source_path: str,
    text: str,
    expected_ventures: list[str],
) -> dict[str, Any]:
    """Return whether predicted ventures match expected (order-insensitive)."""
    predicted = infer_ventures(source_path=source_path, text=text)
    expected = sorted(expected_ventures)
    return {
        "source_path": source_path,
        "expected": expected,
        "predicted": predicted,
        "correct": predicted == expected,
    }


def evaluate_categorization_gold(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Measure exact-match accuracy over gold categorization cases."""
    per_case = [
        score_categorization_case(
            source_path=str(case.get("source_path") or ""),
            text=str(case.get("text") or ""),
            expected_ventures=list(case.get("expected_ventures") or []),
        )
        for case in cases
    ]
    correct = sum(1 for row in per_case if row["correct"])
    total = len(per_case)
    accuracy = correct / total if total else 0.0
    return {
        "cases": total,
        "metrics": {"accuracy": accuracy, "correct": correct},
        "per_case": per_case,
    }
