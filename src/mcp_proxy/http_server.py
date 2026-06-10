"""Remote Streamable HTTP MCP entrypoint with a bearer-token gate (ADR 034).

Runs the same three tools as the local stdio proxy (`mcp_proxy.server`) behind
Streamable HTTP so Claude's remote-connector clients (incl. iPhone) can reach
the live memory bank at `https://mcp.{domain}/`. Auth v1 is a dedicated static
bearer token (`MCP_CONNECTOR_BEARER_TOKEN`) — deliberately not the admin API
key and not OAuth; see ADR 034 for the trade-offs.
"""

from __future__ import annotations

import hmac
import os

import uvicorn
from mcp.server.transport_security import TransportSecuritySettings
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from mcp_proxy.server import mcp

DEFAULT_HOST = "0.0.0.0"  # container-internal; only Caddy is public (ADR 009)
DEFAULT_PORT = 8765
DEFAULT_PUBLIC_HOST = "mcp.chandrav.dev"


class BearerGate:
    """ASGI wrapper that rejects HTTP requests lacking the expected bearer token.

    `/health` stays open for container/Caddy liveness probes; it leaks nothing.
    """

    def __init__(self, app: ASGIApp, token: str) -> None:
        self._app = app
        self._expected = f"Bearer {token}"

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        if scope["path"] == "/health":
            await JSONResponse({"status": "ok"})(scope, receive, send)
            return

        authorization = ""
        for name, value in scope["headers"]:
            if name == b"authorization":
                authorization = value.decode("latin-1")
                break

        if not hmac.compare_digest(authorization, self._expected):
            response = JSONResponse(
                {"error": "unauthorized"},
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
            )
            await response(scope, receive, send)
            return

        await self._app(scope, receive, send)


def _allowed_hosts() -> list[str]:
    raw = os.environ.get("MCP_ALLOWED_HOSTS", DEFAULT_PUBLIC_HOST)
    return [host.strip() for host in raw.split(",") if host.strip()]


def build_app(token: str, allowed_hosts: list[str] | None = None) -> BearerGate:
    """Build the gated Streamable HTTP app serving MCP at the subdomain root."""
    hosts = allowed_hosts if allowed_hosts is not None else _allowed_hosts()
    # Stateless: every request gets a fresh transport — no server-side session
    # affinity needed behind Caddy, which suits a single-user remote connector.
    mcp.settings.stateless_http = True
    # Serve at "/" so the connector URL is exactly https://mcp.{domain}/ (ADR 034).
    mcp.settings.streamable_http_path = "/"
    # Keep the transport's DNS-rebinding protection on, scoped to our subdomain
    # (Caddy forwards the original Host header).
    mcp.settings.transport_security = TransportSecuritySettings(
        allowed_hosts=hosts,
        allowed_origins=[f"https://{host}" for host in hosts],
    )
    return BearerGate(mcp.streamable_http_app(), token)


def main() -> None:
    token = os.environ.get("MCP_CONNECTOR_BEARER_TOKEN", "").strip()
    if not token:
        raise SystemExit("Set MCP_CONNECTOR_BEARER_TOKEN before starting the HTTP MCP server.")

    host = os.environ.get("MCP_HTTP_HOST", DEFAULT_HOST)
    port = int(os.environ.get("MCP_HTTP_PORT", str(DEFAULT_PORT)))
    uvicorn.run(build_app(token), host=host, port=port)


if __name__ == "__main__":
    main()
