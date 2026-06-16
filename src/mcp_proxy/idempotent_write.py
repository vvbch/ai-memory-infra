"""Shared idempotent write path — verify-then-skip on timeout (ADR 037)."""

from __future__ import annotations

import os
import time
from typing import Any, Protocol

import httpx

from memory.contract import EXTERNAL_ID_KEY

DEFAULT_WRITE_TIMEOUT_S = 120.0
DEFAULT_VERIFY_WINDOW_S = 90.0
DEFAULT_VERIFY_INTERVAL_S = 3.0


def write_timeout_seconds() -> float:
    return float(os.environ.get("AI_MEMORY_WRITE_TIMEOUT", DEFAULT_WRITE_TIMEOUT_S))


def verify_window_seconds() -> float:
    return float(os.environ.get("AI_MEMORY_VERIFY_WINDOW_S", DEFAULT_VERIFY_WINDOW_S))


def verify_interval_seconds() -> float:
    return float(os.environ.get("AI_MEMORY_VERIFY_INTERVAL_S", DEFAULT_VERIFY_INTERVAL_S))


class MemoryWriteClient(Protocol):
    def add_memory(
        self,
        text: str,
        *,
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        infer: bool = True,
    ) -> dict[str, Any]: ...

    def list_memories(
        self,
        *,
        user_id: str | None = None,
        limit: int | None = None,
    ) -> Any: ...

    def search_memories(
        self,
        query: str,
        *,
        user_id: str | None = None,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]: ...


def _normalize_list(raw: Any) -> list[dict[str, Any]]:
    if isinstance(raw, list):
        return [r for r in raw if isinstance(r, dict)]
    if isinstance(raw, dict):
        items = raw.get("results", raw.get("memories"))
        if isinstance(items, list):
            return [r for r in items if isinstance(r, dict)]
    return []


def list_all_memories(
    client: MemoryWriteClient, *, user_id: str | None = None
) -> list[dict[str, Any]]:
    raw = client.list_memories(user_id=user_id, limit=1000)
    return _normalize_list(raw)


def _record_metadata(rec: dict[str, Any]) -> dict[str, Any]:
    nested = rec.get("metadata")
    return dict(nested) if isinstance(nested, dict) else {}


def _record_id(rec: dict[str, Any]) -> str:
    return str(rec.get("id") or rec.get("memory_id") or "")


def _search_by_external_id(
    client: MemoryWriteClient,
    external_id: str,
    *,
    user_id: str | None = None,
) -> dict[str, Any] | None:
    try:
        filtered = client.search_memories(
            external_id,
            user_id=user_id,
            top_k=5,
            filters={EXTERNAL_ID_KEY: external_id},
        )
        for rec in _normalize_list(filtered):
            meta = _record_metadata(rec)
            if meta.get(EXTERNAL_ID_KEY) == external_id:
                return rec
    except Exception:
        pass
    return None


def cache_record_from_write(
    text: str,
    *,
    external_id: str,
    metadata: dict[str, Any],
    add_result: dict[str, Any],
) -> dict[str, Any] | None:
    """Build a list_memories-shaped row from an add_memory API response."""
    results = add_result.get("results") if isinstance(add_result, dict) else None
    if not isinstance(results, list) or not results:
        return None
    first = results[0]
    if not isinstance(first, dict):
        return None
    mid = first.get("id") or first.get("memory_id")
    if not mid:
        return None
    meta = dict(metadata)
    meta[EXTERNAL_ID_KEY] = external_id
    return {"id": str(mid), "memory": text, "metadata": meta}


def append_cache_record(
    cache: list[dict[str, Any]] | None,
    record: dict[str, Any] | None,
) -> None:
    """Append a memory row to the in-process import cache (dedupe by external_id)."""
    if cache is None or record is None:
        return
    ext = _record_metadata(record).get(EXTERNAL_ID_KEY)
    if ext:
        for rec in cache:
            if _record_metadata(rec).get(EXTERNAL_ID_KEY) == ext:
                return
    cache.append(record)


def update_cache_after_write(
    client: MemoryWriteClient,
    cache: list[dict[str, Any]] | None,
    *,
    external_id: str,
    user_id: str | None,
    text: str,
    metadata: dict[str, Any],
    add_result: dict[str, Any] | None = None,
    written_record: dict[str, Any] | None = None,
) -> None:
    """Extend the import cache after a successful write — no full list_all_memories."""
    if cache is None:
        return
    record = written_record or (
        cache_record_from_write(
            text, external_id=external_id, metadata=metadata, add_result=add_result or {}
        )
        if add_result is not None
        else None
    )
    if record is None:
        record = _search_by_external_id(client, external_id, user_id=user_id)
    append_cache_record(cache, record)


def find_by_external_id(
    client: MemoryWriteClient,
    external_id: str,
    *,
    user_id: str | None = None,
    cache: list[dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    items = cache if cache is not None else list_all_memories(client, user_id=user_id)
    for rec in items:
        meta = _record_metadata(rec)
        if meta.get(EXTERNAL_ID_KEY) == external_id:
            return rec
    return _search_by_external_id(client, external_id, user_id=user_id)


def add_memory_idempotent(
    client: MemoryWriteClient,
    text: str,
    *,
    external_id: str,
    user_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    infer: bool = True,
    verify_window_s: float | None = None,
    verify_interval_s: float | None = None,
    cache: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Write once with external_id; skip if exists; verify-then-skip on timeout."""
    meta = dict(metadata or {})
    meta[EXTERNAL_ID_KEY] = external_id

    existing = find_by_external_id(client, external_id, user_id=user_id, cache=cache)
    if existing is not None:
        return {
            "external_id": external_id,
            "status": "skipped_exists",
            "memory_id": _record_id(existing),
        }

    window = verify_window_s if verify_window_s is not None else verify_window_seconds()
    interval = (
        verify_interval_s if verify_interval_s is not None else verify_interval_seconds()
    )

    try:
        result = client.add_memory(text, metadata=meta, infer=infer, user_id=user_id)
        update_cache_after_write(
            client,
            cache,
            external_id=external_id,
            user_id=user_id,
            text=text,
            metadata=meta,
            add_result=result,
        )
        return {"external_id": external_id, "status": "written", "result": result}
    except httpx.TimeoutException:
        deadline = time.monotonic() + window
        while time.monotonic() < deadline:
            time.sleep(interval)
            found = find_by_external_id(client, external_id, user_id=user_id, cache=cache)
            if found is not None:
                update_cache_after_write(
                    client,
                    cache,
                    external_id=external_id,
                    user_id=user_id,
                    text=text,
                    metadata=meta,
                    written_record=found,
                )
                return {
                    "external_id": external_id,
                    "status": "verified_after_timeout",
                    "memory_id": _record_id(found),
                }
        return {
            "external_id": external_id,
            "status": "timeout_unverified",
            "message": (
                "client timed out and external_id was not found during verify window; "
                "do not reword-retry — re-run or inspect server logs"
            ),
        }
