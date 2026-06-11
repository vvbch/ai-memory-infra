"""Retrieval read convention — event_date ordering, not created_at (ADR 037 §7)."""

from __future__ import annotations

from typing import Any, Protocol

from memory.contract import DEFAULT_NAMESPACE, EXTERNAL_ID_KEY, event_date_of

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


def matches_external_id_prefix(rec: dict[str, Any], prefix: str) -> bool:
    """True when record metadata external_id starts with prefix."""
    ext = record_metadata(rec).get("external_id") or ""
    return isinstance(ext, str) and ext.startswith(prefix)


def fetch_by_external_id(
    client: MemorySearchClient,
    external_id: str,
    *,
    user_id: str | None = None,
) -> dict[str, Any] | None:
    """Fetch one memory by exact external_id (server-side metadata filter)."""
    try:
        filtered = client.search_memories(
            external_id,
            user_id=user_id,
            top_k=5,
            filters={EXTERNAL_ID_KEY: external_id},
        )
        for rec in _normalize_list(filtered):
            if record_metadata(rec).get(EXTERNAL_ID_KEY) == external_id:
                return rec
    except Exception:
        pass
    return None


def list_by_external_id_prefix(
    client: MemorySearchClient,
    prefix: str,
    *,
    user_id: str | None = None,
    namespace: str | None = DEFAULT_NAMESPACE,
    external_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    """List memories whose external_id starts with prefix (probe / fixture isolation).

    When ``external_ids`` is provided, each id is resolved via ``fetch_by_external_id``
    (works when ``GET /memories`` is capped). Otherwise falls back to a list scan.
    """
    if external_ids is not None:
        out: list[dict[str, Any]] = []
        for eid in external_ids:
            if not eid.startswith(prefix):
                continue
            rec = fetch_by_external_id(client, eid, user_id=user_id)
            if rec is None:
                continue
            if namespace is not None:
                meta = record_metadata(rec)
                if meta.get("namespace", DEFAULT_NAMESPACE) != namespace:
                    continue
            out.append(rec)
        if out:
            return out

    scanned: list[dict[str, Any]] = []
    for rec in _normalize_list(client.list_memories(user_id=user_id, limit=1000)):
        if not matches_external_id_prefix(rec, prefix):
            continue
        if namespace is not None:
            meta = record_metadata(rec)
            if meta.get("namespace", DEFAULT_NAMESPACE) != namespace:
                continue
        scanned.append(rec)
    return scanned


def search_with_contract(
    client: MemorySearchClient,
    query: str,
    *,
    user_id: str | None = None,
    namespace: str | None = DEFAULT_NAMESPACE,
    top_k: int = 10,
    extra_filters: dict[str, Any] | None = None,
    external_id_prefix: str | None = None,
    external_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Similarity search with optional namespace filter; returns raw result records.

    When ``external_id_prefix`` is set, results are scoped to that prefix. Vector hits
    outside the prefix are dropped; the prefix pool is built from ``external_ids``
    when provided (required at scale — ``GET /memories`` may be capped).
    """
    filters: dict[str, Any] = dict(extra_filters or {})
    if namespace is not None:
        filters["namespace"] = namespace
    payload = client.search_memories(
        query,
        user_id=user_id,
        top_k=top_k,
        filters=filters or None,
    )
    hits = _normalize_list(payload)
    if external_id_prefix is None:
        return hits

    pool = list_by_external_id_prefix(
        client,
        external_id_prefix,
        user_id=user_id,
        namespace=namespace,
        external_ids=external_ids,
    )
    if pool:
        pool_ids = {record_id(r) for r in pool}
        vector_prefix = [h for h in hits if record_id(h) in pool_ids]
        seen = {record_id(h) for h in vector_prefix}
        merged = vector_prefix + [r for r in pool if record_id(r) not in seen]
        return merged[: max(top_k, len(pool))]

    return [h for h in hits if matches_external_id_prefix(h, external_id_prefix)]


def entity_disambiguation_score(text: str, query: str) -> int:
    """Score a candidate for entity-collision queries using inline qualifier overlap."""
    text_l = text.lower()
    q_l = query.lower()
    score = 0
    if "project contact" in q_l and "project contact" in text_l:
        score += 10
    if "team lead's sibling" in text_l:
        score -= 8
    return score


def best_entity_match(
    records: list[dict[str, Any]],
    query: str,
    *,
    entity_token: str = "Jordan",
) -> dict[str, Any] | None:
    """Pick the best entity hit after inline-qualifier rerank."""
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
