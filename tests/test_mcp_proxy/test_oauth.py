"""Tests for the minimal self-hosted OAuth layer on the remote MCP endpoint (ADR 035).

claude.ai custom connectors only speak OAuth 2.1 (DCR + PKCE S256). These tests
drive the full flow exactly as Claude does: discovery → dynamic client
registration → /authorize → operator consent → /token (PKCE) → authorized MCP
call — plus the failure paths that make the flow safe (wrong consent secret,
wrong PKCE verifier, code reuse, expired/garbage tokens) and the persistence
property that tokens survive a container restart.
"""

from __future__ import annotations

import base64
import hashlib
import json
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import pytest
from starlette.testclient import TestClient

from mcp_proxy import http_server
from mcp_proxy.oauth import OAuthStateStore

SECRET = "test-consent-secret"
ISSUER = "http://localhost"
CALLBACK = "https://claude.ai/api/mcp/auth_callback"

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

REDIRECT_CODES = {302, 303, 307}


@pytest.fixture()
def state_path(tmp_path: Path) -> Path:
    return tmp_path / "oauth_state.json"


@pytest.fixture()
def client(state_path: Path) -> Iterator[TestClient]:
    app = http_server.build_app(
        SECRET,
        allowed_hosts=["testserver"],
        issuer=ISSUER,
        state_path=state_path,
    )
    with TestClient(app) as test_client:
        yield test_client


def register_client(client: TestClient) -> dict[str, Any]:
    response = client.post(
        "/register",
        json={
            "redirect_uris": [CALLBACK],
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "token_endpoint_auth_method": "none",
            "client_name": "Claude",
        },
    )
    assert response.status_code == 201
    body: dict[str, Any] = response.json()
    assert body["client_id"]
    return body


def pkce_pair() -> tuple[str, str]:
    verifier = "pytest-verifier-" + "v" * 43
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).decode().rstrip("=")
    return verifier, challenge


def start_authorize(
    client: TestClient, client_id: str, challenge: str, state: str = "opaque-state"
) -> str:
    response = client.get(
        "/authorize",
        params={
            "client_id": client_id,
            "redirect_uri": CALLBACK,
            "response_type": "code",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": state,
        },
        follow_redirects=False,
    )
    assert response.status_code in REDIRECT_CODES
    return response.headers["location"]


def txn_from(location: str) -> str:
    return parse_qs(urlparse(location).query)["txn"][0]


def approve_consent(client: TestClient, location: str, secret: str = SECRET) -> Any:
    return client.post(
        "/consent",
        data={"txn": txn_from(location), "secret": secret},
        follow_redirects=False,
    )


def obtain_code(client: TestClient, client_id: str, challenge: str) -> str:
    location = start_authorize(client, client_id, challenge)
    response = approve_consent(client, location)
    assert response.status_code in REDIRECT_CODES
    redirect = response.headers["location"]
    assert redirect.startswith(CALLBACK)
    query = parse_qs(urlparse(redirect).query)
    assert query["state"] == ["opaque-state"]
    return query["code"][0]


def exchange_code(client: TestClient, client_id: str, code: str, verifier: str) -> Any:
    return client.post(
        "/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": CALLBACK,
            "client_id": client_id,
            "code_verifier": verifier,
        },
    )


def full_flow(client: TestClient) -> tuple[dict[str, Any], str]:
    info = register_client(client)
    verifier, challenge = pkce_pair()
    code = obtain_code(client, info["client_id"], challenge)
    response = exchange_code(client, info["client_id"], code, verifier)
    assert response.status_code == 200
    tokens: dict[str, Any] = response.json()
    return tokens, info["client_id"]


def mcp_initialize(client: TestClient, token: str) -> Any:
    return client.post(
        "/",
        json=INITIALIZE_PAYLOAD,
        headers={**MCP_HEADERS, "Authorization": f"Bearer {token}"},
    )


# --- discovery ---------------------------------------------------------------


