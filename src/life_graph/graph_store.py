"""In-memory LifeGraph store for tests and local POC (Phase 6)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from life_graph.schema import EdgeSpec, NodeSpec, validate_edge, validate_node


@dataclass
class GraphStore:
    """Mutable in-memory graph keyed by stable node keys."""

    nodes: dict[str, dict[str, Any]] = field(default_factory=dict)
    edges: list[dict[str, Any]] = field(default_factory=list)

    def add_node(self, node: NodeSpec) -> None:
        validate_node(node)
        self.nodes[node.key] = {"label": node.label, **node.properties}

    def add_edge(self, edge: EdgeSpec) -> None:
        validate_edge(edge, known_keys=set(self.nodes))
        self.edges.append(
            {
                "relationship": edge.relationship,
                "source_key": edge.source_key,
                "target_key": edge.target_key,
                **edge.properties,
            }
        )

    def node_keys_for_label(self, label: str) -> list[str]:
        return [key for key, props in self.nodes.items() if props.get("label") == label]

    def neighbors(
        self,
        source_key: str,
        *,
        rel_type: str | None = None,
        direction: str = "out",
    ) -> list[str]:
        keys: list[str] = []
        for edge in self.edges:
            if (
                direction in {"out", "both"}
                and edge["source_key"] == source_key
                and (rel_type is None or edge["relationship"] == rel_type)
            ):
                keys.append(edge["target_key"])
            if (
                direction in {"in", "both"}
                and edge["target_key"] == source_key
                and (rel_type is None or edge["relationship"] == rel_type)
            ):
                keys.append(edge["source_key"])
        return keys
