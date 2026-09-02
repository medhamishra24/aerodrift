"""Mock AWS resource collection for AeroDrift."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TypeAlias


Relationship: TypeAlias = tuple[str, str, str]


@dataclass(frozen=True)
class CloudResource:
    """Provider-neutral representation of one simulated cloud resource.

    Attributes:
        resource_id: Stable identifier used as the graph node key.
        name: Human-readable resource name for dashboard output.
        resource_type: Category of resource, such as ``Compute`` or ``Database``.
        description: Short explanation of the resource's role in the topology.
    """

    resource_id: str
    name: str
    resource_type: str
    description: str


def load_mock_resources() -> list[CloudResource]:
    """Load and validate the resources used by the demonstration scan.

    Returns:
        Five deterministic mock resources representing the Internet, security
        group, application tiers, and database.

    Raises:
        ValueError: If the built-in resource definitions fail validation.
    """
    resources: list[CloudResource] = [
        CloudResource(
            "internet", "Internet", "External", "Public internet entry point"
        ),
        CloudResource(
            "sg-public",
            "Public Security Group",
            "Security Group",
            "Allows inbound traffic from 0.0.0.0/0",
        ),
        CloudResource(
            "web-server", "Web Server", "Compute", "Public-facing web workload"
        ),
        CloudResource(
            "app-server",
            "Application Server",
            "Compute",
            "Internal application workload",
        ),
        CloudResource(
            "database", "Database", "Database", "Private customer data store"
        ),
    ]
    validate_resources(resources)
    return resources


def load_mock_relationships() -> list[Relationship]:
    """Load and validate directed relationships for the mock topology.

    Returns:
        Four deterministic relationships, including the intentionally unsafe
        route from the Internet to the Database.

    Raises:
        ValueError: If a relationship points to an unknown resource or has a
            blank label.
    """
    relationships: list[Relationship] = [
        ("internet", "sg-public", "internet ingress"),
        ("sg-public", "web-server", "allows traffic to"),
        ("web-server", "app-server", "application request"),
        ("app-server", "database", "database connection"),
    ]
    validate_relationships(relationships, load_mock_resources())
    return relationships


def load_mock_security_group_drift() -> Relationship:
    """Return the mock rule change that opens public application access.

    Returns:
        The security-group relationship that allows public inbound traffic.
    """
    return (
        "sg-public",
        "web-server",
        "allows public traffic (0.0.0.0/0)",
    )


def validate_resources(resources: Sequence[CloudResource]) -> None:
    """Validate resource identity and descriptive fields before graph creation.

    Args:
        resources: Resource records to validate before graph creation.

    Raises:
        ValueError: If the collection is empty, contains duplicate IDs, or has
            a blank required field.
    """
    if not resources:
        raise ValueError("At least one cloud resource is required")

    resource_ids: set[str] = set()
    required_fields: tuple[str, ...] = (
        "resource_id",
        "name",
        "resource_type",
        "description",
    )

    for resource in resources:
        if resource.resource_id in resource_ids:
            raise ValueError(f"Duplicate resource ID: {resource.resource_id}")
        resource_ids.add(resource.resource_id)

        for field_name in required_fields:
            field_value: object = getattr(resource, field_name)
            if not isinstance(field_value, str) or not field_value.strip():
                raise ValueError(f"Resource {field_name} must be a non-empty string")


def validate_relationships(
    relationships: Sequence[Relationship],
    resources: Sequence[CloudResource],
) -> None:
    """Validate relationship endpoints and labels against known resources.

    Args:
        relationships: Directed resource relationships to validate.
        resources: Resource records that define valid endpoint IDs.

    Raises:
        ValueError: If a relationship has an unknown endpoint or blank label.
    """
    known_resource_ids: set[str] = {
        resource.resource_id for resource in resources
    }

    for source_id, target_id, relationship_label in relationships:
        if source_id not in known_resource_ids:
            raise ValueError(f"Unknown relationship source: {source_id}")
        if target_id not in known_resource_ids:
            raise ValueError(f"Unknown relationship target: {target_id}")
        if not relationship_label.strip():
            raise ValueError("Relationship label must be a non-empty string")
