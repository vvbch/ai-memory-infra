"""Eval orchestrator (Phase 7)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from eval.categorization_eval import evaluate_categorization_gold
from eval.extraction_eval import evaluate_extraction_gold
from eval.retrieval_eval import evaluate_retrieval_pairs

DEFAULT_THRESHOLDS = {
    "retrieval_precision@5": 0.7,
    "extraction_recall": 0.8,
    "categorization_accuracy": 0.8,
}


def _load_json(path: Path) -> Any:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return data.get("cases") or data.get("pairs") or []
    return data


def run_all_suites(
    gold_dir: Path,
    *,
    retrieval_results: list[dict[str, Any]] | None = None,
    extraction_results: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run retrieval, extraction, and categorization evals from gold data."""
    pairs = _load_json(gold_dir / "retrieval_pairs.json")
    if retrieval_results is not None:
        for index, pair in enumerate(pairs):
            if index < len(retrieval_results):
                pair = dict(pair)
                pair["retrieved_ids"] = retrieval_results[index].get("retrieved_ids", [])
                pairs[index] = pair

    extraction_cases = _load_json(gold_dir / "extraction_gold.json")
    if extraction_results is not None:
        extraction_cases = extraction_results

    categorization_cases = _load_json(gold_dir / "categorization_gold.json")

    return {
        "retrieval": evaluate_retrieval_pairs(list(pairs)),
        "extraction": evaluate_extraction_gold(list(extraction_cases)),
        "categorization": evaluate_categorization_gold(list(categorization_cases)),
    }


def check_thresholds(
    results: dict[str, Any],
    thresholds: dict[str, float] | None = None,
) -> list[str]:
    """Return list of threshold violations (empty == pass)."""
    limits = thresholds or DEFAULT_THRESHOLDS
    failures: list[str] = []

    retrieval = results.get("retrieval", {}).get("metrics", {})
    if retrieval.get("precision@5", 0.0) < limits["retrieval_precision@5"]:
        failures.append("retrieval precision@5 below threshold")

    extraction = results.get("extraction", {}).get("metrics", {})
    if extraction.get("recall", 0.0) < limits["extraction_recall"]:
        failures.append("extraction recall below threshold")

    categorization = results.get("categorization", {}).get("metrics", {})
    if categorization.get("accuracy", 0.0) < limits["categorization_accuracy"]:
        failures.append("categorization accuracy below threshold")

    return failures
