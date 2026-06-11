"""Unit tests for LifeGraph ingest helpers."""

from __future__ import annotations

from life_graph.ingest import ingest_decision_from_memory, ingest_memory_record
from life_graph.seed import build_seed_graph


def test_ingest_decision_from_memory_adds_nodes_and_edges() -> None:
    graph = build_seed_graph()
    key = ingest_decision_from_memory(
        graph,
        person_key="person:alex",
        decision_name="chose Terraform for IaC",
        event_date="2026-06-01",
        venture_key="venture:alpha-corp",
    )
    assert key in graph.nodes
    assert graph.nodes[key]["label"] == "Decision"


def test_ingest_memory_record_skips_non_decisions() -> None:
    graph = build_seed_graph()
    assert ingest_memory_record(graph, {"metadata": {"type": "fact"}, "text": "x"}) is None
