"""Rich CLI dashboard for AeroDrift scan results."""

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
    """Render scan metrics, drift status, and remediation guidance."""
    console = Console()
    console.print("\n[bold cyan]AeroDrift[/bold cyan] [dim]Agentic Cloud Topology & Remediation Graph[/dim]")

    metrics = Table(title="Topology Scan", box=box.ROUNDED)
    metrics.add_column("Metric", style="bold")
    metrics.add_column("Value", justify="right")
    metrics.add_row("Total nodes", str(topology.number_of_nodes()))
    metrics.add_row("Total edges", str(topology.number_of_edges()))
    metrics.add_row("Internet -> Database path", "YES" if finding.internet_to_database_path else "NO")
    metrics.add_row("Drift status", f"[red]{finding.status}[/red]" if finding.internet_to_database_path else f"[green]{finding.status}[/green]")
    console.print(metrics)

    status_style = "red" if finding.internet_to_database_path else "green"
    console.print(Panel(f"[{status_style}]{finding.message}[/{status_style}]", title="Security Check"))

    recommendations_table = Table(title="Remediation Recommendations", box=box.SIMPLE)
    recommendations_table.add_column("#", style="bold yellow", width=4)
    recommendations_table.add_column("Recommendation")
    for number, recommendation in enumerate(recommendations, start=1):
        recommendations_table.add_row(str(number), recommendation)
    console.print(recommendations_table)
