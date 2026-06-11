"""Integration tests for LifeGraph seed structure."""

from __future__ import annotations

from life_graph.seed import build_seed_graph


def test_seed_graph_contains_core_people_and_ventures() -> None:
    graph = build_seed_graph()
    names = {props["name"] for props in graph.nodes.values()}
    assert {"Chandra", "Vijaya", "TradingFirmLLP", "ContentFirm"}.issubset(names)


def test_seed_graph_links_chandra_to_trading_firm() -> None:
    graph = build_seed_graph()
    neighbors = graph.neighbors("person:chandra", rel_type="WORKS_ON")
    assert "venture:trading-firm" in neighbors


def test_seed_graph_has_skills_and_decisions() -> None:
    graph = build_seed_graph()
    labels = {props["label"] for props in graph.nodes.values()}
    assert "Skill" in labels
    assert "Decision" in labels
    assert len(graph.edges) >= 10
