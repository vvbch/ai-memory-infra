from __future__ import annotations

import importlib.util
import pathlib
from typing import Any

import httpx
import pytest

_IMPORTER = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "bulk_seed_importer.py"
_spec = importlib.util.spec_from_file_location("bulk_seed_importer", _IMPORTER)
assert _spec and _spec.loader
bulk_seed_importer = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bulk_seed_importer)
import_facts = bulk_seed_importer.import_facts

from mcp_proxy.idempotent_write import find_by_external_id  # noqa: E402


class FakeClient:
    def __init__(self, memories: list[dict[str, Any]] | None = None) -> None:
        self.memories = list(memories or [])
        self.writes: list[dict[str, Any]] = []

    def list_memories(self, *, user_id: str | None = None, limit: int | None = None) -> Any:
        return list(self.memories)

    def search_memories(
        self,
        query: str,
        *,
        user_id: str | None = None,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        ext = (filters or {}).get("external_id")
        hits = [
            m
            for m in self.memories
            if (m.get("metadata") or {}).get("external_id") == ext
        ]
        return {"results": hits[:top_k]}

    def add_memory(
        self,
        text: str,
        *,
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        infer: bool = True,
    ) -> dict[str, Any]:
        if metadata and metadata.get("external_id") == "timeout-case":
            raise httpx.ReadTimeout("slow extraction")
        self.writes.append({"text": text, "metadata": metadata, "infer": infer})
        mid = f"id-{len(self.memories) + 1}"
        rec = {"id": mid, "memory": text, "metadata": metadata or {}}
        self.memories.append(rec)
        return {"results": [{"event": "ADD", "id": mid}]}


def _fact(**overrides: Any) -> dict[str, Any]:
    base = {
        "external_id": "seed:test",
        "text": "Qualified Jordan, project contact, is a contact.",
        "metadata": {
            "type": "fact",
            "source": "cursor-repo",
            "event_date": "2026-06-01",
            "namespace": "public",
        },
        "infer": False,
    }
    base.update(overrides)
    return base


def test_skips_existing_external_id() -> None:
    client = FakeClient(
        [{"id": "m1", "memory": "hello", "metadata": {"external_id": "seed:a"}}]
    )
    outcomes = import_facts(
        client,
        [_fact(external_id="seed:a", text="hello again")],
    )
    assert outcomes == [
        {"external_id": "seed:a", "status": "skipped_exists", "memory_id": "m1"}
    ]
    assert client.writes == []


def test_timeout_verifies_then_skips(monkeypatch: pytest.MonkeyPatch) -> None:
    client = FakeClient()
    calls = {"n": 0}

    def delayed_find(*args: Any, **kwargs: Any) -> dict[str, Any] | None:
        calls["n"] += 1
        if calls["n"] == 1:
            return find_by_external_id(*args, **kwargs)
        client.memories.append(
            {
                "id": "late",
                "memory": "landed",
                "metadata": {"external_id": "timeout-case"},
            }
        )
        return client.memories[-1]

    import mcp_proxy.idempotent_write as idem

    monkeypatch.setattr(idem.time, "sleep", lambda _: None)
    monkeypatch.setattr(idem, "find_by_external_id", delayed_find)

    outcomes = import_facts(
        client,
        [_fact(external_id="timeout-case", text="payload")],
        verify_window_s=1.0,
        verify_interval_s=0.01,
    )
    assert outcomes[0]["status"] == "verified_after_timeout"
    assert outcomes[0]["memory_id"] == "late"


def test_find_by_external_id_scans_cache() -> None:
    client = FakeClient(
        [{"id": "m1", "memory": "x", "metadata": {"external_id": "seed:b"}}]
    )
    found = find_by_external_id(client, "seed:b", cache=client.memories)
    assert found is not None
    assert found["id"] == "m1"


def test_rejects_missing_event_date() -> None:
    client = FakeClient()
    outcomes = import_facts(
        client,
        [
            {
                "external_id": "seed:bad",
                "text": "no date",
                "metadata": {"source": "manual"},
            }
        ],
    )
    assert outcomes[0]["status"] == "invalid"


def test_writes_append_cache_without_relisting() -> None:
    client = FakeClient()
    list_calls = 0
    orig_list = client.list_memories

    def counting_list(*args: Any, **kwargs: Any) -> Any:
        nonlocal list_calls
        list_calls += 1
        return orig_list(*args, **kwargs)

    client.list_memories = counting_list  # type: ignore[method-assign]

    facts = [
        _fact(external_id="seed:1", text="first"),
        _fact(external_id="seed:2", text="second"),
        _fact(external_id="seed:3", text="third"),
    ]
    outcomes = import_facts(client, facts)

    assert list_calls == 1
    assert len(client.writes) == 3
    assert all(o["status"] == "written" for o in outcomes)
    assert find_by_external_id(client, "seed:3", cache=client.memories) is not None
