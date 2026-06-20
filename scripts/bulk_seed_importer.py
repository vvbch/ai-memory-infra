#!/usr/bin/env python3
"""Idempotent bulk memory seed importer (ADR 037).

Loads facts from a JSON file, each with a caller-supplied deterministic
``external_id`` in metadata. Before writing, checks whether that external_id
already exists. Uses a longer write timeout and treats client timeouts as
*verify-then-skip* — never retry with reworded text.

Input JSON shape::

    {
      "facts": [
        {
          "external_id": "portfolio:pgvector-blr1",
          "text": "...",
          "metadata": {
            "type": "fact",
            "source": "cursor-repo",
            "event_date": "2026-06-01",
            "namespace": "public"
          },
          "infer": true
        }
      ]
    }

Usage::

    python scripts/bulk_seed_importer.py facts.json
    python scripts/bulk_seed_importer.py facts.json --dry-run
"""

from __future__ import annotations

import argparse
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

from mcp_proxy.client import MemoryApiClient, MemoryApiConfig  # noqa: E402
from mcp_proxy.idempotent_write import (  # noqa: E402
    DEFAULT_VERIFY_INTERVAL_S,
    DEFAULT_VERIFY_WINDOW_S,
    add_memory_idempotent,
    find_by_external_id,
    list_all_memories,
    verify_interval_seconds,
    verify_window_seconds,
    write_timeout_seconds,
)
from memory.contract import (  # noqa: E402
    MemoryContractError,
    build_fact_metadata,
    validate_fact_metadata,
    validate_fact_text,
)


def _client(user_id: str | None, timeout_s: float) -> MemoryApiClient:
    config = MemoryApiConfig.from_env()
    if user_id:
        config = MemoryApiConfig(
            base_url=config.base_url, api_key=config.api_key, user_id=user_id
        )
    timeout = httpx.Timeout(timeout_s, connect=10.0)
    return MemoryApiClient(config, http_client=httpx.Client(timeout=timeout))


def _record_id(rec: dict[str, Any]) -> str:
    return str(rec.get("id") or rec.get("memory_id") or "")


def _prepare_fact_metadata(fact: dict[str, Any]) -> dict[str, Any]:
    raw_meta = dict(fact.get("metadata") or {})
    external_id = str(fact["external_id"])
    event_date = raw_meta.get("event_date") or raw_meta.get("occurred_at")
    source = raw_meta.get("source")
    if not event_date or not source:
        raise MemoryContractError(
            "each fact requires metadata.event_date and metadata.source"
        )
    validate_fact_text(str(fact["text"]))
    fact_type = raw_meta.get("type", "fact")
    meta = build_fact_metadata(
        event_date=str(event_date),
        source=str(source),
        source_doc_id=raw_meta.get("source_doc_id"),
        namespace=raw_meta.get("namespace"),
        external_id=external_id,
        ventures=raw_meta.get("ventures"),
        extra={},
    )
    if fact_type != "fact":
        meta["type"] = fact_type
    for key in ("status", "due_at", "revisit_at"):
        if raw_meta.get(key) is not None:
            meta[key] = raw_meta[key]
    validate_fact_metadata(meta, require_external_id=True)
    return meta


def import_facts(
    client: MemoryApiClient,
    facts: list[dict[str, Any]],
    *,
    user_id: str | None = None,
    dry_run: bool = False,
    verify_window_s: float = DEFAULT_VERIFY_WINDOW_S,
    verify_interval_s: float = DEFAULT_VERIFY_INTERVAL_S,
) -> list[dict[str, Any]]:
    cache = list_all_memories(client, user_id=user_id)
    outcomes: list[dict[str, Any]] = []

    for fact in facts:
        external_id = fact.get("external_id")
        text = fact.get("text")
        if not external_id or not text:
            outcomes.append(
                {
                    "external_id": external_id,
                    "status": "invalid",
                    "message": "each fact requires external_id and text",
                }
            )
            continue

        try:
            metadata = _prepare_fact_metadata(fact)
        except MemoryContractError as exc:
            outcomes.append(
                {
                    "external_id": external_id,
                    "status": "invalid",
                    "message": str(exc),
                }
            )
            continue

        existing = find_by_external_id(
            client, str(external_id), user_id=user_id, cache=cache
        )
        if existing is not None:
            outcomes.append(
                {
                    "external_id": external_id,
                    "status": "skipped_exists",
                    "memory_id": _record_id(existing),
                }
            )
            continue

        if dry_run:
            outcomes.append({"external_id": external_id, "status": "would_write"})
            continue

        infer = bool(fact.get("infer", True))
        outcome = add_memory_idempotent(
            client,
            str(text),
            external_id=str(external_id),
            user_id=user_id,
            metadata=metadata,
            infer=infer,
            verify_window_s=verify_window_s,
            verify_interval_s=verify_interval_s,
            cache=cache,
        )
        outcomes.append(outcome)

    return outcomes


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Idempotent bulk memory seed importer (ADR 037).")
    p.add_argument("input", help="JSON file with a top-level 'facts' array")
    p.add_argument("--dry-run", action="store_true", help="check only; do not write")
    p.add_argument("--user-id", default=None)
    p.add_argument(
        "--write-timeout",
        type=float,
        default=write_timeout_seconds(),
    )
    p.add_argument("--verify-window", type=float, default=verify_window_seconds())
    p.add_argument("--verify-interval", type=float, default=verify_interval_seconds())
    p.add_argument("--json", action="store_true", dest="json_out")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    with open(args.input, encoding="utf-8") as fh:
        payload = json.loads(fh.read())
    facts = payload.get("facts") if isinstance(payload, dict) else payload
    if not isinstance(facts, list):
        print("ERROR: input must be a JSON object with a 'facts' array", file=sys.stderr)
        return 2

    client = _client(args.user_id, args.write_timeout)
    outcomes = import_facts(
        client,
        facts,
        user_id=args.user_id,
        dry_run=args.dry_run,
        verify_window_s=args.verify_window,
        verify_interval_s=args.verify_interval,
    )

    summary = {
        "total": len(outcomes),
        "written": sum(1 for o in outcomes if o["status"] == "written"),
        "skipped_exists": sum(1 for o in outcomes if o["status"] == "skipped_exists"),
        "verified_after_timeout": sum(
            1 for o in outcomes if o["status"] == "verified_after_timeout"
        ),
        "timeout_unverified": sum(
            1 for o in outcomes if o["status"] == "timeout_unverified"
        ),
        "invalid": sum(1 for o in outcomes if o["status"] == "invalid"),
        "outcomes": outcomes,
    }

    if args.json_out:
        print(json.dumps(summary, indent=2, default=str))
    else:
        print(
            f"Bulk import: {summary['written']} written, "
            f"{summary['skipped_exists']} skipped (exists), "
            f"{summary['verified_after_timeout']} verified after timeout, "
            f"{summary['timeout_unverified']} timeout unverified, "
            f"{summary['invalid']} invalid"
        )
        for o in outcomes:
            if o["status"] not in ("written", "skipped_exists"):
                print(f"  {o['external_id']}: {o['status']}")

    return 1 if summary["timeout_unverified"] or summary["invalid"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
