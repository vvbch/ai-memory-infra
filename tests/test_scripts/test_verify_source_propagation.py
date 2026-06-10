"""Tests for scripts/verify_source_propagation.py (ADR 028 live probe helper)."""

from __future__ import annotations

import importlib.util
import json
import pathlib
import sys
from typing import Any

import httpx
import pytest

_SCRIPT = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "verify_source_propagation.py"
_spec = importlib.util.spec_from_file_location("verify_source_propagation", _SCRIPT)
assert _spec and _spec.loader
vsp = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = vsp
_spec.loader.exec_module(vsp)

from mcp_proxy.client import MemoryApiClient, MemoryApiConfig  # noqa: E402


def _client(handler: Any) -> MemoryApiClient:
    return MemoryApiClient(
        MemoryApiConfig(base_url="https://memory.test", api_key="k", user_id="chandrav"),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_run_probe_pgvector_source_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET" and "/memories/probe-1" in str(request.url):
            return httpx.Response(
                200,
                json={
                    "id": "probe-1",
                    "memory": "probe",
                    "metadata": {"type": "fact", "source": "neo4j-probe"},
                },
            )
        raise AssertionError(f"unexpected request: {request.method} {request.url}")

    monkeypatch.setattr(vsp, "_neo4j_node_count_ssh", lambda *a, **k: 0)

    result = vsp.run_probe(
        client=_client(handler),
        memory_id="probe-1",
        source="neo4j-probe",
    )
    assert result.pgvector_ok is True
    assert result.neo4j_node_count == 0
    assert result.neo4j_ok is True


def test_run_probe_pgvector_source_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"id": "probe-1", "memory": "x", "metadata": {"source": "wrong"}},
        )

    monkeypatch.setattr(vsp, "_neo4j_node_count_ssh", lambda *a, **k: 0)

    result = vsp.run_probe(client=_client(handler), memory_id="probe-1")
    assert result.pgvector_ok is False


def test_write_probe_returns_id() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={"results": [{"id": "new-id", "event": "ADD"}]},
        )

    mid = vsp._write_probe(_client(handler), text="t", source="neo4j-probe")
    assert mid == "new-id"
    assert captured["body"]["metadata"]["source"] == "neo4j-probe"
    assert captured["body"]["infer"] is False


def test_main_json_exit_code(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = vsp.ProbeResult(
        memory_id="x",
        expected_source="neo4j-probe",
        pgvector_source="neo4j-probe",
        pgvector_ok=True,
        neo4j_node_count=0,
        neo4j_ok=True,
        messages=["ok"],
    )
    monkeypatch.setattr(vsp, "MemoryApiClient", lambda *a, **k: object())
    fake_config = type("C", (), {"from_env": staticmethod(lambda: object())})
    monkeypatch.setattr(vsp, "MemoryApiConfig", fake_config)
    monkeypatch.setattr(vsp, "run_probe", lambda **k: fake)
    assert vsp.main(["--json", "--no-ssh"]) == 0
