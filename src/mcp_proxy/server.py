"""Local MCP server that proxies tools to the live ai-memory API."""

from __future__ import annotations

import datetime as _dt
import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from mcp_proxy.client import MemoryApiClient, MemoryApiConfig
from memory.contract import DEFAULT_NAMESPACE, build_fact_metadata, validate_fact_text

mcp = FastMCP("ai-memory")


def _client() -> MemoryApiClient:
    return MemoryApiClient(MemoryApiConfig.from_env())


def _today_iso() -> str:
    return _dt.date.today().isoformat()


@mcp.tool()
def search_memories(query: str, top_k: int = 5, user_id: str | None = None) -> dict[str, Any]:
    """Search the live ai-memory store."""
    return _client().search_memories(query, top_k=top_k, user_id=user_id)


@mcp.tool()
def add_memory(
    text: str,
    user_id: str | None = None,
    metadata_json: str | None = None,
    event_date: str | None = None,
    source_doc_id: str | None = None,
    namespace: str | None = None,
    external_id: str | None = None,
) -> dict[str, Any]:
    """Save a memory to the live ai-memory store.

    Optional metadata_json merges with contract fields. When external_id is set,
    the write is idempotent (verify-then-skip on timeout).
    """
    client = _client()
    extra: dict[str, Any] = {}
    if metadata_json:
        parsed = json.loads(metadata_json)
        if not isinstance(parsed, dict):
            raise ValueError("metadata_json must decode to a JSON object")
        extra = parsed

    resolved_event = (
        event_date or extra.get("event_date") or extra.get("occurred_at") or _today_iso()
    )
    resolved_namespace = namespace or extra.get("namespace") or DEFAULT_NAMESPACE
    resolved_source = str(extra.get("source") or "mcp")
    resolved_doc_id = source_doc_id or extra.get("source_doc_id")
    ext = external_id or extra.get("external_id")
    infer = bool(extra.get("infer", True))

    if extra.get("type") in ("open_item", "decision") or extra.get("status"):
        meta: dict[str, Any] = {
            "source": resolved_source,
            "namespace": resolved_namespace,
            **{k: v for k, v in extra.items() if v not in (None, "", [])},
        }
        if resolved_doc_id:
            meta["source_doc_id"] = resolved_doc_id
        if resolved_event:
            meta["event_date"] = str(resolved_event)[:10]
            meta["occurred_at"] = meta["event_date"]
        if ext:
            meta["external_id"] = ext
    else:
        validate_fact_text(text)
        meta = build_fact_metadata(
            event_date=str(resolved_event),
            source=resolved_source,
            source_doc_id=resolved_doc_id,
            namespace=resolved_namespace,
            external_id=ext,
            ventures=extra.get("ventures"),
            extra={k: v for k, v in extra.items() if k not in {"source", "ventures", "type"}},
        )

    if ext:
        return client.add_memory_idempotent(
            text,
            external_id=str(ext),
            user_id=user_id,
            metadata=meta,
            infer=infer,
        )
    return client.add_memory(text, user_id=user_id, metadata=meta, infer=infer)


@mcp.tool()
def list_memories(user_id: str | None = None) -> Any:
    """List memories for the configured ai-memory user."""
    return _client().list_memories(user_id=user_id)


@mcp.tool()
def delete_memory(memory_id: str) -> dict[str, Any]:
    """Delete a memory by id from the live ai-memory store."""
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
        parsed = json.loads(metadata_json)
        if not isinstance(parsed, dict):
            raise ValueError("metadata_json must decode to a JSON object")
        metadata = parsed
    return _client().update_memory(memory_id, text, metadata=metadata)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
