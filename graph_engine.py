"""NetworkX topology construction for AeroDrift."""

from collections.abc import Sequence

import networkx as nx

from aws_data import CloudResource, load_mock_relationships


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
