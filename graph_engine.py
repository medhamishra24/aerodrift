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
    """Add one NetworkX node for each cloud resource.

    The resource ID becomes the stable node key used by reachability checks.
    Human-readable names and metadata are stored as node attributes so other
    modules can present useful resource details without rebuilding the input.

    Args:
        topology: Graph that receives the resource nodes.
        resources: Cloud resources to represent in the graph.
    """
    for resource in resources:
        # The ID is the machine-readable graph key; attributes preserve display data.
        topology.add_node(
            resource.resource_id,
            name=resource.name,
            resource_type=resource.resource_type,
            description=resource.description,
        )


def _add_resource_edges(topology: nx.DiGraph) -> None:
    """Add directed mock relationships and labels to ``topology``.

    Relationships are loaded centrally from ``aws_data`` so the graph uses the
    same mock route definitions as the rest of the application. The label is
    retained as edge metadata for inspection and future visualizations.

    Args:
        topology: Graph that receives the relationship edges.
    """
    for source_resource_id, target_resource_id, relationship_label in load_mock_relationships():
        # Edge direction represents the direction of traffic or communication.
        topology.add_edge(
            source_resource_id,
            target_resource_id,
            relationship=relationship_label,
        )



def describe_topology(topology: nx.DiGraph) -> list[str]:
    """Return human-readable descriptions of every directed topology edge.

    Args:
        topology: Graph whose edge endpoints have a ``name`` node attribute.

    Returns:
        Edge descriptions in NetworkX iteration order, suitable for CLI output
        or a future visualizer.
    """
    return [
        f"{topology.nodes[source_id]['name']} -> {topology.nodes[target_id]['name']}"
        for source_id, target_id in topology.edges
    ]
