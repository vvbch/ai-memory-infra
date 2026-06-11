from __future__ import annotations

from typing import Any

from memory.retrieval import (
    latest_by_event_date,
    record_text,
    search_with_contract,
)


def test_latest_by_event_date_ignores_write_order() -> None:
    records = [
        {
            "memory": "cancelled",
            "metadata": {"event_date": "2026-05-15"},
            "created_at": "2026-06-11T12:00:00Z",
        },
        {
            "memory": "implementation started",
            "metadata": {"event_date": "2026-06-10"},
            "created_at": "2026-06-10T08:00:00Z",
        },
        {
            "memory": "planning",
            "metadata": {"event_date": "2026-06-01"},
        },
    ]
    latest = latest_by_event_date(records)
    assert latest is not None
    assert record_text(latest) == "implementation started"


class _PrefixIsolationClient:
    def __init__(self) -> None:
        self.memories: list[dict[str, Any]] = [
            {
                "id": "adr-1",
                "memory": "ADR 034: Remote MCP HTTP endpoint",
                "metadata": {"external_id": "adr:034", "namespace": "public"},
            },
            {
                "id": "probe-1",
                "memory": "Project Alpha status: implementation started",
                "metadata": {
                    "external_id": "probe:acceptance:alpha-impl",
                    "event_date": "2026-06-10",
                    "namespace": "public",
                },
            },
        ]

    def search_memories(
        self,
        query: str,
        *,
        user_id: str | None = None,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        del query, user_id, filters
        return {"results": self.memories[:top_k]}

    def list_memories(self, *, user_id: str | None = None, limit: int | None = None) -> Any:
        del user_id, limit
        return list(self.memories)


def test_search_with_contract_external_id_prefix_ignores_corpus_noise() -> None:
    client = _PrefixIsolationClient()
    hits = search_with_contract(
        client,
        "Project Alpha status",
        namespace="public",
        external_id_prefix="probe:acceptance:",
        external_ids=["probe:acceptance:alpha-impl"],
    )
    assert len(hits) == 1
    assert hits[0]["id"] == "probe-1"
