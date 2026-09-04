"""Remediation suggestions and code generation for drift findings."""

import ast
import ipaddress
from dataclasses import dataclass
from typing import Any

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
    """Return validated-input AST source for a mock-safe ingress revocation."""
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


@dataclass(frozen=True)
class RemediationExecutionResult:
    """Result of evaluating remediation code against the local mock client."""

    success: bool
    message: str
    operation: dict[str, Any] | None = None


class _LocalEc2Client:
    """Capture the allowed remediation operation without contacting AWS."""

    def __init__(self) -> None:
        self.operation: dict[str, Any] | None = None

    def revoke_security_group_ingress(self, **kwargs: Any) -> None:
        self.operation = kwargs


class _LocalBoto3:
    """Minimal local replacement for the generated code's boto3 dependency."""

    def __init__(self) -> None:
        self.client_instance = _LocalEc2Client()

    def client(self, service_name: str) -> _LocalEc2Client:
        if service_name != "ec2":
            raise ValueError("Only the local EC2 mock is allowed")
        return self.client_instance


def _validate_remediation_ast(source: str) -> ast.Module:
    """Parse and enforce the exact AST shape produced by the generator."""
    tree = ast.parse(source, mode="exec")
    if len(tree.body) != 3:
        raise ValueError("Remediation code must contain exactly three statements")

    import_node, assignment_node, call_node = tree.body
    if not (
        isinstance(import_node, ast.Import)
        and len(import_node.names) == 1
        and import_node.names[0].name == "boto3"
        and import_node.names[0].asname is None
    ):
        raise ValueError("Only the boto3 import is allowed")

    if not (
        isinstance(assignment_node, ast.Assign)
        and len(assignment_node.targets) == 1
        and isinstance(assignment_node.targets[0], ast.Name)
        and assignment_node.targets[0].id == "ec2"
        and isinstance(assignment_node.value, ast.Call)
        and isinstance(assignment_node.value.func, ast.Attribute)
        and isinstance(assignment_node.value.func.value, ast.Name)
        and assignment_node.value.func.value.id == "boto3"
        and assignment_node.value.func.attr == "client"
        and len(assignment_node.value.args) == 1
        and isinstance(assignment_node.value.args[0], ast.Constant)
        and assignment_node.value.args[0].value == "ec2"
        and not assignment_node.value.keywords
    ):
        raise ValueError("Only the local EC2 client assignment is allowed")

    if not (
        isinstance(call_node, ast.Expr)
        and isinstance(call_node.value, ast.Call)
        and isinstance(call_node.value.func, ast.Attribute)
        and isinstance(call_node.value.func.value, ast.Name)
        and call_node.value.func.value.id == "ec2"
        and call_node.value.func.attr == "revoke_security_group_ingress"
        and not call_node.value.args
        and [keyword.arg for keyword in call_node.value.keywords]
        == ["GroupId", "IpPermissions"]
    ):
        raise ValueError("Only security-group ingress revocation is allowed")

    try:
        group_id = ast.literal_eval(call_node.value.keywords[0].value)
        ip_permissions = ast.literal_eval(call_node.value.keywords[1].value)
    except (ValueError, TypeError, SyntaxError) as error:
        raise ValueError("Remediation arguments must contain literals only") from error

    if (
        not isinstance(group_id, str)
        or not group_id.strip()
        or not isinstance(ip_permissions, list)
    ):
        raise ValueError("Remediation arguments have an invalid shape")
    if len(ip_permissions) != 1 or not isinstance(ip_permissions[0], dict):
        raise ValueError("Exactly one ingress permission is required")
    if set(ip_permissions[0]) != {
        "IpProtocol",
        "FromPort",
        "ToPort",
        "IpRanges",
    }:
        raise ValueError("Ingress permission fields are not allowed")
    permission = ip_permissions[0]
    protocol = permission["IpProtocol"]
    from_port = permission["FromPort"]
    to_port = permission["ToPort"]
    if not isinstance(protocol, str) or not protocol.strip():
        raise ValueError("IpProtocol must be a non-empty string")
    if (
        not isinstance(from_port, int)
        or isinstance(from_port, bool)
        or not isinstance(to_port, int)
        or isinstance(to_port, bool)
        or not 0 <= from_port <= 65535
        or not 0 <= to_port <= 65535
        or from_port > to_port
    ):
        raise ValueError("Ingress ports must be an ordered range from 0 to 65535")
    ip_ranges = ip_permissions[0]["IpRanges"]
    if (
        not isinstance(ip_ranges, list)
        or len(ip_ranges) != 1
        or not isinstance(ip_ranges[0], dict)
        or set(ip_ranges[0]) != {"CidrIp"}
        or not isinstance(ip_ranges[0]["CidrIp"], str)
    ):
        raise ValueError("Exactly one CIDR range is required")
    try:
        ipaddress.ip_network(ip_ranges[0]["CidrIp"], strict=False)
    except (TypeError, ValueError) as error:
        raise ValueError("CidrIp must be a valid CIDR") from error

    return tree


