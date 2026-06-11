"""LifeGraph query helpers (Phase 6)."""

from __future__ import annotations

from typing import Any

from life_graph.graph_store import GraphStore


def _node_name(graph: GraphStore, key: str) -> str:
    return str(graph.nodes[key].get("name", key))


def people_for_venture(graph: GraphStore, venture_name: str) -> list[str]:
    """Return person names connected to a venture via WORKS_ON."""
    venture_keys = [
        key
        for key, props in graph.nodes.items()
        if props.get("label") == "Venture" and props.get("name") == venture_name
    ]
    people: list[str] = []
    for venture_key in venture_keys:
        for person_key in graph.neighbors(venture_key, rel_type="WORKS_ON", direction="in"):
            if graph.nodes[person_key].get("label") == "Person":
                people.append(_node_name(graph, person_key))
    return sorted(set(people))


def skills_for_person(graph: GraphStore, person_name: str) -> list[str]:
    """Return skill names linked to a person via HAS_SKILL."""
    person_keys = [
        key
        for key, props in graph.nodes.items()
        if props.get("label") == "Person" and props.get("name") == person_name
    ]
    skills: list[str] = []
    for person_key in person_keys:
        for skill_key in graph.neighbors(person_key, rel_type="HAS_SKILL"):
            if graph.nodes[skill_key].get("label") == "Skill":
                skills.append(_node_name(graph, skill_key))
    return sorted(skills)


def decisions_timeline(
    graph: GraphStore,
    *,
    since: str | None = None,
) -> list[dict[str, Any]]:
    """Return decisions with dates, optionally filtered by ISO date lower bound."""
    rows: list[dict[str, Any]] = []
    for key, props in graph.nodes.items():
        if props.get("label") != "Decision":
            continue
        date = str(props.get("date", ""))
        if since and date and date < since:
            continue
        rows.append({"name": props.get("name"), "date": date, "key": key})
    return sorted(rows, key=lambda row: row.get("date") or "")


def cypher_people_for_venture(venture_name: str) -> str:
    """Cypher template for cross-namespace demo queries."""
    return (
        "MATCH (p:Person)-[:WORKS_ON]->(v:Venture {name: $venture_name}) "
        "RETURN p.name AS person ORDER BY person"
    ).replace("$venture_name", repr(venture_name))
