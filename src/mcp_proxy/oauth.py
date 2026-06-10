"""Minimal single-user OAuth 2.1 provider for the remote MCP endpoint (ADR 035).

claude.ai custom connectors authenticate only via OAuth (DCR + PKCE S256), so
the endpoint is its own authorization server. Protocol mechanics (discovery
metadata, DCR validation, PKCE verification, redirect-URI checks) come from the
`mcp` SDK's auth framework; this module supplies only the single-user policy:

- a JSON-file state store (clients + hashed codes/tokens) on a Docker volume,
  so connector sessions survive redeploys and the file never holds a usable
  bearer secret;
- an operator consent step where the existing `MCP_CONNECTOR_BEARER_TOKEN`
  acts as the approval password (one secret class, ADR 017/035);
- opaque rotated tokens: access 1 h, refresh 60 d.
"""

from __future__ import annotations

import contextlib
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Any

from mcp.server.auth.provider import (
    AccessToken,
    AuthorizationCode,
    AuthorizationParams,
    OAuthAuthorizationServerProvider,
    RefreshToken,
    construct_redirect_uri,
)
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken
from pydantic import AnyUrl

ACCESS_TOKEN_TTL_SECONDS = 3600  # 1 hour
REFRESH_TOKEN_TTL_SECONDS = 60 * 24 * 3600  # 60 days, rotated on use
AUTH_CODE_TTL_SECONDS = 300
CONSENT_TXN_TTL_SECONDS = 300
DEFAULT_MAX_CLIENTS = 50  # DCR is open per RFC 7591; cap so the file can't grow unboundedly

# client_id reported for requests authorized by the static fallback secret.
STATIC_CLIENT_ID = "static-operator-token"


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _now() -> float:
    return time.time()


class UnknownTransactionError(Exception):
    """Consent transaction id is unknown or has expired."""


class WrongSecretError(Exception):
    """Operator-entered consent secret did not match."""


class OAuthStateStore:
    """Whole-file JSON persistence for OAuth state, read/written per operation.

    Tokens and codes are stored under their SHA-256 hash. Re-reading the file
    on each access keeps a restarted (or concurrently redeployed) container
    consistent at single-user traffic volumes.
    """

    SECTIONS = ("clients", "auth_codes", "access_tokens", "refresh_tokens")

    def __init__(self, path: Path, max_clients: int = DEFAULT_MAX_CLIENTS) -> None:
        self._path = path
        self._max_clients = max_clients

    def _read(self) -> dict[str, dict[str, dict[str, Any]]]:
        try:
            raw = json.loads(self._path.read_text())
        except (OSError, ValueError):
            raw = {}
        return {section: dict(raw.get(section, {})) for section in self.SECTIONS}

    def _write(self, state: dict[str, dict[str, dict[str, Any]]]) -> None:
        now = _now()
        for section in ("auth_codes", "access_tokens", "refresh_tokens"):
            state[section] = {
                key: value
                for key, value in state[section].items()
                if float(value.get("expires_at") or now + 1) > now
            }
        clients = state["clients"]
        while len(clients) > self._max_clients:
            clients.pop(next(iter(clients)))
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(state))
        with contextlib.suppress(OSError):  # chmod is best-effort on non-POSIX hosts
            self._path.chmod(0o600)

    def get(self, section: str, key: str) -> dict[str, Any] | None:
        return self._read()[section].get(key)

    def put(self, section: str, key: str, value: dict[str, Any]) -> None:
        state = self._read()
        state[section][key] = value
        self._write(state)

    def delete(self, section: str, key: str) -> None:
        state = self._read()
        state[section].pop(key, None)
        self._write(state)


@dataclass
class _PendingConsent:
    client_id: str
    params: AuthorizationParams
    expires_at: float


