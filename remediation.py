"""Remediation suggestions and code generation for drift findings."""

import ast
import ipaddress
from dataclasses import dataclass

from drift_detector import DriftFinding


@dataclass(frozen=True)
class RemediationInput:
    """Validated details for revoking an unsafe security-group rule."""

    security_group_id: str
    source_cidr: str
    protocol: str
    from_port: int
    to_port: int
    reason: str

    def __post_init__(self) -> None:
        """Reject values that cannot describe a safe remediation request."""
        for field_name in (
            "security_group_id",
            "protocol",
            "reason",
        ):
            field_value = getattr(self, field_name)
            if not isinstance(field_value, str) or not field_value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")

        try:
            ipaddress.ip_network(self.source_cidr, strict=False)
        except (TypeError, ValueError) as error:
            raise ValueError("source_cidr must be a valid CIDR") from error

        protocol = self.protocol.strip().lower()
        valid_protocol_names = {"-1", "tcp", "udp", "icmp", "icmpv6"}
        if protocol not in valid_protocol_names:
            try:
                protocol_number = int(protocol)
            except ValueError as error:
                raise ValueError("protocol must be a valid IP protocol") from error
            if not 0 <= protocol_number <= 255:
                raise ValueError("protocol number must be between 0 and 255")

        if not isinstance(self.from_port, int) or isinstance(self.from_port, bool):
            raise ValueError("from_port must be an integer")
        if not isinstance(self.to_port, int) or isinstance(self.to_port, bool):
            raise ValueError("to_port must be an integer")
        if not 0 <= self.from_port <= 65535:
            raise ValueError("from_port must be between 0 and 65535")
        if not 0 <= self.to_port <= 65535:
            raise ValueError("to_port must be between 0 and 65535")
        if self.from_port > self.to_port:
            raise ValueError("from_port must not exceed to_port")


def generate_remediation_code(remediation: RemediationInput) -> str:
    """Return reviewable AST-generated code for revoking a security rule."""
    revoke_call = ast.Call(
        func=ast.Attribute(
            value=ast.Name(id="ec2", ctx=ast.Load()),
            attr="revoke_security_group_ingress",
            ctx=ast.Load(),
        ),
        args=[],
        keywords=[
            ast.keyword(
                arg="GroupId",
                value=ast.Constant(value=remediation.security_group_id),
            ),
            ast.keyword(
                arg="IpPermissions",
                value=ast.List(
                    elts=[
                        ast.Dict(
                            keys=[
                                ast.Constant(value="IpProtocol"),
                                ast.Constant(value="FromPort"),
                                ast.Constant(value="ToPort"),
                                ast.Constant(value="IpRanges"),
                            ],
                            values=[
                                ast.Constant(value=remediation.protocol),
                                ast.Constant(value=remediation.from_port),
                                ast.Constant(value=remediation.to_port),
                                ast.List(
                                    elts=[
                                        ast.Dict(
                                            keys=[ast.Constant(value="CidrIp")],
                                            values=[
                                                ast.Constant(
                                                    value=remediation.source_cidr
                                                )
                                            ],
                                        )
                                    ],
                                    ctx=ast.Load(),
                                ),
                            ],
                        )
                    ],
                    ctx=ast.Load(),
                ),
            ),
        ],
    )
    module = ast.Module(
        body=[
            ast.Import(names=[ast.alias(name="boto3")]),
            ast.Assign(
                targets=[ast.Name(id="ec2", ctx=ast.Store())],
                value=ast.Call(
                    func=ast.Attribute(
                        value=ast.Name(id="boto3", ctx=ast.Load()),
                        attr="client",
                        ctx=ast.Load(),
                    ),
                    args=[ast.Constant(value="ec2")],
                    keywords=[],
                ),
            ),
            ast.Expr(value=revoke_call),
        ],
        type_ignores=[],
    )
    return ast.unparse(ast.fix_missing_locations(module))


def generate_recommendations(finding: DriftFinding) -> list[str]:
    """Generate remediation guidance from a security drift finding.

    Args:
        finding: Result of the Internet-to-Database reachability check.

    Returns:
        An ordered list of recommendations for the detected security state.
    """
    public_database_path_exists: bool = finding.internet_to_database_path

    if not public_database_path_exists:
        return ["Continue monitoring network paths and security group changes."]

    return [
        "Close the open security group to public inbound traffic.",
        "Restrict public access to approved IP ranges or trusted services.",
        "Remove the unnecessary Internet-to-Database route.",
    ]
