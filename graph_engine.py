"""NetworkX topology construction for AeroDrift."""

from collections.abc import Sequence

import networkx as nx

from aws_data import (
    CloudResource,
    load_mock_relationships,
    load_mock_security_group_drift,
)


def build_topology(resources: Sequence[CloudResource]) -> nx.DiGraph:
    """Build a directed topology from resources and mock relationships.

    Args:
        resources: Cloud resources to add to the topology.

    Returns:
        A directed NetworkX graph containing the supplied resources and their
        mock relationships.
    """
    topology = nx.DiGraph()
    _add_resource_nodes(topology, resources)
    _add_resource_edges(topology)
    return topology


def apply_mock_security_group_drift(topology: nx.DiGraph) -> None:
    """Apply an opt-in public security-group rule change to ``topology``.

    The scenario updates the existing security-group relationship, or adds it
    when testing against a restricted topology. It uses only local mock data.

    Args:
        topology: Existing graph whose security-group rule should be changed.

    Raises:
        ValueError: If the mock security-group or web-server nodes are absent.
    """
    source_id, target_id, relationship = load_mock_security_group_drift()
    if not topology.has_node(source_id) or not topology.has_node(target_id):
        raise ValueError(
            "Mock security-group drift requires sg-public and web-server"
        )

    topology.add_edge(
        source_id,
        target_id,
        relationship=relationship,
        security_group_rule="0.0.0.0/0",
    )


def _add_resource_nodes(
    topology: nx.DiGraph,
    resources: Sequence[CloudResource],
) -> None:
    """Add resource nodes and their display metadata to ``topology``.

    Args:
        topology: Graph that receives the resource nodes.
        resources: Cloud resources to represent in the graph.
    """
    for resource in resources:
        topology.add_node(
            resource.resource_id,
            name=resource.name,
            resource_type=resource.resource_type,
            description=resource.description,
        )


def _add_resource_edges(topology: nx.DiGraph) -> None:
    """Add directed mock relationships and labels to ``topology``.

    Args:
        topology: Graph that receives the relationship edges.
    """
    for (
        source_resource_id,
        target_resource_id,
        relationship_label,
    ) in load_mock_relationships():
        topology.add_edge(
            source_resource_id,
            target_resource_id,
            relationship=relationship_label,
        )


def describe_topology(topology: nx.DiGraph) -> list[str]:
    """Return human-readable descriptions of the topology's directed edges.

    Args:
        topology: Graph whose edge endpoints have a ``name`` node attribute.

    Returns:
        Edge descriptions in NetworkX iteration order.
    """
    return [
        f"{topology.nodes[source_id]['name']} -> {topology.nodes[target_id]['name']}"
        for source_id, target_id in topology.edges
    ]
