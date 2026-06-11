"""Extraction eval — compare predicted vs expected facts (Phase 7)."""

from __future__ import annotations

from typing import Any


def _normalize_fact(text: str) -> str:
    return " ".join(text.strip().lower().split())


def fact_sets_match(expected: list[str], actual: list[str]) -> dict[str, float]:
    """Token-normalized precision/recall/F1 between fact lists."""
    exp = {_normalize_fact(item) for item in expected if item.strip()}
    act = {_normalize_fact(item) for item in actual if item.strip()}
    if not exp and not act:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0}
    if not exp or not act:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    hits = len(exp & act)
    precision = hits / len(act)
    recall = hits / len(exp)
    f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
    return {"precision": precision, "recall": recall, "f1": f1}


def evaluate_extraction_gold(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Evaluate provider outputs against gold conversations."""
    per_case: list[dict[str, Any]] = []
    for case in cases:
        expected = list(case.get("expected_facts") or [])
        actual = list(case.get("actual_facts") or [])
        scores = fact_sets_match(expected, actual)
        per_case.append(
            {
                "id": case.get("id"),
                "provider": case.get("provider"),
                **scores,
            }
        )
    if not per_case:
        return {"cases": 0, "metrics": {"precision": 0.0, "recall": 0.0, "f1": 0.0}}
    metrics = {
        key: sum(row[key] for row in per_case) / len(per_case)
        for key in ("precision", "recall", "f1")
    }
    return {"cases": len(per_case), "metrics": metrics, "per_case": per_case}


def compare_providers(
    cases_by_provider: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Aggregate extraction metrics per provider label."""
    rows: list[dict[str, Any]] = []
    for provider, cases in sorted(cases_by_provider.items()):
        summary = evaluate_extraction_gold(cases)
        rows.append({"provider": provider, **summary["metrics"], "cases": summary["cases"]})
    return rows
