"""Drop migration facts already present in the memory bank (Phase 5)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from memory.contract import EXTERNAL_ID_KEY
from memory.retrieval import record_metadata, record_text


@dataclass(frozen=True)
class BankIndex:
    """Known external_ids and normalized texts from existing bank records."""

    external_ids: frozenset[str]
    normalized_texts: frozenset[str]


@dataclass(frozen=True)
class DroppedFact:
    fact: dict[str, Any]
    reason: str


@dataclass(frozen=True)
class DedupResult:
    kept: list[dict[str, Any]]
    dropped: list[DroppedFact]


def normalize_text(text: str) -> str:
    """Collapse whitespace and case for duplicate detection."""
    return " ".join(text.strip().split()).casefold()


def build_bank_index(records: list[dict[str, Any]]) -> BankIndex:
    """Index external_ids and normalized text from live bank records."""
    external_ids: set[str] = set()
    normalized_texts: set[str] = set()
    for rec in records:
        meta = record_metadata(rec)
        external_id = meta.get(EXTERNAL_ID_KEY) or rec.get(EXTERNAL_ID_KEY)
        if external_id:
            external_ids.add(str(external_id))
        body = record_text(rec)
        if body.strip():
            normalized_texts.add(normalize_text(body))
    return BankIndex(
        external_ids=frozenset(external_ids),
        normalized_texts=frozenset(normalized_texts),
    )


def _fact_external_id(fact: dict[str, Any]) -> str:
    meta = fact.get("metadata")
    if isinstance(meta, dict) and meta.get(EXTERNAL_ID_KEY):
        return str(meta[EXTERNAL_ID_KEY])
    return str(fact.get(EXTERNAL_ID_KEY) or "")


def _duplicate_reason(
    fact: dict[str, Any],
    index: BankIndex,
) -> str | None:
    external_id = _fact_external_id(fact)
    if external_id and external_id in index.external_ids:
        return "external_id"
    text = str(fact.get("text") or "")
    if text.strip():
        normalized = normalize_text(text)
        if normalized in index.normalized_texts:
            return "text"
    return None


def _with_fact(index: BankIndex, fact: dict[str, Any]) -> BankIndex:
    external_id = _fact_external_id(fact)
    external_ids = set(index.external_ids)
    normalized_texts = set(index.normalized_texts)
    if external_id:
        external_ids.add(external_id)
    text = str(fact.get("text") or "")
    if text.strip():
        normalized_texts.add(normalize_text(text))
    return BankIndex(
        external_ids=frozenset(external_ids),
        normalized_texts=frozenset(normalized_texts),
    )


def filter_new_facts(
    facts: list[dict[str, Any]],
    bank_records: list[dict[str, Any]],
) -> DedupResult:
    """Return facts not already in the bank by external_id or normalized text."""
    index = build_bank_index(bank_records)
    kept: list[dict[str, Any]] = []
    dropped: list[DroppedFact] = []

    for fact in facts:
        reason = _duplicate_reason(fact, index)
        if reason:
            dropped.append(DroppedFact(fact=fact, reason=reason))
            continue
        kept.append(fact)
        index = _with_fact(index, fact)

    return DedupResult(kept=kept, dropped=dropped)


def dedup_facts(
    facts: list[dict[str, Any]],
    bank_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Convenience wrapper returning only facts to import."""
    return filter_new_facts(facts, bank_records).kept
