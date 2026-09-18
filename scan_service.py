"""Reusable AeroDrift scan orchestration for CLI and future web consumers."""

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rich.console import Console

from aws_data import load_mock_resources
from database import (
    get_latest_topology_diff,
    save_topology_snapshot,
    summarize_topology_diff,
)
from drift_detector import detect_security_drift
from graph_engine import apply_mock_security_group_drift, build_topology
from incident_report import generate_incident_report
from remediation import (
    RemediationInput,
    generate_recommendations,
    generate_remediation_code,
    run_remediation_workflow,
    validate_remediation_code,
)


def _serialize_topology(topology: Any) -> dict[str, list[dict[str, Any]]]:
    """Return the current graph as dashboard-friendly node and edge records."""
    return {
        "nodes": [
            {"id": node_id, **attributes}
            for node_id, attributes in topology.nodes(data=True)
        ],
        "edges": [
            {"source": source, "target": target, **attributes}
            for source, target, attributes in topology.edges(data=True)
        ],
    }


def _serialize_remediation(remediation_result: Any) -> dict[str, Any]:
    """Return existing remediation workflow values as plain dictionary data."""
    audit_record = remediation_result.audit_record
    action_metadata = audit_record.action_metadata
    return {
        "generated_action": audit_record.generated_code,
        "action_taken": remediation_result.action_taken,
        "details": remediation_result.remediation_summary,
        "validation_status": audit_record.validation_status,
        "execution_status": audit_record.execution_status,
        "validation_passed": remediation_result.validation_passed,
        "execution_attempted": remediation_result.execution_attempted,
        "success": remediation_result.success,
        "message": remediation_result.message,
        "result_summary": remediation_result.result_summary,
        "operation": remediation_result.operation,
        "audit": {
            "attempt_id": audit_record.attempt_id,
            "timestamp": audit_record.timestamp,
            "security_group_id": audit_record.security_group_id,
            "final_result": audit_record.final_result,
            "safety_decision": audit_record.safety_decision,
            "execution_timestamp": audit_record.execution_timestamp,
            "lifecycle_stage": audit_record.lifecycle_stage,
            "completion_summary": audit_record.completion_summary,
            "action_metadata": (
                {
                    "protocol": action_metadata.protocol,
                    "from_port": action_metadata.port_range[0],
                    "to_port": action_metadata.port_range[1],
                    "source_cidr": action_metadata.source_cidr,
                }
                if action_metadata is not None
                else None
            ),
        },
    }


