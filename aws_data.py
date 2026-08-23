"""Mock AWS resource collection for AeroDrift."""

from dataclasses import dataclass
from collections.abc import Sequence


Relationship = tuple[str, str, str]


@dataclass(frozen=True)
class CloudResource:
    """A small, provider-neutral representation of a cloud resource."""

    resource_id: str
    name: str
    resource_type: str
    description: str


def load_mock_resources() -> list[CloudResource]:
    """Return the resources used by the local demonstration scan."""
    resources = [
        CloudResource("internet", "Internet", "External", "Public internet entry point"),
        CloudResource("sg-public", "Public Security Group", "Security Group", "Allows inbound traffic from 0.0.0.0/0"),
        CloudResource("web-server", "Web Server", "Compute", "Public-facing web workload"),
        CloudResource("app-server", "Application Server", "Compute", "Internal application workload"),
        CloudResource("database", "Database", "Database", "Private customer data store"),
    ]
    validate_resources(resources)
    return resources


def load_mock_relationships() -> list[Relationship]:
    """Return directed relationships, including the intentionally unsafe route."""
    relationships = [
        ("internet", "sg-public", "internet ingress"),
        ("sg-public", "web-server", "allows traffic to"),
        ("web-server", "app-server", "application request"),
        ("app-server", "database", "database connection"),
    ]
    validate_relationships(relationships, load_mock_resources())
    return relationships


def validate_resources(resources: Sequence[CloudResource]) -> None:
    """Validate resource identity and descriptive fields before graph creation.

    Raises:
        ValueError: If the collection is empty, contains duplicate IDs, or has
            a blank required field.
    """
    if not resources:
        raise ValueError("At least one cloud resource is required")

    resource_ids: set[str] = set()
    required_fields = ("resource_id", "name", "resource_type", "description")

    for resource in resources:
        # Stable unique IDs are required because NetworkX uses them as node keys.
        if resource.resource_id in resource_ids:
            raise ValueError(f"Duplicate resource ID: {resource.resource_id}")
        resource_ids.add(resource.resource_id)

        for field_name in required_fields:
            field_value = getattr(resource, field_name)
            if not isinstance(field_value, str) or not field_value.strip():
                raise ValueError(f"Resource {field_name} must be a non-empty string")


def validate_relationships(
    relationships: Sequence[Relationship],
    resources: Sequence[CloudResource],
) -> None:
    """Validate relationship endpoints and labels against known resources.

    Raises:
        ValueError: If a relationship has an unknown endpoint or blank label.
    """
    known_resource_ids = {resource.resource_id for resource in resources}

    for source_id, target_id, relationship_label in relationships:
        # Reject dangling edges early so topology analysis cannot silently omit data.
        if source_id not in known_resource_ids:
            raise ValueError(f"Unknown relationship source: {source_id}")
        if target_id not in known_resource_ids:
            raise ValueError(f"Unknown relationship target: {target_id}")
        if not relationship_label.strip():
            raise ValueError("Relationship label must be a non-empty string")
