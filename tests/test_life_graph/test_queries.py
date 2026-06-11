"""Unit tests for LifeGraph query helpers."""

from __future__ import annotations

from life_graph.queries import (
    cypher_people_for_venture,
    decisions_timeline,
    people_for_venture,
    skills_for_person,
)
from life_graph.seed import build_seed_graph


def test_people_for_venture_returns_workers() -> None:
    graph = build_seed_graph()
    people = people_for_venture(graph, "AlphaCorp")
    assert people == ["Alex", "Blake"]


def test_skills_for_person_lists_has_skill_edges() -> None:
    graph = build_seed_graph()
    skills = skills_for_person(graph, "Alex")
    assert "Python" in skills
    assert "distributed systems" in skills


def test_decisions_timeline_sorted_and_filterable() -> None:
    graph = build_seed_graph()
    all_decisions = decisions_timeline(graph)
    assert len(all_decisions) >= 2
    assert all_decisions[0]["date"] <= all_decisions[-1]["date"]
    recent = decisions_timeline(graph, since="2026-06-01")
    assert all(row["date"] >= "2026-06-01" for row in recent)


def test_cypher_people_for_venture_is_parameterized_template() -> None:
    query = cypher_people_for_venture("AlphaCorp")
    assert "MATCH (p:Person)" in query
    assert "AlphaCorp" in query
