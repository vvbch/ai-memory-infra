"""Remote Streamable HTTP MCP entrypoint with self-hosted OAuth (ADR 034 + 035).

Runs the same three tools as the local stdio proxy (`mcp_proxy.server`) behind
Streamable HTTP so Claude's remote-connector clients (incl. iPhone) can reach
the live memory bank at `https://mcp.{domain}/`. Auth is OAuth 2.1 (DCR + PKCE
S256) served by the same origin — the only model claude.ai custom connectors
accept — with the static `MCP_CONNECTOR_BEARER_TOKEN` still honored as an
access token for verification/API-path callers. See ADR 035.
"""

from __future__ import annotations

import os
from pathlib import Path

import uvicorn
from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import AnyHttpUrl
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse, Response

from mcp_proxy import server
from mcp_proxy.oauth import (
    OAuthStateStore,
    SingleUserOAuthProvider,
    UnknownTransactionError,
    WrongSecretError,
)

DEFAULT_HOST = "0.0.0.0"  # container-internal; only Caddy is public (ADR 009)
DEFAULT_PORT = 8765
DEFAULT_PUBLIC_HOST = "mcp.chandrav.dev"
DEFAULT_STATE_PATH = "/data/oauth_state.json"


def _allowed_hosts() -> list[str]:
    raw = os.environ.get("MCP_ALLOWED_HOSTS", DEFAULT_PUBLIC_HOST)
    return [host.strip() for host in raw.split(",") if host.strip()]


def build_app(
    secret: str,
    allowed_hosts: list[str] | None = None,
    issuer: str | None = None,
    state_path: Path | str | None = None,
) -> Starlette:
    """Build the OAuth-protected Streamable HTTP app serving MCP at the root.

    `secret` is `MCP_CONNECTOR_BEARER_TOKEN`: the operator consent password and
    the static fallback access token (ADR 035 §2-3).
    """
    hosts = allowed_hosts if allowed_hosts is not None else _allowed_hosts()
    issuer = (issuer or os.environ.get("MCP_PUBLIC_BASE_URL", f"https://{hosts[0]}")).rstrip("/")
    state_path = Path(state_path or os.environ.get("MCP_OAUTH_STATE_PATH", DEFAULT_STATE_PATH))

    provider = SingleUserOAuthProvider(
        store=OAuthStateStore(state_path), consent_secret=secret, issuer=issuer
    )

    mcp = FastMCP(
        "ai-memory",
        auth_server_provider=provider,
        auth=AuthSettings(
            issuer_url=AnyHttpUrl(issuer),
            resource_server_url=AnyHttpUrl(f"{issuer}/"),
            client_registration_options=ClientRegistrationOptions(enabled=True),
        ),
        # Stateless: every request gets a fresh transport — no server-side
        # session affinity needed behind Caddy (single-user remote connector).
        stateless_http=True,
        # Serve at "/" so the connector URL is exactly https://mcp.{domain}/.
        streamable_http_path="/",
        # Keep the transport's DNS-rebinding protection on, scoped to our
        # subdomain (Caddy forwards the original Host header).
        transport_security=TransportSecuritySettings(
            allowed_hosts=hosts,
            allowed_origins=[f"https://{host}" for host in hosts],
        ),
    )

    # Same tool implementations as the local stdio proxy (ADR 025/028).
    mcp.add_tool(server.search_memories)
    mcp.add_tool(server.add_memory)
    mcp.add_tool(server.list_memories)

    @mcp.custom_route("/health", methods=["GET"])  # type: ignore[untyped-decorator]
    async def health(_: Request) -> Response:
        # Open for container/Caddy liveness probes; it leaks nothing.
        return JSONResponse({"status": "ok"})

    @mcp.custom_route("/consent", methods=["GET", "POST"])  # type: ignore[untyped-decorator]
    async def consent(request: Request) -> Response:
        if request.method == "GET":
            txn = request.query_params.get("txn", "")
            if not provider.transaction_exists(txn):
                return HTMLResponse("Unknown or expired authorization request.", status_code=400)
            return HTMLResponse(provider.consent_page(txn))

        form = await request.form()
        txn = str(form.get("txn", ""))
        entered_secret = str(form.get("secret", ""))
        try:
            redirect_url = provider.complete_consent(txn, entered_secret)
        except UnknownTransactionError:
            return HTMLResponse("Unknown or expired authorization request.", status_code=400)
        except WrongSecretError:
            return HTMLResponse(
                "Wrong secret. Go back and try again with the connector secret "
                "from Bitwarden (MCP_CONNECTOR_BEARER_TOKEN).",
                status_code=401,
            )
        return RedirectResponse(redirect_url, status_code=302)

    return mcp.streamable_http_app()


def main() -> None:
    token = os.environ.get("MCP_CONNECTOR_BEARER_TOKEN", "").strip()
    if not token:
        raise SystemExit("Set MCP_CONNECTOR_BEARER_TOKEN before starting the HTTP MCP server.")

    host = os.environ.get("MCP_HTTP_HOST", DEFAULT_HOST)
    port = int(os.environ.get("MCP_HTTP_PORT", str(DEFAULT_PORT)))
    uvicorn.run(build_app(token), host=host, port=port)


if __name__ == "__main__":
    main()
