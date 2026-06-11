"""Shared memory write/read contract helpers (ADR 037)."""

from memory.contract import (
    DEFAULT_NAMESPACE,
    EXTERNAL_ID_KEY,
    VALID_NAMESPACES,
    VALID_SOURCES,
    build_fact_metadata,
    event_date_of,
    normalize_source,
    validate_event_date,
    validate_fact_metadata,
    validate_fact_text,
    validate_namespace,
    validate_source,
)
from memory.retrieval import (
    latest_by_event_date,
    open_follow_ups,
    record_id,
    record_metadata,
    record_text,
    search_with_contract,
)

__all__ = [
    "DEFAULT_NAMESPACE",
    "EXTERNAL_ID_KEY",
    "VALID_NAMESPACES",
    "VALID_SOURCES",
    "build_fact_metadata",
    "event_date_of",
    "latest_by_event_date",
    "normalize_source",
    "open_follow_ups",
    "record_id",
    "record_metadata",
    "record_text",
    "search_with_contract",
    "validate_event_date",
    "validate_fact_metadata",
    "validate_fact_text",
    "validate_namespace",
    "validate_source",
]
