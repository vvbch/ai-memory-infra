from __future__ import annotations

from typing import Any

import pytest

from mcp_proxy import server


class FakeClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def search_memories(
        self,
        query: str,
        *,
        top_k: int,
        user_id: str | None,
    ) -> dict[str, Any]:
        self.calls.append(("search", {"query": query, "top_k": top_k, "user_id": user_id}))
        return {"results": []}

    def add_memory(
        self,
        text: str,
        *,
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        infer: bool = True,
    ) -> dict[str, Any]:
        self.calls.append(
            ("add", {"text": text, "user_id": user_id, "metadata": metadata, "infer": infer})
        )
        return {"message": "ok"}

    def add_memory_idempotent(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return self.add_memory(*args, **kwargs)

    def list_memories(self, *, user_id: str | None) -> list[dict[str, str]]:
        self.calls.append(("list", {"user_id": user_id}))
        return [{"memory": "hello"}]

    def delete_memory(self, memory_id: str) -> dict[str, str]:
        self.calls.append(("delete", {"memory_id": memory_id}))
        return {"message": "deleted"}

    def update_memory(
        self,
        memory_id: str,
        text: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, str]:
        self.calls.append(
            ("update", {"memory_id": memory_id, "text": text, "metadata": metadata})
        )
        return {"message": "updated"}


def test_search_memories_tool_delegates(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeClient()
    monkeypatch.setattr(server, "_client", lambda: fake)

    assert server.search_memories("hello", top_k=2, user_id="u1") == {"results": []}
    assert fake.calls == [("search", {"query": "hello", "top_k": 2, "user_id": "u1"})]


def test_add_memory_tool_adds_source_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeClient()
    monkeypatch.setattr(server, "_client", lambda: fake)

    assert server.add_memory("remember me", user_id="u1") == {"message": "ok"}
    meta = fake.calls[0][1]["metadata"]
    assert meta["source"] == "mcp"
    assert meta["namespace"] == "public"
    assert meta["type"] == "fact"
    assert meta["event_date"] == meta["occurred_at"]


def test_list_memories_tool_delegates(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeClient()
    monkeypatch.setattr(server, "_client", lambda: fake)

    assert server.list_memories(user_id="u1") == [{"memory": "hello"}]
    assert fake.calls == [("list", {"user_id": "u1"})]


def test_delete_memory_tool_delegates(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeClient()
    monkeypatch.setattr(server, "_client", lambda: fake)

    assert server.delete_memory("m1") == {"message": "deleted"}
    assert fake.calls == [("delete", {"memory_id": "m1"})]


def test_update_memory_tool_delegates(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeClient()
    monkeypatch.setattr(server, "_client", lambda: fake)

    assert server.update_memory("m1", "revised") == {"message": "updated"}
    assert fake.calls == [
        ("update", {"memory_id": "m1", "text": "revised", "metadata": None})
    ]