def run_scan_service(console: Console | None = None) -> dict[str, Any]:
    """Run the existing scan workflow and return one structured result.

    The optional console preserves the existing CLI progress output. Web
    callers can omit it and receive the same scan data without terminal output.
    """
    scan_timestamp = datetime.now(timezone.utc).isoformat()

    if console is not None:
        console.print("[bold cyan]Loading mock AWS resources...[/bold cyan]")
    mock_resources = load_mock_resources()

    if console is not None:
        console.print("[bold cyan]Building cloud topology graph...[/bold cyan]")
    cloud_topology = build_topology(mock_resources)
    snapshot_id = save_topology_snapshot(cloud_topology)
    if console is not None:
        console.print(
            f"[bold green]Topology snapshot saved: {snapshot_id}[/bold green]"
        )
    topology_diff = get_latest_topology_diff()
    if console is not None:
        if topology_diff["status"] == "NO HISTORY":
            console.print(
                "[bold yellow]Historical topology comparison: NO HISTORY[/bold yellow]"
            )
        elif topology_diff["status"] == "NO CHANGE":
            console.print(
                "[bold green]Historical topology comparison: NO TOPOLOGY CHANGE[/bold green]"
            )
        else:
            console.print(
                "[bold yellow]Historical topology comparison: "
                f"{summarize_topology_diff(topology_diff['previous_snapshot_id'], topology_diff['latest_snapshot_id'])}[/bold yellow]"
            )

    if console is not None:
        console.print("[bold cyan]Testing mock security-group drift...[/bold cyan]")
    cloud_topology.remove_edge("sg-public", "web-server")
    restricted_finding = detect_security_drift(cloud_topology)
    if console is not None:
        console.print(f"Restricted topology: {restricted_finding.status}")
    apply_mock_security_group_drift(cloud_topology)
    security_group_rule = cloud_topology.edges["sg-public", "web-server"][
        "security_group_rule"
    ]
    if console is not None:
        console.print(f"Mock security-group rule changed to: {security_group_rule}")

    if console is not None:
        console.print("[bold cyan]Checking for security drift...[/bold cyan]")
    detection_started_at = time.perf_counter()
    drift_finding = detect_security_drift(cloud_topology)
    detection_elapsed_ms = (time.perf_counter() - detection_started_at) * 1000
    if console is not None:
        if detection_elapsed_ms < 5000:
            console.print(
                "[bold green]Audit target passed: detection completed under 5 seconds.[/bold green]"
            )
        else:
            console.print(
                "[bold yellow]Audit target warning: detection took 5 seconds or longer.[/bold yellow]"
            )

    remediation_data: dict[str, Any] | None = None
    report_path: Path | None = None
    if drift_finding.internet_to_database_path:
        detected_path = " -> ".join(
            str(cloud_topology.nodes[resource_id].get("name", resource_id))
            for resource_id in drift_finding.path
        )
        affected_resource_types = list(
            dict.fromkeys(
                cloud_topology.nodes[resource_id].get("resource_type", "Resource")
                for resource_id in drift_finding.path
            )
        )
        if console is not None:
            console.print("[bold red]Audit status: UNSAFE[/bold red]")
            console.print(
                f"[bold red]Detected Internet-to-Database path: {detected_path}[/bold red]"
            )
            console.print(
                "[bold red]Affected resource summary: "
                f"{len(drift_finding.path)} total; types: "
                f"{', '.join(affected_resource_types)}[/bold red]"
            )
            console.print(
                f"[bold cyan]Detection time: {detection_elapsed_ms:.3f} ms[/bold cyan]"
            )
        remediation_input = RemediationInput(
            security_group_id=drift_finding.affected_security_group or "",
            source_cidr=drift_finding.security_group_rule or "",
            protocol="tcp",
            from_port=80,
            to_port=80,
            reason="Revoke the unsafe public security-group ingress rule.",
        )
        remediation_source = generate_remediation_code(remediation_input)
        is_remediation_valid, remediation_message = validate_remediation_code(
            remediation_source
        )
        if console is not None:
            if is_remediation_valid:
                console.print(
                    "[bold green]Generated remediation code passed AST validation "
                    "and is ready for controlled execution.[/bold green]"
                )
            else:
                console.print(f"[bold red]{remediation_message}[/bold red]")
        remediation_result = run_remediation_workflow(remediation_source)
        report_path = generate_incident_report(
            cloud_topology,
            drift_finding,
            remediation_result,
        )
        if console is not None:
            console.print(
                f"[bold green]Incident PDF report generated: {report_path}[/bold green]"
            )
        remediation_data = _serialize_remediation(remediation_result)
    elif console is not None:
        console.print("[bold green]Audit status: SAFE[/bold green]")
        console.print("[bold green]No Internet-to-Database path detected.[/bold green]")
        console.print(
            f"[bold cyan]Detection time: {detection_elapsed_ms:.3f} ms[/bold cyan]"
        )

    recommendations = generate_recommendations(drift_finding)
    topology_data = _serialize_topology(cloud_topology)
    affected_resources = [
        {
            "id": resource_id,
            **cloud_topology.nodes[resource_id],
        }
        for resource_id in drift_finding.path
    ]
    security_group_details = {
        "id": drift_finding.affected_security_group,
        "rule": drift_finding.security_group_rule,
    }

    return {
        "topology": {
            **topology_data,
            "node_count": cloud_topology.number_of_nodes(),
            "edge_count": cloud_topology.number_of_edges(),
            "snapshot_id": snapshot_id,
        },
        "drift": {
            "status": drift_finding.status,
            "risk_level": "HIGH" if drift_finding.internet_to_database_path else "SAFE",
            "message": drift_finding.message,
            "internet_to_database_path": drift_finding.internet_to_database_path,
            "path": list(drift_finding.path),
            "affected_resources": affected_resources,
            "security_group": security_group_details,
            "recommendations": recommendations,
            "detection_elapsed_ms": detection_elapsed_ms,
        },
        "history": {
            "status": topology_diff["status"],
            "previous_snapshot_id": topology_diff["previous_snapshot_id"],
            "latest_snapshot_id": topology_diff["latest_snapshot_id"],
            "added_nodes": topology_diff["added_nodes"],
            "removed_nodes": topology_diff["removed_nodes"],
            "added_edges": topology_diff["added_edges"],
            "removed_edges": topology_diff["removed_edges"],
        },
        "remediation": remediation_data,
        "report": {
            "path": str(report_path) if report_path is not None else None,
            "generated": report_path is not None,
        },
        "timestamp": scan_timestamp,
    }