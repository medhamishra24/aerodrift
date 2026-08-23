"""NetworkX topology construction for AeroDrift."""

import networkx as nx

from aws_data import CloudResource, load_mock_relationships


def build_topology(resources: list[CloudResource]) -> nx.DiGraph:
    """Build a directed cloud topology from resources and mock relationships.

    Each resource becomes a graph node keyed by its stable ``resource_id``.
    The remaining resource fields are retained as node attributes so dashboard
    code and future visualizers can display useful context. Relationships are
    directed because traffic flowing from one resource to another is relevant
    to reachability checks such as Internet-to-Database analysis.

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
    resources: list[CloudResource],
) -> None:
    """Add resource nodes and descriptive attributes to ``topology``."""
    for resource in resources:
        # The ID is the machine-readable graph key; attributes preserve display data.
        topology.add_node(
            resource.resource_id,
            name=resource.name,
            resource_type=resource.resource_type,
            description=resource.description,
        )


def _add_resource_edges(topology: nx.DiGraph) -> None:
    """Add directed mock relationships and their labels to ``topology``."""
    for source, target, relationship in load_mock_relationships():
        # Edge direction represents the direction of traffic or communication.
        topology.add_edge(source, target, relationship=relationship)



def describe_topology(topology: nx.DiGraph) -> list[str]:
    """Return human-readable descriptions of every directed topology edge.

    Args:
        topology: Graph whose edge endpoints have a ``name`` node attribute.

    Returns:
        Edge descriptions in NetworkX iteration order, suitable for CLI output
        or a future visualizer.
    """
    return [
        f"{topology.nodes[source]['name']} -> {topology.nodes[target]['name']}"
        for source, target in topology.edges
    ]
