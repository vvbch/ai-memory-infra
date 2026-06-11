"""Ingest LifeGraph entities from memory metadata (Phase 6 stub)."""

from __future__ import annotations

from typing import Any

from life_graph.graph_store import GraphStore
from life_graph.schema import EdgeSpec, NodeSpec


def ingest_decision_from_memory(
    graph: GraphStore,
    *,
    person_key: str,
    decision_name: str,
    event_date: str,
    venture_key: str | None = None,
) -> str:
    """Add a Decision node and DECIDED edge from a Mem0 memory summary."""
    decision_key = f"decision:{decision_name.lower().replace(' ', '-')[:48]}"
    if decision_key not in graph.nodes:
        graph.add_node(
            NodeSpec(
                "Decision",
                decision_key,
                {"name": decision_name, "date": event_date},
            )
        )
    if person_key in graph.nodes:
        graph.add_edge(
            EdgeSpec("DECIDED", person_key, decision_key, {"date": event_date})
        )
    if venture_key and venture_key in graph.nodes:
        graph.add_edge(EdgeSpec("RELATED_TO", decision_key, venture_key))
    return decision_key


def ingest_memory_record(graph: GraphStore, record: dict[str, Any]) -> str | None:
    """Best-effort ingest when metadata.type is decision."""
    meta = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    if meta.get("type") != "decision":
        return None
    text = str(record.get("memory") or record.get("text") or "").strip()
    if not text:
        return None
    event_date = str(meta.get("event_date") or meta.get("occurred_at") or "")[:10]
    return ingest_decision_from_memory(
        graph,
        person_key="person:chandra",
        decision_name=text[:120],
        event_date=event_date or "2026-01-01",
    )
