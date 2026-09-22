"""PLACE-10: selected entities belong in their type directories."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from ..connections import Connections, compute_connections
from ..discovery import paramset_stem
from ..model import Finding, Location, RepoIndex, Severity
from ..rulemeta import RULES


_TYPE_DIRECTORIES = (
    ("ParameterSet", "parameters"),
    ("Resource Profile Override", "resource_profiles"),
    ("Shared Template Variables", "shared-template-variables"),
    ("Shared credentials", "credentials"),
    ("Cloud Passport", "cloud-passport"),
)


def _scope(index: RepoIndex, physical: Path) -> tuple[Path | None, str]:
    matches: list[tuple[Path, str]] = [(index.root / "environments", "repository")]
    for cluster in index.clusters.values():
        matches.append((cluster.path, cluster.name))
        matches.extend(
            (env.path / "Inventory", env.full_name) for env in cluster.environments
        )
    contained = []
    for base, label in matches:
        try:
            physical.relative_to(base.resolve())
        except (OSError, RuntimeError, ValueError):
            continue
        contained.append((base.resolve(), label))
    if not contained:
        return None, "repository"
    return max(contained, key=lambda item: len(item[0].parts))


def _is_in_directory(physical: Path, base: Path | None, expected: str) -> bool:
    if base is None:
        return False
    relative = physical.relative_to(base)
    return bool(relative.parts) and relative.parts[0] == expected


def _safe_selected_path(index: RepoIndex, physical: Path, selected_path: Path) -> bool:
    try:
        logical = selected_path.absolute().relative_to(index.root)
        relative = physical.relative_to(index.root)
    except ValueError:
        return False
    return ".git" not in logical.parts and ".git" not in relative.parts


def _finding(
    index: RepoIndex,
    physical: Path,
    selected_path: Path,
    kind: str,
    expected: str,
    stem: str,
) -> Finding | None:
    base, scope = _scope(index, physical)
    if _is_in_directory(physical, base, expected):
        return None
    expected_path = (base or index.root / "environments") / expected
    meta = RULES["PLACE-10"]
    return Finding(
        rule=meta.id,
        severity=Severity.WARNING,
        issue_type=meta.default_issue_type,
        action=meta.default_action,
        path=selected_path,
        line=1,
        column=1,
        locations=(Location(selected_path, 1, 1),),
        key=stem,
        scope=scope,
        related=(),
        message=(
            f"{kind} {selected_path.name!r} must be under the {expected!r} directory."
        ),
        hint=f"Move it under {expected_path} within its {scope} scope.",
    )


def check(index: RepoIndex, connections: Connections | None = None) -> list[Finding]:
    connections = connections or compute_connections(index)
    findings: list[Finding] = []
    selections: dict[str, Iterable[Path]] = {
        "ParameterSet": connections.parameter_sets,
        "Resource Profile Override": connections.resource_profiles,
        "Shared Template Variables": connections.shared_template_variables,
        "Shared credentials": connections.credentials,
        "Cloud Passport": connections.passports,
    }
    for kind, expected in _TYPE_DIRECTORIES:
        selected = selections[kind]
        for physical in selected:
            selected_path = connections.selected_aliases.get((kind, physical), physical)
            if not _safe_selected_path(index, physical, selected_path):
                continue
            finding = _finding(
                index,
                physical,
                selected_path,
                kind,
                expected,
                paramset_stem(selected_path),
            )
            if finding is not None:
                findings.append(finding)
    return sorted(findings, key=lambda item: (item.path.as_posix(), item.key, item.line))
