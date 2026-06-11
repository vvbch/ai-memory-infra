#!/usr/bin/env python3
"""Memory Daily Driver v0 — thin helper over the live ai-memory REST API.

WHY THIS EXISTS
---------------
The memory server is live and proven (Phase 0 de-risk, 2026-06-09): the agent can
read/write it over REST. This module is the **Phase 1** plumbing that makes that
usable for the actual product premise — *use the memory layer to plan the day and
track recruiter reach-outs* — while enforcing the metadata contract so nothing
lands in the bank untagged or mis-typed.

It is a **thin projection** (tenets 4/7, ADR 029 §5): no new datastore, no second
brain. Every function shapes a contract-correct request and delegates to
``mcp_proxy.client.MemoryApiClient`` (the same client the MCP proxy uses).

CONTRACT ENFORCED (ADR 028 + ADR 029)
-------------------------------------
* One ``user_id`` for the person (``chandrav``); identity is never the
  discriminator (ADR 028). ``source`` is mandatory on every write.
* Every memory carries a ``type`` (``fact`` | ``decision`` | ``open_item``).
* Authored items (open items, decisions) are written ``infer=False`` so the live
  API stores them **verbatim** rather than re-extracting/rewording them.
* Open items carry a lifecycle: ``status`` (``open`` -> ``in_progress`` ->
  ``done`` | ``dropped``), optional ``due_at`` / ``revisit_at``, and on closure a
  ``resolution`` + ``closed_at``.
* Venture tags (ADR 003) are validated; recruiter reach-outs are ``career``.

DATE FILTERING IS CLIENT-SIDE (Phase 0 open question)
-----------------------------------------------------
Phase 0 proved ``/search`` supports server-side metadata *equality* filters, but
left open whether ``due_at`` / ``revisit_at`` support range operators. So
``agenda`` lists all open items and buckets overdue / due-today / revisit-due
client-side — correct regardless of that answer, and fine at v0 bank size. If the
bank grows, push ranges server-side (tracked in BACKLOG).

USAGE
-----
  # Plan the day (overdue / due today / needs revisit / upcoming):
  python scripts/memory.py agenda

  # Log an open item / follow-up with dates and venture tags:
  python scripts/memory.py add-open-item "Follow up with recruiter Acme Corp" \
      --due 2026-06-12 --revisit 2026-06-11 --venture career

  # Recruiter reach-out board (open items tagged 'career'):
  python scripts/memory.py recruiters

  # Capture a decision / a fact (stored verbatim):
  python scripts/memory.py add-decision "Chose DigitalOcean over Hetzner for BLR latency"
  python scripts/memory.py add-fact "Prefers Python over shell for tooling"

  # Close an open item with what happened:
  python scripts/memory.py close <memory_id> --resolution "Recruiter passed; reapply Q3"

  # Delete or update a memory by id (ADR 037 — MCP parity):
  python scripts/memory.py delete-memory <memory_id>
  python scripts/memory.py update-memory <memory_id> "revised text"

Add ``--json`` for machine-readable output, ``--user-id`` to override the bank
(e.g. a throwaway id for safe smoke tests, mirroring the Phase 0 probe).

PORTABILITY (tenet 2/3): pure stdlib + the shared httpx client; no shell-isms;
UTF-8 forced so Windows consoles never crash on output.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as _dt
import json
import os
import sys
from typing import Any

# Path bootstrap: import the shared REST client whether or not the package is
# installed editable (keeps the script runnable straight from a fresh clone).
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(os.path.dirname(_SCRIPT_DIR), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)
# This file is named memory.py — drop scripts/ from sys.path so src/memory/ package wins.
if _SCRIPT_DIR in sys.path:
    sys.path.remove(_SCRIPT_DIR)

import httpx

from memory.contract import (  # noqa: E402
    MemoryContractError as ContractMemoryError,
    build_fact_metadata,
    normalize_source,
    validate_fact_text,
)
from mcp_proxy.client import MemoryApiClient, MemoryApiConfig  # noqa: E402
from mcp_proxy.idempotent_write import write_timeout_seconds  # noqa: E402

# --------------------------------------------------------------------------- #
# ADR 029 / ADR 028 / ADR 003 vocabulary (the contract this helper enforces).
# --------------------------------------------------------------------------- #
TYPE_FACT = "fact"
TYPE_DECISION = "decision"
TYPE_OPEN_ITEM = "open_item"
VALID_TYPES = frozenset({TYPE_FACT, TYPE_DECISION, TYPE_OPEN_ITEM})

STATUS_OPEN = "open"
STATUS_IN_PROGRESS = "in_progress"
STATUS_DONE = "done"
STATUS_DROPPED = "dropped"
OPEN_STATUSES = frozenset({STATUS_OPEN, STATUS_IN_PROGRESS})
CLOSED_STATUSES = frozenset({STATUS_DONE, STATUS_DROPPED})
VALID_STATUSES = OPEN_STATUSES | CLOSED_STATUSES

# Venture tags (ADR 003). Recruiter reach-outs are tagged with RECRUITER_VENTURE.
VALID_VENTURES = frozenset(
    {"trading_firm", "social_media", "ria", "personal", "career", "migration"}
)
RECRUITER_VENTURE = "career"

# This helper runs inside the Cursor/agent surface.
DEFAULT_SOURCE = "cursor"

# Metadata keys that may live either nested under "metadata" or flattened at the
# top of a returned record — we read both defensively.
_META_KEYS = (
    "type",
    "status",
    "source",
    "due_at",
    "revisit_at",
    "event_date",
    "occurred_at",
    "namespace",
    "source_doc_id",
    "external_id",
    "resolution",
    "closed_at",
    "ventures",
)


class MemoryContractError(ValueError):
    """Raised when a requested write would violate the ADR 028/029 contract."""


# --------------------------------------------------------------------------- #
# Validation.
# --------------------------------------------------------------------------- #
def _validate_ventures(ventures: list[str]) -> None:
    bad = [v for v in ventures if v not in VALID_VENTURES]
    if bad:
        raise MemoryContractError(
            f"unknown venture tag(s) {bad}; valid: {sorted(VALID_VENTURES)}"
        )


def _validate_date(label: str, value: str) -> None:
    try:
        _dt.date.fromisoformat(str(value)[:10])
    except ValueError as exc:
        raise MemoryContractError(
            f"{label} must be an ISO date (YYYY-MM-DD), got {value!r}"
        ) from exc


def _clean(metadata: dict[str, Any]) -> dict[str, Any]:
    """Drop keys whose value is None/empty so we never send blank tags."""
    return {k: v for k, v in metadata.items() if v not in (None, "", [])}


# --------------------------------------------------------------------------- #
# Capture (writes) — authored items go in verbatim (infer=False).
# --------------------------------------------------------------------------- #
def capture_open_item(
    client: MemoryApiClient,
    text: str,
    *,
    due_at: str | None = None,
    revisit_at: str | None = None,
    ventures: list[str] | None = None,
    occurred_at: str | None = None,
    source: str = DEFAULT_SOURCE,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Capture a todo / follow-up as an ``open_item`` (status=open)."""
    if not text.strip():
        raise MemoryContractError("open item text must not be empty")
    ventures = list(ventures or [])
    _validate_ventures(ventures)
    for label, val in (
        ("due_at", due_at),
        ("revisit_at", revisit_at),
        ("occurred_at", occurred_at),
    ):
        if val:
            _validate_date(label, val)
    metadata = _clean(
        {
            "type": TYPE_OPEN_ITEM,
            "status": STATUS_OPEN,
            "source": normalize_source(source),
            "due_at": due_at,
            "revisit_at": revisit_at,
            "occurred_at": occurred_at,
            "ventures": ventures,
        }
    )
    return client.add_memory(text, metadata=metadata, infer=False, user_id=user_id)


