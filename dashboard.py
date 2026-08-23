"""Render AeroDrift scan results in a Rich terminal dashboard.

This module is responsible only for presentation. It receives the completed
topology analysis, drift finding, and remediation recommendations from the
other application modules, then displays those values as readable terminal
tables and a color-coded security status panel.
"""

import networkx as nx
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from drift_detector import DriftFinding


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

    The function does not perform analysis or modify the supplied values. Graph
    analysis and recommendation generation happen in their own modules, keeping
    this layer focused on CLI formatting.
    """
    cli_console = Console()
    cli_console.print(
        "\n[bold cyan]AeroDrift[/bold cyan] "
        "[dim]Agentic Cloud Topology & Remediation Graph[/dim]"
    )

    # Summarize the graph and security finding in a compact table for scanning.
    topology_metrics = Table(title="Topology Scan", box=box.ROUNDED)
    topology_metrics.add_column("Metric", style="bold")
    topology_metrics.add_column("Value", justify="right")
    topology_metrics.add_row("Total nodes", str(topology.number_of_nodes()))
    topology_metrics.add_row("Total edges", str(topology.number_of_edges()))
    topology_metrics.add_row(
        "Internet -> Database path",
        "YES" if finding.internet_to_database_path else "NO",
    )
    topology_metrics.add_row(
        "Drift status",
        (
            f"[red]{finding.status}[/red]"
            if finding.internet_to_database_path
            else f"[green]{finding.status}[/green]"
        ),
    )
    cli_console.print(topology_metrics)

    # Red draws attention to an exposed path; green indicates that no path was found.
    status_color = "red" if finding.internet_to_database_path else "green"
    status_panel = Panel(
        f"[{status_color}]{finding.message}[/{status_color}]",
        title="Security Check",
    )
    cli_console.print(status_panel)

    # Number each recommendation so the operator can discuss actions clearly.
    remediation_table = Table(title="Remediation Recommendations", box=box.SIMPLE)
    remediation_table.add_column("#", style="bold yellow", width=4)
    remediation_table.add_column("Recommendation")
    for recommendation_number, recommendation_text in enumerate(recommendations, start=1):
        remediation_table.add_row(str(recommendation_number), recommendation_text)
    cli_console.print(remediation_table)
