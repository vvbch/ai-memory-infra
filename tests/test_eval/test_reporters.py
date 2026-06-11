"""Unit tests for eval reporters."""

from __future__ import annotations

import json

from eval.reporters import render_json_report, render_markdown_report


def test_render_markdown_report_lists_metrics() -> None:
    text = render_markdown_report(
        {
            "retrieval": {"cases": 2, "metrics": {"precision@5": 0.8, "mrr": 0.75}},
        }
    )
    assert "# Eval report" in text
    assert "precision@5" in text
    assert "0.800" in text


def test_render_json_report_is_valid_json() -> None:
    payload = {"retrieval": {"cases": 1, "metrics": {"mrr": 1.0}}}
    text = render_json_report(payload)
    assert json.loads(text) == payload
