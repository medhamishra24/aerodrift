"""NetworkX topology construction for AeroDrift."""

import networkx as nx

from aws_data import CloudResource, load_mock_relationships


def build_topology(resources: list[CloudResource]) -> nx.DiGraph:
    """Build a directed graph from resources and their relationships."""
    topology = nx.DiGraph()

    for resource in resources:
        topology.add_node(
            resource.resource_id,
            name=resource.name,
            resource_type=resource.resource_type,
            description=resource.description,
        )

    for source, target, relationship in load_mock_relationships():
        topology.add_edge(source, target, relationship=relationship)

    return topology


def describe_topology(topology: nx.DiGraph) -> list[str]:
    """Return readable edge descriptions for CLI output or future visualizers."""
    return [
        f"{topology.nodes[source]['name']} -> {topology.nodes[target]['name']}"
        for source, target in topology.edges
    ]