def test_authorization_server_metadata(client: TestClient) -> None:
    response = client.get("/.well-known/oauth-authorization-server")
    assert response.status_code == 200
    metadata = response.json()
    assert metadata["issuer"].rstrip("/") == ISSUER
    assert metadata["code_challenge_methods_supported"] == ["S256"]
    assert metadata["registration_endpoint"].endswith("/register")
    assert metadata["authorization_endpoint"].endswith("/authorize")
    assert metadata["token_endpoint"].endswith("/token")


def test_protected_resource_metadata(client: TestClient) -> None:
    response = client.get("/.well-known/oauth-protected-resource")
    assert response.status_code == 200
    metadata = response.json()
    assert any(server.rstrip("/") == ISSUER for server in metadata["authorization_servers"])


# --- registration + authorize + consent ---------------------------------------


def test_dcr_registration_persists_client(client: TestClient, state_path: Path) -> None:
    info = register_client(client)
    state = json.loads(state_path.read_text())
    assert info["client_id"] in state["clients"]


def test_authorize_redirects_to_consent(client: TestClient) -> None:
    info = register_client(client)
    _, challenge = pkce_pair()
    location = start_authorize(client, info["client_id"], challenge)
    assert "/consent?txn=" in location


def test_consent_page_renders_form(client: TestClient) -> None:
    info = register_client(client)
    _, challenge = pkce_pair()
    location = start_authorize(client, info["client_id"], challenge)
    response = client.get(f"/consent?txn={txn_from(location)}")
    assert response.status_code == 200
    assert "form" in response.text


def test_consent_page_names_requesting_client(client: TestClient) -> None:
    # ADR 036: the page must identify the actual requesting client, not assume Claude.
    response = client.post(
        "/register",
        json={
            "redirect_uris": ["https://www.perplexity.ai/rest/connections/oauth_callback"],
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "token_endpoint_auth_method": "none",
            "client_name": "Perplexity",
        },
    )
    assert response.status_code == 201
    _, challenge = pkce_pair()
    location = client.get(
        "/authorize",
        params={
            "client_id": response.json()["client_id"],
            "redirect_uri": "https://www.perplexity.ai/rest/connections/oauth_callback",
            "response_type": "code",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": "opaque-state",
        },
        follow_redirects=False,
    ).headers["location"]
    page = client.get(f"/consent?txn={txn_from(location)}")
    assert page.status_code == 200
    assert "Perplexity" in page.text


def test_consent_page_escapes_hostile_client_name(client: TestClient) -> None:
    # DCR is open (RFC 7591); client_name is untrusted input on an operator-facing page.
    response = client.post(
        "/register",
        json={
            "redirect_uris": [CALLBACK],
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "token_endpoint_auth_method": "none",
            "client_name": "<script>alert(1)</script>",
        },
    )
    assert response.status_code == 201
    _, challenge = pkce_pair()
    location = start_authorize(client, response.json()["client_id"], challenge)
    page = client.get(f"/consent?txn={txn_from(location)}")
    assert page.status_code == 200
    assert "<script>" not in page.text
    assert "&lt;script&gt;" in page.text


def test_consent_unknown_txn_rejected(client: TestClient) -> None:
    assert client.get("/consent?txn=nonexistent").status_code == 400
    response = client.post(
        "/consent", data={"txn": "nonexistent", "secret": SECRET}, follow_redirects=False
    )
    assert response.status_code == 400


def test_consent_wrong_secret_rejected(client: TestClient) -> None:
    info = register_client(client)
    _, challenge = pkce_pair()
    location = start_authorize(client, info["client_id"], challenge)
    response = approve_consent(client, location, secret="wrong-secret")
    assert response.status_code == 401
    assert "location" not in response.headers


# --- token issuance -----------------------------------------------------------


def test_full_flow_issues_tokens(client: TestClient) -> None:
    tokens, _ = full_flow(client)
    assert tokens["token_type"].lower() == "bearer"
    assert tokens["access_token"]
    assert tokens["refresh_token"]
    assert tokens["expires_in"] == 3600


