"""Mock AWS resource collection for AeroDrift."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CloudResource:
    """A small, provider-neutral representation of a cloud resource."""

    resource_id: str
    name: str
    resource_type: str
    description: str


def load_mock_resources() -> list[CloudResource]:
    """Return the resources used by the local demonstration scan."""
    return [
        CloudResource("internet", "Internet", "External", "Public internet entry point"),
        CloudResource("sg-public", "Public Security Group", "Security Group", "Allows inbound traffic from 0.0.0.0/0"),
        CloudResource("web-server", "Web Server", "Compute", "Public-facing web workload"),
        CloudResource("app-server", "Application Server", "Compute", "Internal application workload"),
        CloudResource("database", "Database", "Database", "Private customer data store"),
    ]


def load_mock_relationships() -> list[tuple[str, str, str]]:
    """Return directed relationships, including the intentionally unsafe route."""
    return [
        ("internet", "sg-public", "internet ingress"),
        ("sg-public", "web-server", "allows traffic to"),
        ("web-server", "app-server", "application request"),
        ("app-server", "database", "database connection"),
    ]
