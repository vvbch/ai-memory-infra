"""Tests for the remote Streamable HTTP MCP entrypoint (ADR 034).

The bearer gate is the security boundary for the public `mcp.` subdomain:
every MCP request must carry `Authorization: Bearer <MCP_CONNECTOR_BEARER_TOKEN>`.
Only `/health` (used by container/Caddy probes) is reachable without it.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from starlette.testclient import TestClient

from mcp_proxy import http_server

TOKEN = "test-bearer-token"

# A minimal MCP initialize request — proves an authorized call reaches the real
# Streamable HTTP transport underneath the gate.
INITIALIZE_PAYLOAD = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-03-26",
        "capabilities": {},
        "clientInfo": {"name": "pytest", "version": "0"},
    },
}
MCP_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}


@pytest.fixture(scope="module")
def client() -> Iterator[TestClient]:
    # One app + one lifespan for the whole module: the MCP session manager can
    # only be started once per process.
    app = http_server.build_app(TOKEN, allowed_hosts=["testserver"])
    with TestClient(app) as test_client:
        yield test_client


def test_missing_bearer_is_rejected(client: TestClient) -> None:
    response = client.post("/", json=INITIALIZE_PAYLOAD, headers=MCP_HEADERS)
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_wrong_bearer_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/",
        json=INITIALIZE_PAYLOAD,
        headers={**MCP_HEADERS, "Authorization": "Bearer wrong-token"},
    )
    assert response.status_code == 401


def test_non_bearer_scheme_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/",
        json=INITIALIZE_PAYLOAD,
        headers={**MCP_HEADERS, "Authorization": f"Basic {TOKEN}"},
    )
    assert response.status_code == 401


def test_health_is_open(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_valid_bearer_reaches_mcp_transport(client: TestClient) -> None:
    response = client.post(
        "/",
        json=INITIALIZE_PAYLOAD,
        headers={**MCP_HEADERS, "Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 200


def test_main_requires_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MCP_CONNECTOR_BEARER_TOKEN", raising=False)
    with pytest.raises(SystemExit):
        http_server.main()