def validate_remediation_code(source: str) -> tuple[bool, str]:
    """Validate remediation source without executing it."""
    try:
        _validate_remediation_ast(source)
    except (SyntaxError, ValueError) as error:
        return False, f"Rejected remediation code: {error}"
    return True, "Remediation code passed AST validation."


@dataclass(frozen=True)
class RemediationPreparationResult:
    """Result of preparing remediation from an existing drift finding."""

    drift_detected: bool
    validation_passed: bool
    execution_attempted: bool
    ready_for_execution: bool
    source_code: str | None
    message: str


def prepare_remediation_from_finding(
    finding: DriftFinding,
) -> RemediationPreparationResult:
    """Prepare validated remediation source for an unsafe drift finding.

    The function only generates and validates source code. It never invokes
    the controlled execution function.

    Args:
        finding: Existing result from :func:`detect_security_drift`.

    Returns:
        A structured preparation result containing source code only when an
        unsafe finding has valid security-group information.
    """
    if not finding.internet_to_database_path:
        return RemediationPreparationResult(
            drift_detected=False,
            validation_passed=False,
            execution_attempted=False,
            ready_for_execution=False,
            source_code=None,
            message="No drift detected; remediation was not generated.",
        )

    if not isinstance(finding.affected_security_group, str) or not finding.affected_security_group.strip():
        return RemediationPreparationResult(
            drift_detected=True,
            validation_passed=False,
            execution_attempted=False,
            ready_for_execution=False,
            source_code=None,
            message="Rejected remediation: affected security group is missing.",
        )
    if not isinstance(finding.security_group_rule, str) or not finding.security_group_rule.strip():
        return RemediationPreparationResult(
            drift_detected=True,
            validation_passed=False,
            execution_attempted=False,
            ready_for_execution=False,
            source_code=None,
            message="Rejected remediation: security-group CIDR is missing.",
        )

    try:
        remediation_input = RemediationInput(
            security_group_id=finding.affected_security_group,
            source_cidr=finding.security_group_rule,
            protocol="tcp",
            from_port=80,
            to_port=80,
            reason="Revoke the unsafe public security-group ingress rule.",
        )
        source_code = generate_remediation_code(remediation_input)
    except ValueError as error:
        return RemediationPreparationResult(
            drift_detected=True,
            validation_passed=False,
            execution_attempted=False,
            ready_for_execution=False,
            source_code=None,
            message=f"Rejected remediation: {error}",
        )

    is_valid, validation_message = validate_remediation_code(source_code)
    return RemediationPreparationResult(
        drift_detected=True,
        validation_passed=is_valid,
        execution_attempted=False,
        ready_for_execution=is_valid,
        source_code=source_code if is_valid else None,
        message=validation_message,
    )


def execute_remediation_code(source: str) -> RemediationExecutionResult:
    """Execute approved remediation code against a local-only mock client."""
    is_valid, validation_message = validate_remediation_code(source)
    if not is_valid:
        return RemediationExecutionResult(False, validation_message)

    local_boto3 = _LocalBoto3()

    def restricted_import(
        name: str,
        globals: dict[str, Any] | None = None,
        locals: dict[str, Any] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> _LocalBoto3:
        if name != "boto3" or level != 0 or fromlist:
            raise ImportError("Only the local boto3 mock is allowed")
        return local_boto3

    sandbox_globals: dict[str, Any] = {
        "__builtins__": {"__import__": restricted_import}
    }
    try:
        exec(compile(source, "<remediation-sandbox>", "exec"), sandbox_globals)
    except Exception as error:
        return RemediationExecutionResult(False, f"Sandbox execution failed: {error}")

    return RemediationExecutionResult(
        True,
        "Remediation executed against the local mock client.",
        local_boto3.client_instance.operation,
    )


@dataclass(frozen=True)
class RemediationWorkflowResult:
    """Validation and local execution outcome for remediation source."""

    validation_passed: bool
    execution_attempted: bool
    success: bool
    message: str
    operation: dict[str, Any] | None = None


def run_remediation_workflow(source: str) -> RemediationWorkflowResult:
    """Validate source, then execute it only through the local mock sandbox."""
    is_valid, validation_message = validate_remediation_code(source)
    if not is_valid:
        return RemediationWorkflowResult(
            validation_passed=False,
            execution_attempted=False,
            success=False,
            message=validation_message,
        )

    execution_result = execute_remediation_code(source)
    return RemediationWorkflowResult(
        validation_passed=True,
        execution_attempted=True,
        success=execution_result.success,
        message=execution_result.message,
        operation=execution_result.operation,
    )


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
