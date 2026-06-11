from __future__ import annotations

import importlib.util
import pathlib
from typing import Any

_ACCEPTANCE = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "acceptance_probe.py"
_spec = importlib.util.spec_from_file_location("acceptance_probe", _ACCEPTANCE)
assert _spec and _spec.loader
acceptance_probe = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(acceptance_probe)


class FakeClient:
    def __init__(self) -> None:
        self.memories: list[dict[str, Any]] = [
            {
                "id": "a1",
                "memory": "Project Alpha status: cancelled",
                "metadata": {
                    "external_id": "probe:acceptance:alpha-cancel",
                    "event_date": "2026-05-15",
                    "namespace": "public",
                },
            },
            {
                "id": "a2",
                "memory": "Project Alpha status: implementation started",
                "metadata": {
                    "external_id": "probe:acceptance:alpha-impl",
                    "event_date": "2026-06-10",
                    "namespace": "public",
                },
            },
            {
                "id": "o1",
                "memory": "Follow up with Krishna, interview-prep contact, about mock",
                "metadata": {
                    "external_id": "probe:acceptance:open-item",
                    "type": "open_item",
                    "status": "open",
                    "namespace": "public",
                },
            },
            {
                "id": "k1",
                "memory": "Krishna, Chandra's elder son, started camp",
                "metadata": {"namespace": "public"},
            },
            {
                "id": "k2",
                "memory": "Krishna, interview-prep contact, scheduled mock",
                "metadata": {"namespace": "public"},
            },
        ]
        self.deleted: list[str] = []

    def search_memories(
        self,
        query: str,
        *,
        user_id: str | None = None,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        hits = self.memories
        if filters:
            hits = [
                m
                for m in hits
                if all((m.get("metadata") or {}).get(k) == v for k, v in filters.items())
            ]
        if "Project Alpha" in query:
            hits = [m for m in hits if "Project Alpha" in m["memory"]]
        if "Krishna" in query:
            hits = [m for m in hits if "Krishna" in m["memory"]]
            if "interview-prep" in query:
                hits = [m for m in hits if "interview-prep contact" in m["memory"]]
        return {"results": hits[:top_k]}

    def list_memories(self, *, user_id: str | None = None, limit: int | None = None) -> Any:
        return list(self.memories)

    def delete_memory(self, memory_id: str) -> dict[str, Any]:
        self.deleted.append(memory_id)
        self.memories = [m for m in self.memories if m["id"] != memory_id]
        return {"message": "deleted"}


def test_backdated_recency_query_passes() -> None:
    client = FakeClient()
    result = acceptance_probe.query_backdated_recency(client, None)
    assert result["passed"] is True


def test_structured_filter_query_passes() -> None:
    client = FakeClient()
    result = acceptance_probe.query_structured_filter(client, None)
    assert result["passed"] is True


def test_entity_collision_query_passes() -> None:
    client = FakeClient()
    result = acceptance_probe.query_entity_collision(client, None)
    assert result["passed"] is True
    assert "interview-prep contact" in result["best_krishna_text"]
