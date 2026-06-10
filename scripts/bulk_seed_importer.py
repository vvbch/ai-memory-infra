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
          "metadata": {"type": "fact", "source": "cursor"},
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
import time
from typing import Any

import httpx

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from mcp_proxy.client import MemoryApiClient, MemoryApiConfig  # noqa: E402

DEFAULT_WRITE_TIMEOUT_S = 120.0
DEFAULT_VERIFY_WINDOW_S = 90.0
DEFAULT_VERIFY_INTERVAL_S = 3.0
EXTERNAL_ID_KEY = "external_id"


def _client(user_id: str | None, timeout_s: float) -> MemoryApiClient:
    config = MemoryApiConfig.from_env()
    if user_id:
        config = MemoryApiConfig(
            base_url=config.base_url, api_key=config.api_key, user_id=user_id
        )
    timeout = httpx.Timeout(timeout_s, connect=10.0)
    return MemoryApiClient(config, http_client=httpx.Client(timeout=timeout))


def _normalize_list(raw: Any) -> list[dict[str, Any]]:
    if isinstance(raw, list):
        return [r for r in raw if isinstance(r, dict)]
    if isinstance(raw, dict):
        items = raw.get("results", raw.get("memories"))
        if isinstance(items, list):
            return [r for r in items if isinstance(r, dict)]
    return []


def list_all_memories(client: MemoryApiClient, *, user_id: str | None = None) -> list[dict[str, Any]]:
    """Return all memories, requesting a high limit when the API supports it."""
    raw = client.list_memories(user_id=user_id, limit=1000)
    return _normalize_list(raw)


def _record_metadata(rec: dict[str, Any]) -> dict[str, Any]:
    nested = rec.get("metadata")
    return dict(nested) if isinstance(nested, dict) else {}


def _record_id(rec: dict[str, Any]) -> str:
    return str(rec.get("id") or rec.get("memory_id") or "")


def find_by_external_id(
    client: MemoryApiClient,
    external_id: str,
    *,
    user_id: str | None = None,
    cache: list[dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    items = cache if cache is not None else list_all_memories(client, user_id=user_id)
    for rec in items:
        meta = _record_metadata(rec)
        if meta.get(EXTERNAL_ID_KEY) == external_id:
            return rec
    try:
        filtered = client.search_memories(
            external_id,
            user_id=user_id,
            top_k=5,
            filters={EXTERNAL_ID_KEY: external_id},
        )
        for rec in _normalize_list(filtered):
            meta = _record_metadata(rec)
            if meta.get(EXTERNAL_ID_KEY) == external_id:
                return rec
    except Exception:
        pass
    return None


def _write_fact(
    client: MemoryApiClient,
    fact: dict[str, Any],
    *,
    user_id: str | None,
    verify_window_s: float,
    verify_interval_s: float,
) -> dict[str, Any]:
    external_id = fact["external_id"]
    text = fact["text"]
    metadata = dict(fact.get("metadata") or {})
    metadata[EXTERNAL_ID_KEY] = external_id
    infer = bool(fact.get("infer", True))

    try:
        result = client.add_memory(text, metadata=metadata, infer=infer, user_id=user_id)
        return {"external_id": external_id, "status": "written", "result": result}
    except httpx.TimeoutException:
        deadline = time.monotonic() + verify_window_s
        while time.monotonic() < deadline:
            time.sleep(verify_interval_s)
            existing = find_by_external_id(client, external_id, user_id=user_id)
            if existing is not None:
                return {
                    "external_id": external_id,
                    "status": "verified_after_timeout",
                    "memory_id": _record_id(existing),
                }
        return {
            "external_id": external_id,
            "status": "timeout_unverified",
            "message": (
                "client timed out and external_id was not found during verify window; "
                "do not reword-retry — re-run importer or inspect server logs"
            ),
        }


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

        outcome = _write_fact(
            client,
            fact,
            user_id=user_id,
            verify_window_s=verify_window_s,
            verify_interval_s=verify_interval_s,
        )
        outcomes.append(outcome)
        if outcome["status"] == "written":
            refreshed = list_all_memories(client, user_id=user_id)
            cache[:] = refreshed

    return outcomes


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Idempotent bulk memory seed importer (ADR 037).")
    p.add_argument("input", help="JSON file with a top-level 'facts' array")
    p.add_argument("--dry-run", action="store_true", help="check only; do not write")
    p.add_argument("--user-id", default=None)
    p.add_argument(
        "--write-timeout",
        type=float,
        default=float(os.environ.get("AI_MEMORY_WRITE_TIMEOUT", DEFAULT_WRITE_TIMEOUT_S)),
    )
    p.add_argument("--verify-window", type=float, default=DEFAULT_VERIFY_WINDOW_S)
    p.add_argument("--verify-interval", type=float, default=DEFAULT_VERIFY_INTERVAL_S)
    p.add_argument("--json", action="store_true", dest="json_out")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    payload = json.loads(open(args.input, encoding="utf-8").read())
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
        "outcomes": outcomes,
    }

    if args.json_out:
        print(json.dumps(summary, indent=2, default=str))
    else:
        print(
            f"Bulk import: {summary['written']} written, "
            f"{summary['skipped_exists']} skipped (exists), "
            f"{summary['verified_after_timeout']} verified after timeout, "
            f"{summary['timeout_unverified']} timeout unverified"
        )
        for o in outcomes:
            if o["status"] not in ("written", "skipped_exists"):
                print(f"  {o['external_id']}: {o['status']}")

    return 1 if summary["timeout_unverified"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
