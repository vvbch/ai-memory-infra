#!/usr/bin/env python3
"""5-fact acceptance probe for the memory write/read/metadata contract (ADR 037).

Writes throwaway facts through the real bulk importer path, runs three contract
queries, deletes probe facts, and prints pass/fail per query.

Usage::

    python scripts/acceptance_probe.py
    python scripts/acceptance_probe.py --json
    python scripts/acceptance_probe.py --dry-run
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
from typing import Any

import httpx

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(os.path.dirname(_SCRIPT_DIR), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)
if _SCRIPT_DIR in sys.path:
    sys.path.remove(_SCRIPT_DIR)

from memory.retrieval import (  # noqa: E402
    best_entity_match,
    latest_by_event_date,
    open_follow_ups,
    record_id,
    record_text,
    search_with_contract,
)
from mcp_proxy.client import MemoryApiClient, MemoryApiConfig  # noqa: E402
from mcp_proxy.idempotent_write import list_all_memories, write_timeout_seconds  # noqa: E402

# Import bulk importer after path bootstrap.
import importlib.util
from pathlib import Path

_IMPORTER = Path(__file__).resolve().parent / "bulk_seed_importer.py"
_spec = importlib.util.spec_from_file_location("bulk_seed_importer", _IMPORTER)
assert _spec and _spec.loader
_bulk = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bulk)
import_facts = _bulk.import_facts

PROBE_PREFIX = "probe:acceptance:"
PROBE_OPEN_ID = f"{PROBE_PREFIX}open-item"
PROBE_JORDAN_SIBLING_ID = f"{PROBE_PREFIX}jordan-sibling"
PROBE_JORDAN_CONTACT_ID = f"{PROBE_PREFIX}jordan-contact"


def _client(user_id: str | None) -> MemoryApiClient:
    config = MemoryApiConfig.from_env()
    if user_id:
        config = MemoryApiConfig(
            base_url=config.base_url, api_key=config.api_key, user_id=user_id
        )
    timeout = httpx.Timeout(write_timeout_seconds(), connect=10.0)
    return MemoryApiClient(config, http_client=httpx.Client(timeout=timeout))


def probe_facts(*, today: str) -> list[dict[str, Any]]:
    """Five probe facts — write order matters for backdated-recency test."""
    common = {"source": "manual", "namespace": "public"}
    return [
        {
            "external_id": f"{PROBE_PREFIX}alpha-impl",
            "text": "Project Alpha status: implementation started",
            "metadata": {**common, "type": "fact", "event_date": "2026-06-10"},
            "infer": False,
        },
        {
            "external_id": f"{PROBE_PREFIX}alpha-cancel",
            "text": "Project Alpha status: cancelled",
            "metadata": {**common, "type": "fact", "event_date": "2026-05-15"},
            "infer": False,
        },
        {
            "external_id": f"{PROBE_PREFIX}alpha-plan",
            "text": "Project Alpha status: planning phase",
            "metadata": {**common, "type": "fact", "event_date": "2026-06-01"},
            "infer": False,
        },
        {
            "external_id": PROBE_OPEN_ID,
            "text": (
                "Follow up with Jordan, project contact, about system design mock"
            ),
            "metadata": {
                **common,
                "type": "open_item",
                "status": "open",
                "event_date": today,
            },
            "infer": False,
        },
        {
            "external_id": PROBE_JORDAN_SIBLING_ID,
            "text": "Jordan, team lead's sibling, started summer coding camp",
            "metadata": {**common, "type": "fact", "event_date": "2026-06-01"},
            "infer": False,
        },
        {
            "external_id": PROBE_JORDAN_CONTACT_ID,
            "text": "Jordan, project contact, scheduled mock interview",
            "metadata": {**common, "type": "fact", "event_date": "2026-06-02"},
            "infer": False,
        },
    ]


def _probe_memory_ids(client: MemoryApiClient, user_id: str | None) -> list[str]:
    ids: list[str] = []
    for rec in list_all_memories(client, user_id=user_id):
        meta = rec.get("metadata") or {}
        ext = meta.get("external_id") or ""
        if isinstance(ext, str) and ext.startswith(PROBE_PREFIX):
            mid = record_id(rec)
            if mid:
                ids.append(mid)
    return ids


def query_backdated_recency(client: MemoryApiClient, user_id: str | None) -> dict[str, Any]:
    hits = search_with_contract(
        client,
        "What is the latest status of Project Alpha?",
        user_id=user_id,
        namespace="public",
        top_k=10,
    )
    alpha_hits = [h for h in hits if "Project Alpha" in record_text(h)]
    latest = latest_by_event_date(alpha_hits)
    text = record_text(latest) if latest else ""
    passed = "implementation started" in text and "cancelled" not in text
    return {
        "name": "backdated_recency",
        "passed": passed,
        "expected": "max event_date -> implementation started (2026-06-10)",
        "latest_text": text,
        "candidate_count": len(alpha_hits),
    }


def query_structured_filter(client: MemoryApiClient, user_id: str | None) -> dict[str, Any]:
    filtered = open_follow_ups(client, user_id=user_id, namespace="public")
    probe_items = [
        r
        for r in filtered
        if (r.get("metadata") or {}).get("external_id") == PROBE_OPEN_ID
    ]
    vector_only = search_with_contract(
        client,
        "what is open what needs follow-up",
        user_id=user_id,
        namespace="public",
        top_k=10,
        extra_filters=None,
    )
    vector_has_probe = any(
        (r.get("metadata") or {}).get("external_id") == PROBE_OPEN_ID for r in vector_only
    )
    passed = len(probe_items) >= 1
    return {
        "name": "structured_filter",
        "passed": passed,
        "expected": "open_item metadata filter returns probe follow-up",
        "metadata_filter_hit": len(probe_items) >= 1,
        "pure_vector_hit": vector_has_probe,
        "note": (
            "Pure vector search alone may miss open items — metadata filter required "
            "(documented contract limit)."
        ),
    }


def query_entity_collision(client: MemoryApiClient, user_id: str | None) -> dict[str, Any]:
    query = "Tell me about Jordan the project contact"
    hits = search_with_contract(
        client,
        query,
        user_id=user_id,
        namespace="public",
        top_k=20,
    )
    jordan_hits = [h for h in hits if "Jordan" in record_text(h)]
    best = best_entity_match(hits, query)
    best_text = record_text(best) if best else ""
    passed = bool(
        best_text
        and "project contact" in best_text
        and "team lead's sibling" not in best_text
    )
    texts = [record_text(h) for h in hits]
    return {
        "name": "entity_collision",
        "passed": passed,
        "expected": (
            "Among Jordan hits, inline qualifier rerank picks project contact, "
            "not team lead's sibling"
        ),
        "best_jordan_text": best_text,
        "top_texts": texts[:5],
        "jordan_hit_count": len(jordan_hits),
    }


def run_probe(
    client: MemoryApiClient,
    *,
    user_id: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    today = _dt.date.today().isoformat()
    facts = probe_facts(today=today)
    write_outcomes: list[dict[str, Any]] = []
    memory_ids: list[str] = []

    if not dry_run:
        write_outcomes = import_facts(client, facts, user_id=user_id)
        memory_ids = _probe_memory_ids(client, user_id=user_id)

    queries = []
    if not dry_run:
        queries = [
            query_backdated_recency(client, user_id),
            query_structured_filter(client, user_id),
            query_entity_collision(client, user_id),
        ]

    deleted: list[str] = []
    if not dry_run and memory_ids:
        for mid in memory_ids:
            client.delete_memory(mid)
            deleted.append(mid)

    all_passed = all(q.get("passed") for q in queries) if queries else False
    return {
        "dry_run": dry_run,
        "facts_written": len(write_outcomes),
        "write_outcomes": write_outcomes,
        "memory_ids": memory_ids,
        "queries": queries,
        "all_passed": all_passed,
        "deleted_ids": deleted,
    }


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    if not args.report_path and not args.dry_run:
        today = _dt.date.today().isoformat()
        args.report_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "docs",
            "reports",
            f"acceptance-probe-{today}.md",
        )
    client = _client(args.user_id)
    report = run_probe(client, user_id=args.user_id, dry_run=args.dry_run)

    if args.report_path:
        os.makedirs(os.path.dirname(args.report_path) or ".", exist_ok=True)
        with open(args.report_path, "w", encoding="utf-8") as fh:
            fh.write(_format_report_md(report))

    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        print(_format_report_md(report))

    if report["dry_run"]:
        return 0
    return 0 if report["all_passed"] else 1


def _format_report_md(report: dict[str, Any]) -> str:
    lines = ["# Acceptance probe results", ""]
    if report["dry_run"]:
        lines.append("Dry run — no writes or queries executed.")
        return "\n".join(lines)
    lines.append(f"**Overall:** {'PASS' if report['all_passed'] else 'FAIL'}")
    lines.append("")
    for q in report.get("queries", []):
        status = "PASS" if q.get("passed") else "FAIL"
        lines.append(f"## {q['name']} — {status}")
        lines.append(f"- Expected: {q.get('expected', '')}")
        for key, value in q.items():
            if key in ("name", "passed", "expected"):
                continue
            lines.append(f"- {key}: {value}")
        lines.append("")
    lines.append(f"Deleted {len(report.get('deleted_ids', []))} probe memories.")
    return "\n".join(lines)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="5-fact memory contract acceptance probe.")
    p.add_argument("--user-id", default=None)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--json", action="store_true")
    p.add_argument(
        "--report-path",
        default=None,
        help="write markdown report (default: docs/reports/acceptance-probe-YYYY-MM-DD.md)",
    )
    return p.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
