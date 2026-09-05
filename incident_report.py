"""Generate local PDF incident reports for detected AeroDrift drift."""

from datetime import datetime, timezone
from pathlib import Path

import networkx as nx
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from drift_detector import DriftFinding
from remediation import RemediationWorkflowResult


REPORT_PATH = Path(__file__).parent / "data" / "aerodrift_incident_report.pdf"


def generate_incident_report(
    topology: nx.DiGraph,
    finding: DriftFinding,
    remediation_result: RemediationWorkflowResult,
    output_path: Path = REPORT_PATH,
) -> Path:
    """Write a readable local PDF report for one detected drift incident."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "IncidentTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#17324D"),
        spaceAfter=16,
    )
    body_style = styles["BodyText"]
    body_style.leading = 15
    small_style = ParagraphStyle(
        "IncidentSmall",
        parent=body_style,
        fontSize=8,
        leading=10,
    )

    path_labels = [
        str(topology.nodes[resource_id].get("name", resource_id))
        for resource_id in finding.path
    ]
    target_rule = (
        f"{finding.security_group_rule or 'unknown'} on "
        f"{finding.affected_security_group or 'unknown'}"
    )
    generated_action = remediation_result.audit_record.generated_code or "Unavailable"
    report_timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

    story = [
        Paragraph("AeroDrift Security Drift Incident", title_style),
        Paragraph("Automated local incident report", body_style),
        Spacer(1, 0.15 * inch),
    ]
    details = [
        ("Report timestamp", report_timestamp),
        ("Affected security group", finding.affected_security_group or "Unknown"),
        ("Detected unsafe rule", target_rule),
        ("Topology path", " -> ".join(path_labels) or "Unavailable"),
        ("AST validation", remediation_result.audit_record.validation_status),
        ("Controlled execution", remediation_result.audit_record.execution_status),
        ("Final remediation status", remediation_result.audit_record.final_result),
    ]
    table_data = [[Paragraph(label, body_style), Paragraph(value, body_style)] for label, value in details]
    table = Table(table_data, colWidths=[1.8 * inch, 5.2 * inch], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E8F0F7")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#6B8194")),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#B7C5D0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.extend([table, Spacer(1, 0.2 * inch)])
    story.append(Paragraph("Generated remediation action", styles["Heading2"]))
    story.append(Paragraph(generated_action.replace("&", "&amp;"), small_style))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("Finding", styles["Heading2"]))
    story.append(Paragraph(finding.message, body_style))

    SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=0.7 * inch,
        leftMargin=0.7 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
        title="AeroDrift Security Drift Incident",
        author="AeroDrift",
    ).build(story)
    return output_path
