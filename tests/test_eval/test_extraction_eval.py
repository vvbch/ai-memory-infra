"""Unit tests for extraction eval."""

from __future__ import annotations

from eval.extraction_eval import compare_providers, evaluate_extraction_gold, fact_sets_match


def test_fact_sets_match_perfect() -> None:
    scores = fact_sets_match(["Alpha", "Beta"], ["beta", "alpha"])
    assert scores["f1"] == 1.0


def test_fact_sets_match_partial() -> None:
    scores = fact_sets_match(["Alpha", "Beta"], ["Alpha", "Gamma"])
    assert scores["precision"] == 0.5
    assert scores["recall"] == 0.5


def test_evaluate_extraction_gold() -> None:
    result = evaluate_extraction_gold(
        [
            {
                "id": "1",
                "expected_facts": ["fact a"],
                "actual_facts": ["fact a"],
            }
        ]
    )
    assert result["metrics"]["recall"] == 1.0


def test_compare_providers() -> None:
    rows = compare_providers(
        {
            "gpt": [{"expected_facts": ["a"], "actual_facts": ["a"]}],
            "other": [{"expected_facts": ["a"], "actual_facts": []}],
        }
    )
    assert rows[0]["provider"] == "gpt"
    assert rows[0]["recall"] == 1.0
    assert rows[1]["recall"] == 0.0
