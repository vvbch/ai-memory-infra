from __future__ import annotations

import pytest

from memory.contract import (
    MemoryContractError,
    build_fact_metadata,
    event_date_of,
    validate_fact_text,
)


def test_event_date_of_prefers_event_date() -> None:
    assert event_date_of({"event_date": "2026-06-10", "occurred_at": "2026-01-01"}) == "2026-06-10"


def test_event_date_of_falls_back_to_occurred_at() -> None:
    assert event_date_of({"occurred_at": "2026-01-01"}) == "2026-01-01"


def test_build_fact_metadata_dual_writes_dates() -> None:
    meta = build_fact_metadata(
        event_date="2026-06-01",
        source="manual",
        namespace="public",
        external_id="probe:test",
    )
    assert meta["event_date"] == "2026-06-01"
    assert meta["occurred_at"] == "2026-06-01"
    assert meta["source"] == "manual"
    assert meta["namespace"] == "public"


def test_validate_fact_text_rejects_bare_jordan() -> None:
    with pytest.raises(MemoryContractError, match="qualify"):
        validate_fact_text("Jordan called today")


def test_validate_fact_text_allows_qualified_jordan() -> None:
    validate_fact_text("Jordan, project contact, scheduled a call")
