"""Initial LifeGraph seed data (Phase 6 POC)."""

from __future__ import annotations

from life_graph.graph_store import GraphStore
from life_graph.schema import EdgeSpec, NodeSpec


def build_seed_graph() -> GraphStore:
    """Return the canonical starter LifeGraph for demos and tests."""
    graph = GraphStore()

    people = [
        NodeSpec("Person", "person:chandra", {"name": "Chandra", "role": "founder"}),
        NodeSpec("Person", "person:vijaya", {"name": "Vijaya", "role": "co-founder"}),
        NodeSpec("Person", "person:chinnu", {"name": "Chinnu", "role": "family"}),
        NodeSpec("Person", "person:swapna", {"name": "Swapna", "role": "family"}),
    ]
    ventures = [
        NodeSpec(
            "Venture",
            "venture:trading-firm",
            {"name": "TradingFirmLLP", "status": "planning", "venture_tag": "trading_firm"},
        ),
        NodeSpec(
            "Venture",
            "venture:content-firm",
            {"name": "ContentFirm", "status": "planning", "venture_tag": "social_media"},
        ),
        NodeSpec(
            "Venture",
            "venture:ria",
            {"name": "RIA", "status": "future", "venture_tag": "ria"},
        ),
    ]
    skills = [
        NodeSpec("Skill", "skill:python", {"name": "Python"}),
        NodeSpec("Skill", "skill:distributed-systems", {"name": "distributed systems"}),
        NodeSpec("Skill", "skill:options-trading", {"name": "options trading"}),
    ]
    decisions = [
        NodeSpec(
            "Decision",
            "decision:mem0",
            {"name": "chose Mem0 over alternatives", "date": "2026-06-04"},
        ),
        NodeSpec(
            "Decision",
            "decision:llp",
            {"name": "LLP structure for tax efficiency", "date": "2026-05-01"},
        ),
    ]
    milestones = [
        NodeSpec(
            "Milestone",
            "milestone:amazon-exit",
            {"name": "Amazon exit", "date": "2026-07-01"},
        ),
        NodeSpec(
            "Milestone",
            "milestone:phd-deadline",
            {"name": "PhD deadline", "date": "2026-12-01"},
        ),
    ]
    goals = [
        NodeSpec("Goal", "goal:migration", {"name": "international migration"}),
        NodeSpec("Goal", "goal:ai-role", {"name": "AI engineering role"}),
    ]
    tools = [
        NodeSpec("Tool", "tool:mem0", {"name": "Mem0"}),
        NodeSpec("Tool", "tool:neo4j", {"name": "Neo4j"}),
    ]

    for node in [*people, *ventures, *skills, *decisions, *milestones, *goals, *tools]:
        graph.add_node(node)

    edges = [
        EdgeSpec("CO_FOUNDER", "person:chandra", "person:vijaya"),
        EdgeSpec("WORKS_ON", "person:chandra", "venture:trading-firm"),
        EdgeSpec("WORKS_ON", "person:vijaya", "venture:trading-firm"),
        EdgeSpec("WORKS_ON", "person:vijaya", "venture:content-firm"),
        EdgeSpec("HAS_SKILL", "person:chandra", "skill:python"),
        EdgeSpec("HAS_SKILL", "person:chandra", "skill:distributed-systems"),
        EdgeSpec("HAS_SKILL", "person:chandra", "skill:options-trading"),
        EdgeSpec("DECIDED", "person:chandra", "decision:mem0", {"date": "2026-06-04"}),
        EdgeSpec("DECIDED", "person:chandra", "decision:llp", {"date": "2026-05-01"}),
        EdgeSpec("TARGETS", "person:chandra", "goal:migration", {"deadline": "2026-12-01"}),
        EdgeSpec("TARGETS", "person:chandra", "goal:ai-role"),
        EdgeSpec("ACHIEVED", "person:chandra", "milestone:amazon-exit", {"date": "2026-07-01"}),
        EdgeSpec("USES", "person:chandra", "tool:mem0"),
        EdgeSpec("USES", "person:chandra", "tool:neo4j"),
        EdgeSpec("RELATED_TO", "decision:mem0", "venture:trading-firm"),
    ]
    for edge in edges:
        graph.add_edge(edge)

    return graph
