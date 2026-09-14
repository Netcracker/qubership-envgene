"""PLACE-7: One category per ParameterSet."""

from __future__ import annotations

from collections import defaultdict

from ..connections import Connections, compute_connections
from ..discovery import ENV_DEFINITION_FILE, INVENTORY_DIR
from ..model import Category, Finding, Location, RepoIndex, Severity
from ..rulemeta import RULES
from ..yamlio import YamlReadError, load

_HINT = "Use a separate ParameterSet for each category, even when the parameter values are identical."


def check(index: RepoIndex, connections: Connections | None = None) -> list[Finding]:
    connections = connections or compute_connections(index)
    selected = {
        (use.environment, use.category, use.target, use.reference)
        for uses in connections.parameter_uses.values()
        for use in uses
    }
    findings: list[Finding] = []
    for env in index.environments:
        categories: dict[str, set[Category]] = defaultdict(set)
        paths: dict[str, list[tuple]] = defaultdict(list)
        for category in Category:
            for target, names in env.bound_targets(category).items():
                for position, name in enumerate(names):
                    if (env.full_name, category, target, name) not in selected:
                        continue
                    categories[name].add(category)
                    paths[name].append(
                        ("envTemplate", category.binding_field, target, position)
                    )

        conflicts = {name: used for name, used in categories.items() if len(used) > 1}
        if not conflicts:
            continue

        path = env.path / INVENTORY_DIR / ENV_DEFINITION_FILE
        try:
            loaded = load(path)
        except YamlReadError:
            continue

        meta = RULES["PLACE-7"]
        for name, used in conflicts.items():
            positions = sorted({loaded.position(binding_path) for binding_path in paths[name]})
            locations = tuple(Location(path, line, column) for line, column in positions)
            primary = locations[0]
            label = ", ".join(category.value for category in Category if category in used)
            findings.append(
                Finding(
                    rule="PLACE-7",
                    severity=Severity.WARNING,
                    issue_type=meta.default_issue_type,
                    action=meta.default_action,
                    path=path,
                    line=primary.line,
                    column=primary.column,
                    key=name,
                    scope=env.full_name,
                    related=(),
                    locations=locations,
                    message=(
                        f"ParameterSet {name!r} is bound to multiple categories: {label}."
                    ),
                    hint=_HINT,
                )
            )

    findings.sort(key=lambda item: (item.path.as_posix(), item.key, item.line))
    return findings
