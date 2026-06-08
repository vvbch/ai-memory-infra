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
        user_id: str | None,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        self.calls.append(("add", {"text": text, "user_id": user_id, "metadata": metadata}))
        return {"message": "ok"}

    def list_memories(self, *, user_id: str | None) -> list[dict[str, str]]:
        self.calls.append(("list", {"user_id": user_id}))
        return [{"memory": "hello"}]


def test_search_memories_tool_delegates(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeClient()
    monkeypatch.setattr(server, "_client", lambda: fake)

    assert server.search_memories("hello", top_k=2, user_id="u1") == {"results": []}
    assert fake.calls == [("search", {"query": "hello", "top_k": 2, "user_id": "u1"})]


def test_add_memory_tool_adds_source_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeClient()
    monkeypatch.setattr(server, "_client", lambda: fake)

    assert server.add_memory("remember me", user_id="u1") == {"message": "ok"}
    assert fake.calls == [
        ("add", {"text": "remember me", "user_id": "u1", "metadata": {"source": "mcp"}})
    ]


def test_list_memories_tool_delegates(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeClient()
    monkeypatch.setattr(server, "_client", lambda: fake)

    assert server.list_memories(user_id="u1") == [{"memory": "hello"}]
    assert fake.calls == [("list", {"user_id": "u1"})]
