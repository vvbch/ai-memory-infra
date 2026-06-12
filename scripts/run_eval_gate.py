#!/usr/bin/env python3
"""Deterministic eval regression gate (ADR 007 / Phase 9).

Runs retrieval, extraction, and categorization suites against bundled synthetic
gold data and fails when metrics drop below ADR 007 thresholds. No live Mem0
stack required — this is the fast CI gate; live-stack eval is a follow-up.

Wired into ``.github/workflows/ci.yml`` (every push/PR) and
``.github/workflows/eval-suite.yml`` (weekly + workflow_dispatch).

CROSS-PLATFORM (tenet 3): pure Python; ``pip install -e .`` suffices.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from eval.reporters import render_json_report, render_markdown_report
from eval.runners import DEFAULT_THRESHOLDS, check_thresholds, run_all_suites


def _default_gold_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "src" / "eval" / "gold_standard"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run eval suites and enforce ADR 007 thresholds.")
    parser.add_argument(
        "--gold-dir",
        type=Path,
        default=_default_gold_dir(),
        help="Directory with retrieval_pairs.json, extraction_gold.json, categorization_gold.json",
    )
    parser.add_argument(
        "--report-md",
        type=Path,
        metavar="PATH",
        help="Write Markdown summary (for GitHub Actions step summary)",
    )
    parser.add_argument(
        "--report-json",
        type=Path,
        metavar="PATH",
        help="Write machine-readable JSON results artifact",
    )
    args = parser.parse_args(argv)

    results = run_all_suites(args.gold_dir)
    failures = check_thresholds(results, DEFAULT_THRESHOLDS)

    if args.report_md:
        args.report_md.write_text(render_markdown_report(results), encoding="utf-8")
    if args.report_json:
        args.report_json.write_text(render_json_report(results), encoding="utf-8")

    if failures:
        print("eval gate FAILED:", file=sys.stderr)
        for item in failures:
            print(f"  - {item}", file=sys.stderr)
        print(json.dumps(results["retrieval"]["metrics"], indent=2), file=sys.stderr)
        return 1

    print("eval gate PASSED (synthetic gold, ADR 007 thresholds)")
    for suite, payload in results.items():
        metrics = payload.get("metrics") or {}
        print(f"  {suite}: {metrics}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
