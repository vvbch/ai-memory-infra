"""Unit tests for retrieval eval metrics."""

from __future__ import annotations

from eval.retrieval_eval import (
    evaluate_retrieval_pairs,
    mean_reciprocal_rank,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)


def test_precision_at_k() -> None:
    assert precision_at_k(["a", "b", "c"], {"a", "c"}, 3) == 2 / 3


def test_recall_at_k() -> None:
    assert recall_at_k(["a", "x"], {"a", "b"}, 5) == 0.5


def test_reciprocal_rank_and_mrr() -> None:
    assert reciprocal_rank(["x", "hit", "y"], {"hit"}) == 0.5
    mrr = mean_reciprocal_rank([(["miss", "a"], {"a"}), (["b"], {"b"})])
    assert round(mrr, 3) == round((0.5 + 1.0) / 2, 3)


def test_evaluate_retrieval_pairs_aggregate() -> None:
    result = evaluate_retrieval_pairs(
        [
            {"expected_ids": ["a"], "retrieved_ids": ["a", "b"]},
            {"expected_ids": ["c"], "retrieved_ids": ["c"]},
        ]
    )
    assert result["cases"] == 2
    assert result["metrics"]["precision@1"] == 1.0
