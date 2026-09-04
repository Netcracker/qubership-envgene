"""Parse --tenant CLI values into a deduplicated tenant list."""

from __future__ import annotations


def parse_tenant_values(values: tuple[str, ...]) -> list[str]:
    """Expand comma-separated and repeated ``--tenant`` flags into one list."""
    tenants: list[str] = []
    for raw in values:
        for part in raw.split(","):
            name = part.strip()
            if name:
                tenants.append(name)

    seen: set[str] = set()
    unique: list[str] = []
    for tenant in tenants:
        if tenant not in seen:
            seen.add(tenant)
            unique.append(tenant)
    return unique