def capture_decision(
    client: MemoryApiClient,
    text: str,
    *,
    occurred_at: str | None = None,
    ventures: list[str] | None = None,
    source: str = DEFAULT_SOURCE,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Capture a timestamped ``decision`` (stored verbatim)."""
    if not text.strip():
        raise MemoryContractError("decision text must not be empty")
    ventures = list(ventures or [])
    _validate_ventures(ventures)
    if occurred_at:
        _validate_date("occurred_at", occurred_at)
    metadata = _clean(
        {
            "type": TYPE_DECISION,
            "source": normalize_source(source),
            "occurred_at": occurred_at,
            "ventures": ventures,
        }
    )
    return client.add_memory(text, metadata=metadata, infer=False, user_id=user_id)


def capture_fact(
    client: MemoryApiClient,
    text: str,
    *,
    ventures: list[str] | None = None,
    occurred_at: str | None = None,
    event_date: str | None = None,
    source: str = DEFAULT_SOURCE,
    source_doc_id: str | None = None,
    namespace: str | None = None,
    external_id: str | None = None,
    infer: bool = False,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Capture a ``fact``. Verbatim by default; pass infer=True for extraction."""
    ventures = list(ventures or [])
    _validate_ventures(ventures)
    resolved_event = event_date or occurred_at
    if not infer:
        try:
            validate_fact_text(text)
        except ContractMemoryError as exc:
            raise MemoryContractError(str(exc)) from exc
    try:
        if resolved_event:
            metadata = build_fact_metadata(
                event_date=resolved_event,
                source=normalize_source(source),
                source_doc_id=source_doc_id,
                namespace=namespace,
                external_id=external_id,
                ventures=ventures,
            )
        else:
            metadata = _clean(
                {
                    "type": TYPE_FACT,
                    "source": normalize_source(source),
                    "source_doc_id": source_doc_id,
                    "namespace": namespace or "public",
                    "ventures": ventures,
                    "external_id": external_id,
                }
            )
    except ContractMemoryError as exc:
        raise MemoryContractError(str(exc)) from exc

    if external_id:
        return client.add_memory_idempotent(
            text,
            external_id=external_id,
            metadata=metadata,
            infer=infer,
            user_id=user_id,
        )
    return client.add_memory(text, metadata=metadata, infer=infer, user_id=user_id)


# --------------------------------------------------------------------------- #
# Read helpers.
# --------------------------------------------------------------------------- #
def _results(raw: Any) -> list[dict[str, Any]]:
    items = raw.get("results", []) if isinstance(raw, dict) else raw
    return [r for r in items if isinstance(r, dict)]


def _record_text(rec: dict[str, Any]) -> str:
    value = rec.get("memory") or rec.get("text") or ""
    return str(value)


def _record_id(rec: dict[str, Any]) -> str:
    value = rec.get("id") or rec.get("memory_id") or ""
    return str(value)


def _record_metadata(rec: dict[str, Any]) -> dict[str, Any]:
    nested = rec.get("metadata")
    meta: dict[str, Any] = dict(nested) if isinstance(nested, dict) else {}
    # Fall back to flattened top-level fields if the server didn't nest them.
    for key in _META_KEYS:
        if key not in meta and key in rec:
            meta[key] = rec[key]
    return meta


def _as_open_item(rec: dict[str, Any]) -> dict[str, Any]:
    meta = _record_metadata(rec)
    ventures = meta.get("ventures") or []
    if not isinstance(ventures, list):
        ventures = [ventures]
    return {
        "id": _record_id(rec),
        "text": _record_text(rec),
        "status": meta.get("status", STATUS_OPEN),
        "due_at": meta.get("due_at"),
        "revisit_at": meta.get("revisit_at"),
        "occurred_at": meta.get("occurred_at"),
        "ventures": list(ventures),
        "source": meta.get("source"),
        "created_at": rec.get("created_at"),
        "resolution": meta.get("resolution"),
        "closed_at": meta.get("closed_at"),
    }


def open_items(
    client: MemoryApiClient,
    *,
    user_id: str | None = None,
    include_closed: bool = False,
) -> list[dict[str, Any]]:
    """Return open_item memories (open/in_progress by default)."""
    out: list[dict[str, Any]] = []
    for rec in _results(client.list_memories(user_id=user_id)):
        meta = _record_metadata(rec)
        if meta.get("type") != TYPE_OPEN_ITEM:
            continue
        status = meta.get("status", STATUS_OPEN)
        if not include_closed and status in CLOSED_STATUSES:
            continue
        out.append(_as_open_item(rec))
    return out


def _as_date(value: Any) -> _dt.date | None:
    if not value:
        return None
    try:
        return _dt.date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _date_sort_key(value: Any) -> str:
    # None/blank sort last; ISO date strings sort chronologically as text.
    parsed = _as_date(value)
    return parsed.isoformat() if parsed else "9999-12-31"


def agenda(
    client: MemoryApiClient,
    *,
    today: _dt.date | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Bucket open items into overdue / due-today / revisit-due / upcoming / undated.

    Each item lands in exactly one bucket (overdue beats due-today beats
    revisit-due beats upcoming). Dates are compared client-side (see module docs).
    """
    today = today or _dt.date.today()
    overdue: list[dict[str, Any]] = []
    due_today: list[dict[str, Any]] = []
    revisit_due: list[dict[str, Any]] = []
    upcoming: list[dict[str, Any]] = []
    undated: list[dict[str, Any]] = []

    for item in open_items(client, user_id=user_id):
        due = _as_date(item["due_at"])
        revisit = _as_date(item["revisit_at"])
        if due is not None and due < today:
            overdue.append(item)
        elif due is not None and due == today:
            due_today.append(item)
        elif revisit is not None and revisit <= today:
            revisit_due.append(item)
        elif due is not None or revisit is not None:
            upcoming.append(item)
        else:
            undated.append(item)

    overdue.sort(key=lambda it: _date_sort_key(it["due_at"]))
    due_today.sort(key=lambda it: _date_sort_key(it["due_at"]))
    revisit_due.sort(key=lambda it: _date_sort_key(it["revisit_at"]))
    upcoming.sort(key=lambda it: _date_sort_key(it["due_at"] or it["revisit_at"]))

    return {
        "today": today.isoformat(),
        "overdue": overdue,
        "due_today": due_today,
        "revisit_due": revisit_due,
        "upcoming": upcoming,
        "undated": undated,
    }


def recruiter_board(
    client: MemoryApiClient,
    *,
    user_id: str | None = None,
    include_closed: bool = False,
) -> list[dict[str, Any]]:
    """Open items tagged with the recruiter venture (``career``), soonest first."""
    items = open_items(client, user_id=user_id, include_closed=include_closed)
    board = [it for it in items if RECRUITER_VENTURE in (it["ventures"] or [])]
    board.sort(key=lambda it: _date_sort_key(it["due_at"] or it["revisit_at"]))
    return board


def close_item(
    client: MemoryApiClient,
    memory_id: str,
    resolution: str,
    *,
    status: str = STATUS_DONE,
    closed_at: str | None = None,
) -> dict[str, Any]:
    """Close an open item in place: record status + resolution + closed_at.

    Updates the existing memory (preserving its id and created_at) via the live
    ``PUT /memories/{id}`` endpoint, merging closure fields into the existing
    metadata so type/source/ventures/dates are kept.
    """
    if status not in CLOSED_STATUSES:
        raise MemoryContractError(
            f"close status must be one of {sorted(CLOSED_STATUSES)}, got {status!r}"
        )
    if not resolution.strip():
        raise MemoryContractError("a resolution (what happened) is required to close an item")
    closed_at = closed_at or _dt.date.today().isoformat()
    _validate_date("closed_at", closed_at)

    raw = client.get_memory(memory_id)
    wrapped = _results(raw)
    rec = wrapped[0] if wrapped else raw
    text = _record_text(rec) or " "  # PUT requires non-empty text
    meta = _record_metadata(rec)
    meta["status"] = status
    meta["resolution"] = resolution
    meta["closed_at"] = closed_at
    return client.update_memory(memory_id, text, metadata=_clean(meta))


def delete_memory_record(
    client: MemoryApiClient,
    memory_id: str,
) -> dict[str, Any]:
    """Delete a memory by id."""
    if not memory_id.strip():
        raise MemoryContractError("memory_id must not be empty")
    return client.delete_memory(memory_id)


def update_memory_record(
    client: MemoryApiClient,
    memory_id: str,
    text: str,
    *,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Update a memory's text and optional metadata."""
    if not memory_id.strip():
        raise MemoryContractError("memory_id must not be empty")
    if not text.strip():
        raise MemoryContractError("memory text must not be empty")
    return client.update_memory(memory_id, text, metadata=_clean(metadata or {}))


# --------------------------------------------------------------------------- #
# Rendering (human-readable plain English).
# --------------------------------------------------------------------------- #
def _fmt_item(item: dict[str, Any]) -> str:
    bits = [f"[{_record_short_id(item['id'])}] {item['text']}"]
    tail = []
    if item.get("due_at"):
        tail.append(f"due {item['due_at']}")
    if item.get("revisit_at"):
        tail.append(f"revisit {item['revisit_at']}")
    if item.get("ventures"):
        tail.append("/".join(item["ventures"]))
    if item.get("status") and item["status"] != STATUS_OPEN:
        tail.append(item["status"])
    if tail:
        bits.append(f"  ({', '.join(tail)})")
    return "".join(bits)


def _record_short_id(value: str) -> str:
    return value[:8] if value else "?"


def _render_agenda(data: dict[str, Any]) -> str:
    lines = [f"Agenda for {data['today']}", ""]
    sections = (
        ("OVERDUE", "overdue"),
        ("DUE TODAY", "due_today"),
        ("NEEDS REVISIT", "revisit_due"),
        ("UPCOMING", "upcoming"),
        ("NO DATE", "undated"),
    )
    any_items = False
    for label, key in sections:
        items = data.get(key, [])
        if not items:
            continue
        any_items = True
        lines.append(f"{label} ({len(items)}):")
        lines.extend(f"  - {_fmt_item(it)}" for it in items)
        lines.append("")
    if not any_items:
        lines.append("Nothing open. Inbox zero.")
    return "\n".join(lines).rstrip()


def _render_board(board: list[dict[str, Any]]) -> str:
    if not board:
        return "No open recruiter reach-outs."
    lines = [f"Recruiter reach-outs ({len(board)}):"]
    lines.extend(f"  - {_fmt_item(it)}" for it in board)
    return "\n".join(lines)


def _render_capture(kind: str, text: str, result: dict[str, Any]) -> str:
    return f"Stored {kind}: {text}\n(server response: {json.dumps(result, default=str)})"


# --------------------------------------------------------------------------- #
# CLI.
# --------------------------------------------------------------------------- #
def _client(user_id: str | None) -> MemoryApiClient:
    config = MemoryApiConfig.from_env()
    if user_id:
        config = MemoryApiConfig(
            base_url=config.base_url, api_key=config.api_key, user_id=user_id
        )
    timeout = httpx.Timeout(write_timeout_seconds(), connect=10.0)
    return MemoryApiClient(config, http_client=httpx.Client(timeout=timeout))


def _parse(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="memory",
        description="Memory Daily Driver v0 — capture/plan/track over the live ai-memory API.",
    )
    p.add_argument("--json", action="store_true", help="machine-readable JSON output")
    p.add_argument(
        "--user-id", default=None, help="override the bank user_id (e.g. a smoke-test id)"
    )
    sub = p.add_subparsers(dest="command", required=True)

    oi = sub.add_parser("add-open-item", help="capture a todo / follow-up")
    oi.add_argument("text")
    oi.add_argument("--due", default=None, help="due date YYYY-MM-DD")
    oi.add_argument("--revisit", default=None, help="revisit date YYYY-MM-DD")
    oi.add_argument("--occurred", default=None, help="when it actually happened YYYY-MM-DD")
    oi.add_argument("--venture", action="append", default=[], help="venture tag (repeatable)")
    oi.add_argument("--source", default=DEFAULT_SOURCE)

    dec = sub.add_parser("add-decision", help="capture a timestamped decision")
    dec.add_argument("text")
    dec.add_argument("--occurred", default=None, help="when decided YYYY-MM-DD")
    dec.add_argument("--venture", action="append", default=[], help="venture tag (repeatable)")
    dec.add_argument("--source", default=DEFAULT_SOURCE)

    fa = sub.add_parser("add-fact", help="capture a durable fact")
    fa.add_argument("text")
    fa.add_argument("--event-date", default=None, help="when the fact/event occurred YYYY-MM-DD")
    fa.add_argument("--occurred", default=None, help="alias for --event-date (compat)")
    fa.add_argument("--venture", action="append", default=[], help="venture tag (repeatable)")
    fa.add_argument("--source", default=DEFAULT_SOURCE)
    fa.add_argument("--source-doc-id", default=None, help="traceable origin reference")
    fa.add_argument("--namespace", default=None, choices=["public", "sensitive"])
    fa.add_argument("--external-id", default=None, help="deterministic id for idempotent writes")
    fa.add_argument("--infer", action="store_true", help="run Mem0 extraction instead of verbatim")

    sub.add_parser("agenda", help="plan the day: overdue / due / revisit / upcoming")
    rec = sub.add_parser("recruiters", help="open recruiter reach-outs (career)")
    rec.add_argument("--include-closed", action="store_true")

    cl = sub.add_parser("close", help="close an open item with what happened")
    cl.add_argument("memory_id")
    cl.add_argument("--resolution", required=True, help="what happened")
    cl.add_argument("--status", default=STATUS_DONE, choices=sorted(CLOSED_STATUSES))
    cl.add_argument("--closed-at", default=None, help="closure date YYYY-MM-DD")

    dm = sub.add_parser("delete-memory", help="delete a memory by id")
    dm.add_argument("memory_id")

    um = sub.add_parser("update-memory", help="update a memory's text")
    um.add_argument("memory_id")
    um.add_argument("text")
    um.add_argument(
        "--metadata-json",
        default=None,
        help='optional metadata object as JSON, e.g. \'{"type":"fact"}\'',
    )

    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        with contextlib.suppress(Exception):
            sys.stdout.reconfigure(encoding="utf-8")

    args = _parse(sys.argv[1:] if argv is None else argv)

    try:
        client = _client(args.user_id)
        if args.command == "add-open-item":
            result = capture_open_item(
                client,
                args.text,
                due_at=args.due,
                revisit_at=args.revisit,
                occurred_at=args.occurred,
                ventures=args.venture,
                source=args.source,
            )
            payload: Any = result
            human = _render_capture("open item", args.text, result)
        elif args.command == "add-decision":
            result = capture_decision(
                client,
                args.text,
                occurred_at=args.occurred,
                ventures=args.venture,
                source=args.source,
            )
            payload = result
            human = _render_capture("decision", args.text, result)
        elif args.command == "add-fact":
            result = capture_fact(
                client,
                args.text,
                event_date=args.event_date or args.occurred,
                ventures=args.venture,
                source=args.source,
                source_doc_id=args.source_doc_id,
                namespace=args.namespace,
                external_id=args.external_id,
                infer=args.infer,
            )
            payload = result
            human = _render_capture("fact", args.text, result)
        elif args.command == "agenda":
            payload = agenda(client)
            human = _render_agenda(payload)
        elif args.command == "recruiters":
            payload = recruiter_board(client, include_closed=args.include_closed)
            human = _render_board(payload)
        elif args.command == "close":
            payload = close_item(
                client,
                args.memory_id,
                args.resolution,
                status=args.status,
                closed_at=args.closed_at,
            )
            human = f"Closed {args.memory_id} ({args.status}): {args.resolution}"
        elif args.command == "delete-memory":
            payload = delete_memory_record(client, args.memory_id)
            human = f"Deleted {args.memory_id}"
        elif args.command == "update-memory":
            meta = json.loads(args.metadata_json) if args.metadata_json else None
            if meta is not None and not isinstance(meta, dict):
                raise MemoryContractError("metadata-json must decode to a JSON object")
            payload = update_memory_record(
                client,
                args.memory_id,
                args.text,
                metadata=meta,
            )
            human = f"Updated {args.memory_id}: {args.text}"
        else:  # pragma: no cover - argparse enforces a valid command
            raise MemoryContractError(f"unknown command {args.command!r}")
    except MemoryContractError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(payload, default=str, indent=2) if args.json else human)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
