"""Local MCP server that proxies tools to the live ai-memory API."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from mcp_proxy.client import MemoryApiClient, MemoryApiConfig

mcp = FastMCP("ai-memory")


def _client() -> MemoryApiClient:
    return MemoryApiClient(MemoryApiConfig.from_env())


@mcp.tool()
def search_memories(query: str, top_k: int = 5, user_id: str | None = None) -> dict[str, Any]:
    """Search Chandra's live ai-memory store."""
    return _client().search_memories(query, top_k=top_k, user_id=user_id)


@mcp.tool()
def add_memory(text: str, user_id: str | None = None) -> dict[str, Any]:
    """Save a memory to Chandra's live ai-memory store."""
    metadata = {"source": "mcp"}
    return _client().add_memory(text, user_id=user_id, metadata=metadata)


@mcp.tool()
def list_memories(user_id: str | None = None) -> Any:
    """List memories for the configured ai-memory user."""
    return _client().list_memories(user_id=user_id)


@mcp.tool()
def delete_memory(memory_id: str) -> dict[str, Any]:
    """Delete a memory by id from Chandra's live ai-memory store."""
    return _client().delete_memory(memory_id)


@mcp.tool()
def update_memory(
    memory_id: str,
    text: str,
    metadata_json: str | None = None,
) -> dict[str, Any]:
    """Update a memory's text (and optional metadata JSON object)."""
    metadata: dict[str, Any] | None = None
    if metadata_json:
        import json

        parsed = json.loads(metadata_json)
        if not isinstance(parsed, dict):
            raise ValueError("metadata_json must decode to a JSON object")
        metadata = parsed
    return _client().update_memory(memory_id, text, metadata=metadata)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
