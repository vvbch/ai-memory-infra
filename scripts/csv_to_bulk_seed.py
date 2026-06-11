#!/usr/bin/env python3
"""Convert reconciled-facts CSV to bulk_seed_importer JSON (ADR 037).

The operator-editable sheet lives at ``data/reconciled-facts.csv``. After you
fill it in, convert then import::

    python scripts/csv_to_bulk_seed.py data/reconciled-facts.csv -o data/reconciled-facts.json
    python scripts/bulk_seed_importer.py data/reconciled-facts.json --dry-run
    python scripts/bulk_seed_importer.py data/reconciled-facts.json

CSV columns (header row required):

  external_id   — required; stable id e.g. portfolio:pgvector-blr1
  text          — required; qualify colliding entity names inline
  event_date    — required; YYYY-MM-DD
  source        — required; cursor-repo|chatgpt|perplexity|claude|manual|mcp|extension
  namespace     — optional; public (default) or sensitive
  source_doc_id — optional traceable ref
  type          — optional; fact (default), open_item, decision
  status        — optional; for open_item e.g. open
  infer         — optional; false (default) or true
  ventures      — optional; comma-separated tags e.g. career,personal
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent
_SRC = _SCRIPT_DIR.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
if str(_SCRIPT_DIR) in sys.path:
    sys.path.remove(str(_SCRIPT_DIR))

from memory.contract import MemoryContractError, validate_fact_text  # noqa: E402

REQUIRED_COLUMNS = ("external_id", "text", "event_date", "source")
OPTIONAL_COLUMNS = (
    "namespace",
    "source_doc_id",
    "type",
    "status",
    "infer",
    "ventures",
)
ALL_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS


def _parse_bool(value: str | None, *, default: bool) -> bool:
    if value is None or str(value).strip() == "":
        return default
    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes", "y"}:
        return True
    if normalized in {"false", "0", "no", "n"}:
        return False
    raise MemoryContractError(f"infer must be true/false, got {value!r}")


def _row_to_fact(row: dict[str, str], *, line_no: int) -> dict[str, Any]:
    external_id = (row.get("external_id") or "").strip()
    text = (row.get("text") or "").strip()
    event_date = (row.get("event_date") or "").strip()
    source = (row.get("source") or "").strip()

    if not external_id or not text or not event_date or not source:
        raise MemoryContractError(
            f"line {line_no}: external_id, text, event_date, and source are required"
        )
    if external_id.startswith("example:"):
        raise MemoryContractError(f"line {line_no}: skip example rows (external_id={external_id})")

    infer = _parse_bool(row.get("infer"), default=False)
    if not infer:
        validate_fact_text(text)

    metadata: dict[str, Any] = {
        "type": (row.get("type") or "fact").strip() or "fact",
        "source": source,
        "event_date": event_date,
        "namespace": (row.get("namespace") or "public").strip() or "public",
    }
    doc_id = (row.get("source_doc_id") or "").strip()
    if doc_id:
        metadata["source_doc_id"] = doc_id
    status = (row.get("status") or "").strip()
    if status:
        metadata["status"] = status
    ventures_raw = (row.get("ventures") or "").strip()
    if ventures_raw:
        metadata["ventures"] = [v.strip() for v in ventures_raw.split(",") if v.strip()]

    return {
        "external_id": external_id,
        "text": text,
        "metadata": metadata,
        "infer": infer,
    }


def csv_to_facts(path: Path, *, skip_examples: bool = True) -> list[dict[str, Any]]:
    facts: list[dict[str, Any]] = []
    with path.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            raise MemoryContractError("CSV must have a header row")
        missing = [c for c in REQUIRED_COLUMNS if c not in reader.fieldnames]
        if missing:
            raise MemoryContractError(f"CSV missing columns: {missing}")

        for line_no, row in enumerate(reader, start=2):
            if not any((v or "").strip() for v in row.values()):
                continue
            ext = (row.get("external_id") or "").strip()
            if skip_examples and ext.startswith("example:"):
                continue
            facts.append(_row_to_fact(row, line_no=line_no))
    return facts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert reconciled facts CSV to JSON.")
    parser.add_argument(
        "csv_path",
        nargs="?",
        default=str(_SCRIPT_DIR.parent / "data" / "reconciled-facts.csv"),
        help="input CSV (default: data/reconciled-facts.csv)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="output JSON path (default: same basename as CSV with .json)",
    )
    parser.add_argument(
        "--include-examples",
        action="store_true",
        help="do not skip rows whose external_id starts with example:",
    )
    parser.add_argument("--json", action="store_true", dest="json_out", help="print JSON to stdout")
    args = parser.parse_args(argv)

    csv_path = Path(args.csv_path)
    if not csv_path.is_file():
        print(f"ERROR: CSV not found: {csv_path}", file=sys.stderr)
        return 2

    try:
        facts = csv_to_facts(csv_path, skip_examples=not args.include_examples)
    except MemoryContractError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    payload = {"facts": facts}
    if args.json_out:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    out_path = Path(args.output) if args.output else csv_path.with_suffix(".json")
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(facts)} fact(s) to {out_path}")
    print("Next: python scripts/bulk_seed_importer.py", out_path, "--dry-run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
