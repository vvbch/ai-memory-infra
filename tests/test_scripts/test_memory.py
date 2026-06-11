"""Tests for the Memory Daily Driver v0 helper (scripts/memory.py).

Uses a real ``MemoryApiClient`` wired to an httpx MockTransport so the helper +
client are exercised together against a simulated live API (matching the proven
Phase 0 request/response shapes).
"""

from __future__ import annotations

import datetime as _dt
import importlib.util
import json
import pathlib
from typing import Any

import httpx
import pytest

_MEMORY_PY = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "memory.py"
_spec = importlib.util.spec_from_file_location("memory_helper", _MEMORY_PY)
assert _spec and _spec.loader
memory = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(memory)

from mcp_proxy.client import MemoryApiClient, MemoryApiConfig  # noqa: E402


def _client(handler: Any) -> MemoryApiClient:
    return MemoryApiClient(
        MemoryApiConfig(base_url="https://memory.test", api_key="k", user_id="primary-user"),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


def _record(text: str, **meta: Any) -> dict[str, Any]:
    return {"id": meta.pop("id", "abc123"), "memory": text, "metadata": meta}


# --------------------------------------------------------------------------- #
# Capture writes.
# --------------------------------------------------------------------------- #
def test_capture_open_item_sends_contract_metadata_and_infer_false() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"results": [{"event": "ADD"}]})

    memory.capture_open_item(
        _client(handler),
        "Follow up with recruiter Acme Corp",
        due_at="2026-06-12",
        revisit_at="2026-06-11",
        ventures=["career"],
    )

    body = captured["body"]
    assert body["infer"] is False
    assert body["user_id"] == "primary-user"
    assert body["metadata"] == {
        "type": "open_item",
        "status": "open",
        "source": "cursor-repo",
        "due_at": "2026-06-12",
        "revisit_at": "2026-06-11",
        "ventures": ["career"],
    }


def test_capture_fact_defaults_to_verbatim() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"results": []})

    memory.capture_fact(_client(handler), "Prefers Python over shell")
    assert captured["body"]["infer"] is False
    assert captured["body"]["metadata"]["type"] == "fact"


def test_capture_rejects_unknown_venture() -> None:
    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover - not reached
        return httpx.Response(200, json={})

    with pytest.raises(memory.MemoryContractError):
        memory.capture_open_item(_client(handler), "x", ventures=["not_a_venture"])


def test_capture_rejects_bad_date() -> None:
    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover - not reached
        return httpx.Response(200, json={})

    with pytest.raises(memory.MemoryContractError):
        memory.capture_open_item(_client(handler), "x", due_at="next tuesday")


# --------------------------------------------------------------------------- #
# Reads: agenda bucketing + recruiter board.
# --------------------------------------------------------------------------- #
def test_agenda_buckets_by_date_client_side() -> None:
    records = [
        _record("overdue one", id="1", type="open_item", status="open", due_at="2026-06-01"),
        _record("due today", id="2", type="open_item", status="open", due_at="2026-06-09"),
        _record("revisit now", id="3", type="open_item", status="open", revisit_at="2026-06-08"),
        _record("future", id="4", type="open_item", status="open", due_at="2026-07-01"),
        _record("no date", id="5", type="open_item", status="in_progress"),
        _record("done one", id="6", type="open_item", status="done"),
        _record("just a fact", id="7", type="fact"),
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"results": records})

    data = memory.agenda(_client(handler), today=_dt.date(2026, 6, 9))

    assert [it["id"] for it in data["overdue"]] == ["1"]
    assert [it["id"] for it in data["due_today"]] == ["2"]
    assert [it["id"] for it in data["revisit_due"]] == ["3"]
    assert [it["id"] for it in data["upcoming"]] == ["4"]
    assert [it["id"] for it in data["undated"]] == ["5"]


def test_recruiter_board_filters_career_open_items() -> None:
    records = [
        _record("recruiter A", id="1", type="open_item", status="open", ventures=["career"]),
        _record("trading task", id="2", type="open_item", status="open", ventures=["trading_firm"]),
        _record("recruiter B closed", id="3", type="open_item", status="done", ventures=["career"]),
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"results": records})

    board = memory.recruiter_board(_client(handler))
    assert [it["id"] for it in board] == ["1"]


# --------------------------------------------------------------------------- #
# Close: GET current record, PUT merged closure metadata in place.
# --------------------------------------------------------------------------- #
def test_close_item_merges_closure_fields_and_keeps_existing_metadata() -> None:
    calls: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return httpx.Response(
                200,
                json=_record(
                    "Follow up with recruiter Acme Corp",
                    id="m1",
                    type="open_item",
                    status="open",
                    source="cursor",
                    due_at="2026-06-12",
                    ventures=["career"],
                ),
            )
        if request.method == "PUT":
            calls["put_body"] = json.loads(request.content)
            calls["put_url"] = str(request.url)
            return httpx.Response(200, json={"message": "updated"})
        raise AssertionError(f"unexpected method {request.method}")

    result = memory.close_item(
        _client(handler), "m1", "Recruiter passed; reapply Q3", closed_at="2026-06-09"
    )

    assert result == {"message": "updated"}
    assert calls["put_url"].endswith("/memories/m1")
    assert calls["put_body"]["text"] == "Follow up with recruiter Acme Corp"
    assert calls["put_body"]["metadata"] == {
        "type": "open_item",
        "status": "done",
        "source": "cursor",
        "due_at": "2026-06-12",
        "ventures": ["career"],
        "resolution": "Recruiter passed; reapply Q3",
        "closed_at": "2026-06-09",
    }


def test_close_item_requires_resolution() -> None:
    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover - not reached
        return httpx.Response(200, json={})

    with pytest.raises(memory.MemoryContractError):
        memory.close_item(_client(handler), "m1", "   ")
