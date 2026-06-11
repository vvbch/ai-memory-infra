"""Initial LifeGraph seed data (Phase 6 POC — synthetic fixtures)."""

from __future__ import annotations

from life_graph.graph_store import GraphStore
from life_graph.schema import EdgeSpec, NodeSpec


def build_seed_graph() -> GraphStore:
    """Return a synthetic starter LifeGraph for demos and tests."""
    graph = GraphStore()

    people = [
        NodeSpec("Person", "person:alex", {"name": "Alex", "role": "founder"}),
        NodeSpec("Person", "person:blake", {"name": "Blake", "role": "co-founder"}),
        NodeSpec("Person", "person:casey", {"name": "Casey", "role": "contributor"}),
    ]
    ventures = [
        NodeSpec(
            "Venture",
            "venture:alpha-corp",
            {"name": "AlphaCorp", "status": "planning", "venture_tag": "trading_firm"},
        ),
        NodeSpec(
            "Venture",
            "venture:media-lab",
            {"name": "MediaLab", "status": "planning", "venture_tag": "social_media"},
        ),
        NodeSpec(
            "Venture",
            "venture:advisory",
            {"name": "AdvisoryCo", "status": "future", "venture_tag": "ria"},
        ),
    ]
    skills = [
        NodeSpec("Skill", "skill:python", {"name": "Python"}),
        NodeSpec("Skill", "skill:distributed-systems", {"name": "distributed systems"}),
        NodeSpec("Skill", "skill:data-engineering", {"name": "data engineering"}),
    ]
    decisions = [
        NodeSpec(
            "Decision",
            "decision:mem0",
            {"name": "chose Mem0 over alternatives", "date": "2026-06-04"},
        ),
        NodeSpec(
            "Decision",
            "decision:entity-structure",
            {"name": "chose LLP structure for new venture", "date": "2026-05-01"},
        ),
    ]
    milestones = [
        NodeSpec(
            "Milestone",
            "milestone:platform-launch",
            {"name": "platform MVP launch", "date": "2026-07-01"},
        ),
        NodeSpec(
            "Milestone",
            "milestone:cert-deadline",
            {"name": "certification deadline", "date": "2026-12-01"},
        ),
    ]
    goals = [
        NodeSpec("Goal", "goal:relocation", {"name": "international relocation"}),
        NodeSpec("Goal", "goal:platform-scale", {"name": "scale memory platform"}),
    ]
    tools = [
        NodeSpec("Tool", "tool:mem0", {"name": "Mem0"}),
        NodeSpec("Tool", "tool:neo4j", {"name": "Neo4j"}),
    ]

    for node in [*people, *ventures, *skills, *decisions, *milestones, *goals, *tools]:
        graph.add_node(node)

    edges = [
        EdgeSpec("CO_FOUNDER", "person:alex", "person:blake"),
        EdgeSpec("WORKS_ON", "person:alex", "venture:alpha-corp"),
        EdgeSpec("WORKS_ON", "person:blake", "venture:alpha-corp"),
        EdgeSpec("WORKS_ON", "person:blake", "venture:media-lab"),
        EdgeSpec("HAS_SKILL", "person:alex", "skill:python"),
        EdgeSpec("HAS_SKILL", "person:alex", "skill:distributed-systems"),
        EdgeSpec("HAS_SKILL", "person:alex", "skill:data-engineering"),
        EdgeSpec("DECIDED", "person:alex", "decision:mem0", {"date": "2026-06-04"}),
        EdgeSpec("DECIDED", "person:alex", "decision:entity-structure", {"date": "2026-05-01"}),
        EdgeSpec("TARGETS", "person:alex", "goal:relocation", {"deadline": "2026-12-01"}),
        EdgeSpec("TARGETS", "person:alex", "goal:platform-scale"),
        EdgeSpec("ACHIEVED", "person:alex", "milestone:platform-launch", {"date": "2026-07-01"}),
        EdgeSpec("USES", "person:alex", "tool:mem0"),
        EdgeSpec("USES", "person:alex", "tool:neo4j"),
        EdgeSpec("RELATED_TO", "decision:mem0", "venture:alpha-corp"),
    ]
    for edge in edges:
        graph.add_edge(edge)

    return graph
