"""Render AeroDrift scan results in a Rich terminal dashboard.

This module is responsible only for presentation. It receives the completed
topology analysis, drift finding, and remediation recommendations from the
other application modules, then displays those values as readable terminal
tables and a color-coded security status panel.
"""

import networkx as nx
from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from drift_detector import DriftFinding


def _resource_label(topology: nx.DiGraph, resource_id: object) -> str:
    """Return a readable label for one topology node."""
    resource_data = topology.nodes[resource_id]
    resource_type = resource_data.get("resource_type", "Resource")
    resource_name = resource_data.get("name", resource_id)
    return f"{resource_type}: {resource_name} ({resource_id})"


def _resource_text(
    topology: nx.DiGraph,
    resource_id: object,
    affected_resource_ids: set[object],
) -> Text:
    """Return a styled resource label for dashboard output."""
    resource_style = (
        "bold yellow" if resource_id in affected_resource_ids else None
    )
    return Text(_resource_label(topology, resource_id), style=resource_style)


def _build_topology_tree(
    topology: nx.DiGraph,
    affected_resource_ids: set[object] | None = None,
) -> Tree | None:
    """Build a Rich tree from the existing directed topology graph."""
    if not topology:
        return None

    tree = Tree("[bold cyan]Cloud topology[/bold cyan]")
    affected_resource_ids = affected_resource_ids or set()
    visited: set[object] = set()

    def add_branch(parent: Tree, resource_id: object, path: set[object]) -> None:
        if resource_id in path:
            return

        branch = parent.add(
            _resource_text(topology, resource_id, affected_resource_ids)
        )
        visited.add(resource_id)
        next_path = path | {resource_id}
        for child_id in topology.successors(resource_id):
            relationship = topology.edges[resource_id, child_id].get("relationship")
            child_label = relationship or "connected to"
            child_branch = branch.add(f"[dim]-- {child_label} -->[/dim]")
            add_branch(child_branch, child_id, next_path)

    root_ids = [
        resource_id
        for resource_id in topology
        if topology.in_degree(resource_id) == 0
    ]
    for root_id in root_ids:
        add_branch(tree, root_id, set())

    for resource_id in topology:
        if resource_id not in visited:
            add_branch(tree, resource_id, set())

    return tree


def display_dashboard(
    topology: nx.DiGraph,
    finding: DriftFinding,
    recommendations: list[str],
) -> None:
    """Render one completed scan as a readable Rich terminal dashboard.

    Args:
        topology: Directed graph whose node and edge counts summarize the scan.
        finding: Security reachability result produced by the drift detector.
        recommendations: Remediation messages generated for the finding.

    The function presents results; analysis and recommendation generation happen
    in their own modules.
    """
    cli_console = Console()
    drift_detected: bool = finding.internet_to_database_path
    cli_console.print(
        "\n[bold cyan]AeroDrift[/bold cyan] "
        "[dim]Agentic Cloud Topology & Remediation Graph[/dim]"
    )

    topology_metrics = Table(title="Topology Scan", box=box.ROUNDED)
    topology_metrics.add_column("Metric", style="bold")
    topology_metrics.add_column("Value", justify="right")
    topology_metrics.add_row("Total nodes", str(topology.number_of_nodes()))
    topology_metrics.add_row("Total edges", str(topology.number_of_edges()))
    topology_metrics.add_row(
        "Internet -> Database path",
        "YES" if drift_detected else "NO",
    )
    topology_metrics.add_row(
        "Drift status",
        (
            f"[red]{finding.status}[/red]"
            if drift_detected
            else f"[green]{finding.status}[/green]"
        ),
    )
    cli_console.print(topology_metrics)

    affected_resource_ids = set(finding.path) if drift_detected else set()
    topology_tree = _build_topology_tree(topology, affected_resource_ids)
    if topology_tree is None:
        topology_content = Text("Cloud topology is empty.", style="yellow")
    else:
        topology_content = topology_tree
    cli_console.print(
        Panel(
            topology_content,
            title="Topology Tree",
            border_style="cyan",
        )
    )

    if drift_detected:
        path_text = Text("\n").join(
            Text(f"{resource_number}. ").append(
                _resource_text(topology, resource_id, affected_resource_ids)
            )
            for resource_number, resource_id in enumerate(finding.path, start=1)
        )
        affected_resources_table = Table(
            title="Affected Resources",
            box=box.SIMPLE,
        )
        affected_resources_table.add_column("#", style="bold yellow", width=4)
        affected_resources_table.add_column("Resource")
        for resource_number, resource_id in enumerate(finding.path, start=1):
            affected_resources_table.add_row(
                str(resource_number),
                _resource_label(topology, resource_id),
            )
        status_panel = Panel(
            Group(
                Text("SECURITY DRIFT DETECTED", style="bold white on red"),
                Text("Audit result: UNSAFE", style="bold white on red"),
                Text(finding.message, style="bold red"),
                Text("Affected Internet-to-Database path:", style="bold"),
                Text(f"Affected resources: {len(finding.path)}", style="bold"),
                Text(
                    f"Public ingress rule: source CIDR {finding.security_group_rule or 'unknown'}",
                    style="bold",
                ),
                Text(
                    f"Affected security group: {finding.affected_security_group or 'unknown'}",
                    style="bold",
                ),
                affected_resources_table,
                Text("Ordered path:", style="bold"),
                path_text,
            ),
            title="Security Check",
            border_style="red",
        )
    else:
        status_panel = Panel(
            Group(
                Text("NO SECURITY DRIFT DETECTED", style="bold green"),
                Text("Audit result: SAFE", style="bold green"),
            ),
            title="Security Check: No Drift",
            border_style="green",
        )
    cli_console.print(status_panel)

    remediation_table = Table(title="Remediation Recommendations", box=box.SIMPLE)
    remediation_table.add_column("#", style="bold yellow", width=4)
    remediation_table.add_column("Recommendation")
    for recommendation_number, recommendation_text in enumerate(recommendations, start=1):
        remediation_table.add_row(str(recommendation_number), recommendation_text)
    cli_console.print(
        Panel(
            remediation_table,
            title="Remediation",
            border_style="yellow",
        )
    )