class SingleUserOAuthProvider(
    OAuthAuthorizationServerProvider[AuthorizationCode, RefreshToken, AccessToken]
):
    """OAuth provider for exactly one resource owner: the operator."""

    def __init__(self, store: OAuthStateStore, consent_secret: str, issuer: str) -> None:
        self._store = store
        self._secret = consent_secret
        self._issuer = issuer.rstrip("/")
        self._pending: dict[str, _PendingConsent] = {}

    # --- client registry (DCR) -------------------------------------------------

    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
        data = self._store.get("clients", client_id)
        return OAuthClientInformationFull.model_validate(data) if data else None

    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        assert client_info.client_id is not None  # set by the SDK registration handler
        self._store.put("clients", client_info.client_id, client_info.model_dump(mode="json"))

    # --- authorization + consent -----------------------------------------------

    async def authorize(
        self, client: OAuthClientInformationFull, params: AuthorizationParams
    ) -> str:
        self._prune_pending()
        txn = secrets.token_urlsafe(16)
        assert client.client_id is not None
        self._pending[txn] = _PendingConsent(
            client_id=client.client_id,
            params=params,
            expires_at=_now() + CONSENT_TXN_TTL_SECONDS,
        )
        return f"{self._issuer}/consent?txn={txn}"

    def _prune_pending(self) -> None:
        now = _now()
        for txn in [txn for txn, pending in self._pending.items() if pending.expires_at < now]:
            del self._pending[txn]

    def transaction_exists(self, txn: str) -> bool:
        self._prune_pending()
        return txn in self._pending

    def _client_display_name(self, txn: str) -> str:
        pending = self._pending.get(txn)
        if pending is None:
            return "A connector client"
        client = self._store.get("clients", pending.client_id)
        name = (client or {}).get("client_name")
        return str(name) if name else pending.client_id

    def consent_page(self, txn: str) -> str:
        """HTML consent form. `txn` must already be validated by the caller."""
        # client_name comes from open DCR (untrusted) — escaped before rendering.
        client_name = escape(self._client_display_name(txn))
        return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>ai-memory — approve connector</title></head>
<body style="font-family: system-ui, sans-serif; max-width: 26rem; margin: 4rem auto;">
  <h1 style="font-size: 1.2rem;">Approve connector access</h1>
  <p><strong>{client_name}</strong> is requesting access to your memory bank.
  Paste the connector secret (Bitwarden: <code>MCP_CONNECTOR_BEARER_TOKEN</code>)
  to approve.</p>
  <form method="post" action="/consent">
    <input type="hidden" name="txn" value="{escape(txn)}">
    <input type="password" name="secret" autofocus required
           style="width: 100%; padding: 0.5rem;" placeholder="Connector secret">
    <button type="submit" style="margin-top: 0.75rem; padding: 0.5rem 1.5rem;">Approve</button>
  </form>
