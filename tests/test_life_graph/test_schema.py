"""Unit tests for LifeGraph schema validation."""

from __future__ import annotations

import pytest

from life_graph.schema import (
    EdgeSpec,
    LifeGraphSchemaError,
    NodeSpec,
    validate_edge,
    validate_node,
)


def test_validate_node_accepts_person() -> None:
    node = validate_node(NodeSpec("Person", "person:alex", {"name": "Alex"}))
    assert node.key == "person:alex"


def test_validate_node_rejects_unknown_label() -> None:
    with pytest.raises(LifeGraphSchemaError, match="label must be one of"):
        validate_node(NodeSpec("Company", "x", {"name": "Acme"}))


def test_validate_node_requires_name() -> None:
    with pytest.raises(LifeGraphSchemaError, match="requires a name"):
        validate_node(NodeSpec("Person", "person:x", {}))


def test_validate_edge_checks_endpoints() -> None:
    edge = EdgeSpec("WORKS_ON", "person:alex", "venture:alpha-corp")
    validate_edge(edge, known_keys={"person:alex", "venture:alpha-corp"})


def test_validate_edge_rejects_unknown_relationship() -> None:
    with pytest.raises(LifeGraphSchemaError, match="relationship must be one of"):
        validate_edge(EdgeSpec("OWNS", "a", "b"), known_keys={"a", "b"})
