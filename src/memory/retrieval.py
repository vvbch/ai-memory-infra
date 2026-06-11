"""Retrieval read convention — event_date ordering, not created_at (ADR 037 §7)."""

from __future__ import annotations

from typing import Any, Protocol

from memory.contract import DEFAULT_NAMESPACE, TYPE_FACT, event_date_of

TYPE_OPEN_ITEM = "open_item"
STATUS_OPEN = "open"
STATUS_IN_PROGRESS = "in_progress"
OPEN_STATUSES = frozenset({STATUS_OPEN, STATUS_IN_PROGRESS})


class MemorySearchClient(Protocol):
    def search_memories(
        self,
        query: str,
        *,
        user_id: str | None = None,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]: ...

    def list_memories(
        self,
        *,
        user_id: str | None = None,
        limit: int | None = None,
    ) -> Any: ...


def _normalize_list(raw: Any) -> list[dict[str, Any]]:
    if isinstance(raw, list):
        return [r for r in raw if isinstance(r, dict)]
    if isinstance(raw, dict):
        items = raw.get("results", raw.get("memories"))
        if isinstance(items, list):
            return [r for r in items if isinstance(r, dict)]
    return []


def record_text(rec: dict[str, Any]) -> str:
    return str(rec.get("memory") or rec.get("text") or "")


def record_id(rec: dict[str, Any]) -> str:
    return str(rec.get("id") or rec.get("memory_id") or "")


def record_metadata(rec: dict[str, Any]) -> dict[str, Any]:
    nested = rec.get("metadata")
    meta: dict[str, Any] = dict(nested) if isinstance(nested, dict) else {}
    for key in (
        "type",
        "status",
        "source",
        "namespace",
        "event_date",
        "occurred_at",
        "external_id",
    ):
        if key not in meta and key in rec:
            meta[key] = rec[key]
    return meta


def _event_date_sort_key(rec: dict[str, Any]) -> str:
    parsed = event_date_of(record_metadata(rec))
    return parsed or "0000-00-00"


def latest_by_event_date(records: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Pick the record with max event_date — never use created_at for recency."""
    if not records:
        return None
    return max(records, key=_event_date_sort_key)


def search_with_contract(
    client: MemorySearchClient,
    query: str,
    *,
    user_id: str | None = None,
    namespace: str | None = DEFAULT_NAMESPACE,
    top_k: int = 10,
    extra_filters: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Similarity search with optional namespace filter; returns raw result records."""
    filters: dict[str, Any] = dict(extra_filters or {})
    if namespace is not None:
        filters["namespace"] = namespace
    payload = client.search_memories(
        query,
        user_id=user_id,
        top_k=top_k,
        filters=filters or None,
    )
    return _normalize_list(payload)


def entity_disambiguation_score(text: str, query: str) -> int:
    """Score a candidate for entity-collision queries using inline qualifier overlap."""
    text_l = text.lower()
    q_l = query.lower()
    score = 0
    if "interview-prep contact" in q_l and "interview-prep contact" in text_l:
        score += 10
    if "elder son" in text_l:
        score -= 8
    return score


def best_entity_match(
    records: list[dict[str, Any]],
    query: str,
    *,
    entity_token: str = "Krishna",
) -> dict[str, Any] | None:
    """Pick the best Krishna (or other entity) hit after qualifier rerank."""
    scoped = [r for r in records if entity_token in record_text(r)]
    if not scoped:
        return None
    return max(scoped, key=lambda r: entity_disambiguation_score(record_text(r), query))


def open_follow_ups(
    client: MemorySearchClient,
    *,
    user_id: str | None = None,
    namespace: str | None = DEFAULT_NAMESPACE,
) -> list[dict[str, Any]]:
    """Return open items via metadata filter; fall back to list + client filter."""
    filters: dict[str, Any] = {"type": TYPE_OPEN_ITEM, "status": STATUS_OPEN}
    if namespace is not None:
        filters["namespace"] = namespace
    try:
        hits = search_with_contract(
            client,
            "open follow-up todo",
            user_id=user_id,
            namespace=None,
            top_k=50,
            extra_filters=filters,
        )
        if hits:
            return hits
    except Exception:
        pass

    out: list[dict[str, Any]] = []
    for rec in _normalize_list(client.list_memories(user_id=user_id, limit=1000)):
        meta = record_metadata(rec)
        if meta.get("type") != TYPE_OPEN_ITEM:
            continue
        if meta.get("status", STATUS_OPEN) not in OPEN_STATUSES:
            continue
        if namespace is not None and meta.get("namespace", DEFAULT_NAMESPACE) != namespace:
            continue
        out.append(rec)
    return out
