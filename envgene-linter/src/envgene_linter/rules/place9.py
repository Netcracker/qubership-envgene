"""PLACE-9: one used Cloud Passport per cluster and role."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from ..connections import Connections, compute_connections
from ..discovery import ENV_DEFINITION_FILE, INVENTORY_DIR
from ..model import EnvModel, Finding, Location, PassportFile, RepoIndex, Severity
from ..passport import AUTO_FOLDER, resolve_passport
from ..rulemeta import RULES
from ..yamlio import YamlReadError, load

_INFRA_NAME = "passport-infra"


def _physical_in_repo(index: RepoIndex, path: Path) -> Path | None:
    try:
        logical_relative = path.absolute().relative_to(index.root)
        physical = path.resolve()
        relative = physical.relative_to(index.root)
    except (OSError, RuntimeError, ValueError):
        return None
    return None if ".git" in logical_relative.parts or ".git" in relative.parts else physical


def _definition_location(env: EnvModel) -> Location:
    path = env.path / INVENTORY_DIR / ENV_DEFINITION_FILE
    if env.cloud_passport is None:
        return Location(path, 1, 1)
    try:
        line, column = load(path).position(("inventory", "cloudPassport"))
    except YamlReadError:
        line, column = 1, 1
    return Location(path, line, column)


def _locations(items: list[Location]) -> tuple[Location, ...]:
    unique = {(item.path, item.line, item.column): item for item in items}
    return tuple(
        unique[key]
        for key in sorted(unique, key=lambda value: (value[0].as_posix(), value[1], value[2]))
    )


@dataclass
class _Ambiguity:
    candidates: dict[Path, PassportFile] = field(default_factory=dict)
    definitions: list[Location] = field(default_factory=list)
    clusters: set[str] = field(default_factory=set)
    names: set[str] = field(default_factory=set)


def _ambiguity_findings(index: RepoIndex) -> list[Finding]:
    groups: dict[tuple[Path, ...], _Ambiguity] = {}
    for env in index.environments:
        resolution = resolve_passport(index, env)
        physical = {
            resolved: candidate
            for candidate in resolution.candidates
            if (resolved := _physical_in_repo(index, candidate.path)) is not None
        }
        if resolution.file is not None or len(physical) <= 1:
            continue
        group_key = tuple(sorted(physical, key=lambda path: path.as_posix()))
        group = groups.setdefault(group_key, _Ambiguity())
        group.candidates.update(physical)
        group.definitions.append(_definition_location(env))
        group.clusters.add(env.cluster)
        group.names.add(env.cloud_passport or next(iter(physical.values())).stem)

    meta = RULES["PLACE-9"]
    findings: list[Finding] = []
    for group in groups.values():
        candidates = sorted(group.candidates.values(), key=lambda item: item.path.as_posix())
        locations = _locations(
            [Location(item.path, 1, 1) for item in candidates] + group.definitions
        )
        name = ", ".join(sorted(group.names))
        findings.append(
            Finding(
                rule="PLACE-9",
                severity=Severity.WARNING,
                issue_type=meta.default_issue_type,
                action=meta.default_action,
                path=candidates[0].path,
                line=1,
                column=1,
                key=name,
                scope=", ".join(sorted(group.clusters)),
                locations=locations,
                message=f"Cloud Passport {name!r} resolves to multiple files.",
                hint="Keep one matching Cloud Passport on its resolution path.",
            )
        )
    return findings


def _selected_by_cluster(
    index: RepoIndex, connections: Connections
) -> dict[tuple[str, str], dict[Path, PassportFile]]:
    selected: dict[tuple[str, str], dict[Path, PassportFile]] = defaultdict(dict)
    for env in index.environments:
        passport = connections.environment_passports.get(env.full_name)
        if passport is None:
            continue
        physical = _physical_in_repo(index, passport.path)
        if physical is None:
            continue
        role = "infra" if passport.stem == _INFRA_NAME else "default"
        selected[(env.cluster, role)].setdefault(physical, passport)
    return selected


def _cardinality_findings(
    index: RepoIndex, connections: Connections
) -> list[Finding]:
    meta = RULES["PLACE-9"]
    findings: list[Finding] = []
    for (cluster, role), physical in _selected_by_cluster(index, connections).items():
        if len(physical) <= 1:
            continue
        passports = sorted(physical.values(), key=lambda item: item.path.as_posix())
        locations = tuple(Location(item.path, 1, 1) for item in passports)
        findings.append(
            Finding(
                rule="PLACE-9",
                severity=Severity.WARNING,
                issue_type=meta.default_issue_type,
                action=meta.default_action,
                path=passports[0].path,
                line=1,
                column=1,
                key=role,
                scope=cluster,
                locations=locations,
                message=f"Cluster {cluster!r} uses multiple {role} Cloud Passports.",
                hint=f"Keep one {role} Cloud Passport for cluster {cluster!r}.",
            )
        )
    return findings


def _placement_findings(
    index: RepoIndex, connections: Connections
) -> list[Finding]:
    selected: dict[tuple[str, Path], PassportFile] = {}
    for env in index.environments:
        passport = connections.environment_passports.get(env.full_name)
        if passport is None or not passport.on_cluster:
            continue
        physical = _physical_in_repo(index, passport.path)
        if physical is not None:
            selected.setdefault((env.cluster, physical), passport)

    meta = RULES["PLACE-9"]
    findings: list[Finding] = []
    for (cluster, physical), passport in selected.items():
        canonical = (index.clusters[cluster].path / AUTO_FOLDER).resolve()
        if physical.is_relative_to(canonical):
            continue
        findings.append(
            Finding(
                rule="PLACE-9",
                severity=Severity.WARNING,
                issue_type=meta.default_issue_type,
                action=meta.default_action,
                path=passport.path,
                line=1,
                column=1,
                key=passport.stem,
                scope=cluster,
                locations=(Location(passport.path, 1, 1),),
                message=f"Cloud Passport {passport.path.name!r} is outside the canonical cluster folder.",
                hint=f"Move it under environments/{cluster}/cloud-passport/.",
            )
        )
    return findings


@dataclass
class _CredentialIssue:
    path: Path
    passports: dict[Path, PassportFile] = field(default_factory=dict)
    clusters: set[str] = field(default_factory=set)


def _credential_findings(
    index: RepoIndex, connections: Connections
) -> list[Finding]:
    issues: dict[Path, _CredentialIssue] = {}
    for env in index.environments:
        passport = connections.environment_passports.get(env.full_name)
        if passport is None:
            continue
        passport_physical = _physical_in_repo(index, passport.path)
        if passport_physical is None:
            continue
        slots = (
            passport.path.parent / "credentials" / f"{passport.stem}.yml",
            passport.path.parent / f"{passport.stem}-creds.yml",
        )
        used = next((slot for slot in slots if slot.is_file()), None)
        if used is None:
            continue
        used_physical = _physical_in_repo(index, used)
        if used_physical is None:
            continue
        canonical = (index.clusters[env.cluster].path / AUTO_FOLDER).resolve()
        if used_physical.parent == passport_physical.parent and used_physical.is_relative_to(canonical):
            continue
        issue = issues.setdefault(used_physical, _CredentialIssue(path=used))
        issue.passports.setdefault(passport_physical, passport)
        issue.clusters.add(env.cluster)

    meta = RULES["PLACE-9"]
    findings: list[Finding] = []
    for issue in issues.values():
        passports = sorted(issue.passports.values(), key=lambda item: item.path.as_posix())
        locations = _locations(
            [Location(issue.path, 1, 1)]
            + [Location(passport.path, 1, 1) for passport in passports]
        )
        scope = ", ".join(sorted(issue.clusters))
        findings.append(
            Finding(
                rule="PLACE-9",
                severity=Severity.WARNING,
                issue_type=meta.default_issue_type,
                action=meta.default_action,
                path=issue.path,
                line=1,
                column=1,
                key=issue.path.stem,
                scope=scope,
                locations=locations,
                message=(
                    f"Credentials file {issue.path.name!r} is not beside its Cloud Passport "
                    "in the appropriate cluster cloud-passport folder."
                ),
                hint=(
                    "Move it beside the passport under the appropriate cluster's "
                    "cloud-passport folder."
                ),
            )
        )
    return findings


def check(index: RepoIndex, connections: Connections | None = None) -> list[Finding]:
    connections = connections or compute_connections(index)
    findings = [
        *_ambiguity_findings(index),
        *_cardinality_findings(index, connections),
        *_placement_findings(index, connections),
        *_credential_findings(index, connections),
    ]
    return sorted(findings, key=lambda item: (item.path.as_posix(), item.key, item.line))
