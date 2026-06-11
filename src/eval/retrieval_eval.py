"""Retrieval eval metrics (Phase 7 / ADR 007)."""

from __future__ import annotations

from typing import Any


def precision_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    """Fraction of top-k retrieved IDs that are relevant."""
    if k <= 0:
        return 0.0
    top = retrieved_ids[:k]
    if not top:
        return 0.0
    hits = sum(1 for item in top if item in relevant_ids)
    return hits / len(top)


def recall_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    """Fraction of relevant IDs found in top-k."""
    if not relevant_ids or k <= 0:
        return 0.0
    top = set(retrieved_ids[:k])
    hits = len(top & relevant_ids)
    return hits / len(relevant_ids)


def reciprocal_rank(retrieved_ids: list[str], relevant_ids: set[str]) -> float:
    """Reciprocal rank of the first relevant hit."""
    for index, item in enumerate(retrieved_ids, start=1):
        if item in relevant_ids:
            return 1.0 / index
    return 0.0


def mean_reciprocal_rank(
    cases: list[tuple[list[str], set[str]]],
) -> float:
    """Mean reciprocal rank across query cases."""
    if not cases:
        return 0.0
    return sum(reciprocal_rank(ids, rel) for ids, rel in cases) / len(cases)


def score_retrieval_case(
    retrieved_ids: list[str],
    relevant_ids: set[str],
    *,
    k_values: tuple[int, ...] = (1, 5, 10),
) -> dict[str, float]:
    """Score one query case at common k values."""
    metrics: dict[str, float] = {"mrr": reciprocal_rank(retrieved_ids, relevant_ids)}
    for k in k_values:
        metrics[f"precision@{k}"] = precision_at_k(retrieved_ids, relevant_ids, k)
        metrics[f"recall@{k}"] = recall_at_k(retrieved_ids, relevant_ids, k)
    return metrics


def evaluate_retrieval_pairs(pairs: list[dict[str, Any]]) -> dict[str, Any]:
    """Evaluate a list of {query, expected_ids, retrieved_ids} records."""
    case_metrics: list[dict[str, float]] = []
    mrr_cases: list[tuple[list[str], set[str]]] = []
    for pair in pairs:
        expected = set(pair.get("expected_ids") or [])
        retrieved = list(pair.get("retrieved_ids") or [])
        case_metrics.append(score_retrieval_case(retrieved, expected))
        mrr_cases.append((retrieved, expected))
    aggregate: dict[str, float] = {"mrr": mean_reciprocal_rank(mrr_cases)}
    if case_metrics:
        for key in case_metrics[0]:
            if key != "mrr":
                aggregate[key] = sum(row[key] for row in case_metrics) / len(case_metrics)
    return {"cases": len(pairs), "metrics": aggregate, "per_case": case_metrics}
