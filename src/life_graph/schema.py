"""LifeGraph node/edge schema (ADR 005 / Phase 6)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

NODE_LABELS = frozenset(
    {"Person", "Venture", "Skill", "Decision", "Milestone", "Goal", "Tool"}
)

RELATIONSHIP_TYPES = frozenset(
    {
        "CO_FOUNDER",
        "WORKS_ON",
        "HAS_SKILL",
        "DECIDED",
        "ACHIEVED",
        "TARGETS",
        "USES",
        "RELATED_TO",
    }
)


class LifeGraphSchemaError(ValueError):
    """Raised when graph data violates the LifeGraph schema."""


@dataclass(frozen=True)
class NodeSpec:
    label: str
    key: str
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EdgeSpec:
    relationship: str
    source_key: str
    target_key: str
    properties: dict[str, Any] = field(default_factory=dict)


def validate_label(label: str) -> str:
    if label not in NODE_LABELS:
        raise LifeGraphSchemaError(
            f"label must be one of {sorted(NODE_LABELS)}, got {label!r}"
        )
    return label


def validate_relationship(relationship: str) -> str:
    if relationship not in RELATIONSHIP_TYPES:
        raise LifeGraphSchemaError(
            f"relationship must be one of {sorted(RELATIONSHIP_TYPES)}, got "
            f"{relationship!r}"
        )
    return relationship


def validate_node(node: NodeSpec) -> NodeSpec:
    validate_label(node.label)
    if not node.key.strip():
        raise LifeGraphSchemaError("node key must not be empty")
    name = node.properties.get("name")
    if not name or not str(name).strip():
        raise LifeGraphSchemaError(f"node {node.key!r} requires a name property")
    return node


def validate_edge(edge: EdgeSpec, *, known_keys: set[str] | None = None) -> EdgeSpec:
    validate_relationship(edge.relationship)
    if not edge.source_key.strip() or not edge.target_key.strip():
        raise LifeGraphSchemaError("edge source_key and target_key are required")
    if known_keys is not None:
        if edge.source_key not in known_keys:
            raise LifeGraphSchemaError(f"unknown source node {edge.source_key!r}")
        if edge.target_key not in known_keys:
            raise LifeGraphSchemaError(f"unknown target node {edge.target_key!r}")
    return edge