</body>
</html>"""

    def consent_success_page(self, redirect_url: str) -> str:
        """HTML page that returns the browser to the connector OAuth callback.

        A bare 302 after POST is enough for most clients, but ChatGPT's OAuth
        popup sometimes stalls on an empty redirect — so we also render an
        auto-redirect plus a manual fallback link (same redirect URL).
        """
        safe_href = escape(redirect_url, quote=True)
        safe_js = json.dumps(redirect_url)
        return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>ai-memory — approved</title>
  <meta http-equiv="refresh" content="0;url={safe_href}">
</head>
<body style="font-family: system-ui, sans-serif; max-width: 28rem; margin: 4rem auto;">
  <h1 style="font-size: 1.2rem;">Approved</h1>
  <p>Returning you to the connector to finish sign-in…</p>
  <p><a id="oauth-redirect" href="{safe_href}">Continue to connector</a>
  if you are not redirected automatically.</p>
  <script>window.location.replace({safe_js});</script>
</body>
</html>"""

    def complete_consent(self, txn: str, secret: str) -> str:
        """Verify the consent secret and mint an authorization code.

        Returns the client redirect URL (callback + code + state).
        """
        self._prune_pending()
        pending = self._pending.get(txn)
        if pending is None:
            raise UnknownTransactionError(txn)
        if not hmac.compare_digest(secret.encode(), self._secret.encode()):
            raise WrongSecretError()
        del self._pending[txn]

        params = pending.params
        code = secrets.token_urlsafe(32)
        self._store.put(
            "auth_codes",
            _hash(code),
            {
                "client_id": pending.client_id,
                "code_challenge": params.code_challenge,
                "redirect_uri": str(params.redirect_uri),
                "redirect_uri_provided_explicitly": params.redirect_uri_provided_explicitly,
                "scopes": params.scopes or [],
                "resource": params.resource,
                "expires_at": _now() + AUTH_CODE_TTL_SECONDS,
            },
        )
        return construct_redirect_uri(str(params.redirect_uri), code=code, state=params.state)

    # --- token issuance ----------------------------------------------------------

    async def load_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: str
    ) -> AuthorizationCode | None:
        data = self._store.get("auth_codes", _hash(authorization_code))
        if data is None or data["client_id"] != client.client_id:
            return None
        return AuthorizationCode(
            code=authorization_code,
            scopes=data["scopes"],
            expires_at=data["expires_at"],
            client_id=data["client_id"],
            code_challenge=data["code_challenge"],
            redirect_uri=AnyUrl(data["redirect_uri"]),
            redirect_uri_provided_explicitly=data["redirect_uri_provided_explicitly"],
            resource=data["resource"],
        )

    async def exchange_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: AuthorizationCode
    ) -> OAuthToken:
        # Single use: the code dies before the tokens are minted.
        self._store.delete("auth_codes", _hash(authorization_code.code))
        return self._issue_tokens(
            authorization_code.client_id,
            authorization_code.scopes,
            authorization_code.resource,
        )

    def _issue_tokens(
        self, client_id: str, scopes: list[str], resource: str | None = None
    ) -> OAuthToken:
        access_token = secrets.token_urlsafe(32)
        refresh_token = secrets.token_urlsafe(32)
        now = int(_now())
        self._store.put(
            "access_tokens",
            _hash(access_token),
            {
                "client_id": client_id,
                "scopes": scopes,
                "expires_at": now + ACCESS_TOKEN_TTL_SECONDS,
                "resource": resource,
            },
        )
        self._store.put(
            "refresh_tokens",
            _hash(refresh_token),
            {
                "client_id": client_id,
                "scopes": scopes,
                "expires_at": now + REFRESH_TOKEN_TTL_SECONDS,
            },
        )
        return OAuthToken(
            access_token=access_token,
            expires_in=ACCESS_TOKEN_TTL_SECONDS,
            refresh_token=refresh_token,
            scope=" ".join(scopes) if scopes else None,
        )

    async def load_refresh_token(
        self, client: OAuthClientInformationFull, refresh_token: str
    ) -> RefreshToken | None:
        data = self._store.get("refresh_tokens", _hash(refresh_token))
        if data is None or data["client_id"] != client.client_id:
            return None
        return RefreshToken(
            token=refresh_token,
            client_id=data["client_id"],
            scopes=data["scopes"],
            expires_at=data["expires_at"],
        )

    async def exchange_refresh_token(
        self,
        client: OAuthClientInformationFull,
        refresh_token: RefreshToken,
        scopes: list[str],
    ) -> OAuthToken:
        # Rotation: the presented refresh token dies; a fresh pair is minted.
        self._store.delete("refresh_tokens", _hash(refresh_token.token))
        return self._issue_tokens(refresh_token.client_id, scopes)

    # --- resource-server verification ---------------------------------------------

    async def load_access_token(self, token: str) -> AccessToken | None:
        # Static fallback: the connector secret itself stays a valid access token
        # (agent live-verification via curl; API-path callers that support
        # authorization_token). Same secret class as the consent password.
        if hmac.compare_digest(token.encode(), self._secret.encode()):
            return AccessToken(token=token, client_id=STATIC_CLIENT_ID, scopes=[])

        data = self._store.get("access_tokens", _hash(token))
        if data is None:
            return None
        if data["expires_at"] < _now():
            self._store.delete("access_tokens", _hash(token))
            return None
        return AccessToken(
            token=token,
            client_id=data["client_id"],
            scopes=data["scopes"],
            expires_at=int(data["expires_at"]),
            resource=data["resource"],
        )

    async def revoke_token(self, token: AccessToken | RefreshToken) -> None:
        self._store.delete("access_tokens", _hash(token.token))
        self._store.delete("refresh_tokens", _hash(token.token))