def test_wrong_pkce_verifier_rejected(client: TestClient) -> None:
    info = register_client(client)
    verifier, challenge = pkce_pair()
    code = obtain_code(client, info["client_id"], challenge)
    response = exchange_code(client, info["client_id"], code, verifier + "-tampered")
    assert response.status_code == 400
    assert response.json()["error"] == "invalid_grant"


def test_authorization_code_is_single_use(client: TestClient) -> None:
    info = register_client(client)
    verifier, challenge = pkce_pair()
    code = obtain_code(client, info["client_id"], challenge)
    assert exchange_code(client, info["client_id"], code, verifier).status_code == 200
    replay = exchange_code(client, info["client_id"], code, verifier)
    assert replay.status_code == 400
    assert replay.json()["error"] == "invalid_grant"


def test_refresh_rotation(client: TestClient) -> None:
    tokens, client_id = full_flow(client)

    def refresh(token: str) -> Any:
        return client.post(
            "/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": token,
                "client_id": client_id,
            },
        )

    first = refresh(tokens["refresh_token"])
    assert first.status_code == 200
    new_tokens = first.json()
    assert new_tokens["access_token"] != tokens["access_token"]
    assert new_tokens["refresh_token"] != tokens["refresh_token"]

    # Old refresh token must be dead after rotation; the new pair must work.
    assert refresh(tokens["refresh_token"]).status_code == 400
    assert mcp_initialize(client, new_tokens["access_token"]).status_code == 200


# --- resource-server enforcement ----------------------------------------------


def test_access_token_reaches_mcp_transport(client: TestClient) -> None:
    tokens, _ = full_flow(client)
    assert mcp_initialize(client, tokens["access_token"]).status_code == 200


def test_static_secret_still_authorizes_mcp(client: TestClient) -> None:
    assert mcp_initialize(client, SECRET).status_code == 200


def test_missing_token_gets_challenge_with_resource_metadata(client: TestClient) -> None:
    response = client.post("/", json=INITIALIZE_PAYLOAD, headers=MCP_HEADERS)
    assert response.status_code == 401
    challenge = response.headers["WWW-Authenticate"]
    assert challenge.startswith("Bearer")
    assert "resource_metadata" in challenge


def test_garbage_token_rejected(client: TestClient) -> None:
    assert mcp_initialize(client, "garbage-token").status_code == 401


def test_expired_access_token_rejected(client: TestClient, state_path: Path) -> None:
    tokens, _ = full_flow(client)
    state = json.loads(state_path.read_text())
    for entry in state["access_tokens"].values():
        entry["expires_at"] = int(time.time()) - 10
    state_path.write_text(json.dumps(state))
    assert mcp_initialize(client, tokens["access_token"]).status_code == 401


# --- persistence --------------------------------------------------------------


def test_tokens_survive_restart(client: TestClient, state_path: Path) -> None:
    tokens, _ = full_flow(client)
    restarted = http_server.build_app(
        SECRET, allowed_hosts=["testserver"], issuer=ISSUER, state_path=state_path
    )
    with TestClient(restarted) as second_client:
        assert mcp_initialize(second_client, tokens["access_token"]).status_code == 200


def test_client_store_is_capped(tmp_path: Path) -> None:
    store = OAuthStateStore(tmp_path / "state.json", max_clients=3)
    for index in range(5):
        store.put("clients", f"client-{index}", {"client_id": f"client-{index}"})
    assert store.get("clients", "client-0") is None
    assert store.get("clients", "client-1") is None
    assert store.get("clients", "client-4") is not None


def test_corrupt_state_file_treated_as_empty(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    path.write_text("{not json")
    store = OAuthStateStore(path)
    assert store.get("clients", "anything") is None
    store.put("clients", "fresh", {"client_id": "fresh"})
    assert store.get("clients", "fresh") == {"client_id": "fresh"}
