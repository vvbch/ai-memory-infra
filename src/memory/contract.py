"""Fact metadata contract (ADR 037 §6)."""

from __future__ import annotations

import datetime as _dt
import re
from typing import Any

TYPE_FACT = "fact"
EXTERNAL_ID_KEY = "external_id"
EVENT_DATE_KEY = "event_date"
OCCURRED_AT_KEY = "occurred_at"

DEFAULT_NAMESPACE = "public"
VALID_NAMESPACES = frozenset({"public", "sensitive"})

VALID_SOURCES = frozenset(
    {
        "cursor-repo",
        "chatgpt",
        "perplexity",
        "claude",
        "manual",
        "mcp",
        "extension",
    }
)

# Legacy write surfaces map to canonical source tags.
_SOURCE_ALIASES = {
    "cursor": "cursor-repo",
}

# Entity names that require inline qualification (comma-disambiguation pattern).
_COLLIDING_ENTITIES = frozenset({"Krishna"})


class MemoryContractError(ValueError):
    """Raised when a write would violate the memory metadata contract."""


def event_date_of(meta: dict[str, Any]) -> str | None:
    """Return canonical event time from metadata (event_date preferred over occurred_at)."""
    value = meta.get(EVENT_DATE_KEY) or meta.get(OCCURRED_AT_KEY)
    return str(value)[:10] if value else None


def normalize_source(source: str) -> str:
    """Map legacy source tags to the canonical enum."""
    trimmed = source.strip()
    return _SOURCE_ALIASES.get(trimmed, trimmed)


def validate_event_date(value: str, *, label: str = EVENT_DATE_KEY) -> str:
    try:
        parsed = _dt.date.fromisoformat(str(value)[:10])
    except ValueError as exc:
        raise MemoryContractError(
            f"{label} must be an ISO date (YYYY-MM-DD), got {value!r}"
        ) from exc
    return parsed.isoformat()


def validate_source(source: str) -> str:
    canonical = normalize_source(source)
    if canonical not in VALID_SOURCES:
        raise MemoryContractError(
            f"source must be one of {sorted(VALID_SOURCES)}, got {source!r}"
        )
    return canonical


def validate_namespace(namespace: str | None) -> str:
    value = (namespace or DEFAULT_NAMESPACE).strip()
    if value not in VALID_NAMESPACES:
        raise MemoryContractError(
            f"namespace must be one of {sorted(VALID_NAMESPACES)}, got {namespace!r}"
        )
    return value


def validate_fact_text(text: str) -> None:
    """Reject bare colliding entity tokens in authored fact text."""
    stripped = text.strip()
    if not stripped:
        raise MemoryContractError("fact text must not be empty")
    for entity in _COLLIDING_ENTITIES:
        if re.search(rf"\b{re.escape(entity)}\b", stripped) and f"{entity}," not in stripped:
            raise MemoryContractError(
                f"fact text must qualify '{entity}' inline (e.g. "
                f"'{entity}, <disambiguator>') — bare tokens collide"
            )


def _clean(metadata: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in metadata.items() if v not in (None, "", [])}


def build_fact_metadata(
    *,
    event_date: str,
    source: str,
    source_doc_id: str | None = None,
    namespace: str | None = None,
    external_id: str | None = None,
    ventures: list[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build contract-correct fact metadata with event_date + occurred_at dual-write."""
    validated_date = validate_event_date(event_date)
    meta = _clean(
        {
            "type": TYPE_FACT,
            "source": validate_source(source),
            EVENT_DATE_KEY: validated_date,
            OCCURRED_AT_KEY: validated_date,
            "source_doc_id": source_doc_id,
            "namespace": validate_namespace(namespace),
            EXTERNAL_ID_KEY: external_id,
            "ventures": list(ventures or []),
        }
    )
    if extra:
        meta.update(_clean(extra))
    return meta


def validate_fact_metadata(metadata: dict[str, Any], *, require_external_id: bool = False) -> None:
    """Validate metadata on bulk/probe writes."""
    mem_type = metadata.get("type", TYPE_FACT)
    if mem_type not in {TYPE_FACT, "open_item"}:
        raise MemoryContractError(
            f"metadata.type must be 'fact' or 'open_item', got {mem_type!r}"
        )
    event_date = metadata.get(EVENT_DATE_KEY) or metadata.get(OCCURRED_AT_KEY)
    if not event_date:
        raise MemoryContractError(f"metadata must include {EVENT_DATE_KEY}")
    validate_event_date(str(event_date))
    source = metadata.get("source")
    if not source:
        raise MemoryContractError("metadata must include source")
    validate_source(str(source))
    validate_namespace(metadata.get("namespace"))
    if require_external_id and not metadata.get(EXTERNAL_ID_KEY):
        raise MemoryContractError(f"metadata must include {EXTERNAL_ID_KEY}")
