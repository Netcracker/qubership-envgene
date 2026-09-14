"""PLACE-8: review referenced or used empty entities."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from ..connections import Connections, compute_connections
from ..model import (
    Action,
    Finding,
    IssueType,
    Location,
    NamedEntityFile,
    ParamsetFile,
    RepoIndex,
    Severity,
)

_PROFILE_DIRS = ("resource_profiles", "rp_override", "Profiles", "parameters")
_CREDENTIAL_DIRS = ("credentials", "Credentials", "shared-credentials")
_PARAMSET_ROOT_KEYS = frozenset({"name", "version", "description", "parameters", "applications"})
_PROFILE_ROOT_KEYS = frozenset(
    {"name", "version", "description", "baseline", "applications"}
)
_MISSING = object()
_HINT = (
    "Review whether this empty file is intentional. "
    "If not, populate it or remove its reference or usage."
)
_Kind = Literal["ParameterSet", "Resource Profile Override", "Credentials file"]


def _mapping_state(value: object) -> bool | None:
    if not isinstance(value, dict):
        return None
    return bool(value)


def _empty_parameter_set(doc: object) -> bool | None:
    if doc is None:
        return True
    if not isinstance(doc, dict) or not set(doc).issubset(_PARAMSET_ROOT_KEYS):
        return None

    parameters = doc.get("parameters", _MISSING)
    if parameters is not _MISSING:
        has_parameters = _mapping_state(parameters)
        if has_parameters is None:
            return None
        if has_parameters:
            return False

    applications = doc.get("applications", _MISSING)
    if applications is _MISSING:
        return True
    if not isinstance(applications, list):
        return None
    for application in applications:
        if not isinstance(application, dict):
            return None
        app_parameters = application.get("parameters", _MISSING)
        if app_parameters is _MISSING:
            continue
        has_parameters = _mapping_state(app_parameters)
        if has_parameters is None:
            return None
        if has_parameters:
            return False
    return True


def _empty_profile(doc: object) -> bool | None:
    if doc is None:
        return True
    if not isinstance(doc, dict) or not set(doc).issubset(_PROFILE_ROOT_KEYS):
        return None

    applications = doc.get("applications", _MISSING)
    if applications is _MISSING:
        return True
    if not isinstance(applications, list):
        return None
    for application in applications:
        if not isinstance(application, dict):
            return None
        services = application.get("services", _MISSING)
        if services is _MISSING:
            continue
        if not isinstance(services, list):
            return None
        for service in services:
            if not isinstance(service, dict):
                return None
            parameters = service.get("parameters", _MISSING)
            if parameters is _MISSING:
                continue
            if not isinstance(parameters, list):
                return None
            if parameters:
                return False
    return True


def _empty_credentials(doc: object) -> bool | None:
    if doc is None:
        return True
    if not isinstance(doc, dict):
        return None
    return not bool(doc)


def _recognizable_profile(doc: object) -> bool:
    if not isinstance(doc, dict):
        return False
    applications = doc.get("applications")
    return isinstance(applications, list) and any(
        isinstance(application, dict) and "services" in application
        for application in applications
    )


def _mixed_legacy_profile(doc: object) -> bool:
    if not isinstance(doc, dict):
        return False
    applications = doc.get("applications")
    return isinstance(applications, list) and any(
        isinstance(application, dict) and "parameters" in application
        for application in applications
    )


def _scope(index: RepoIndex, path: Path) -> str:
    relative = path.relative_to(index.root / "environments")
    parts = relative.parts
    if parts[0] in {*_PROFILE_DIRS, *_CREDENTIAL_DIRS}:
        return "repository"
    if len(parts) >= 4 and parts[2] == "Inventory":
        return f"{parts[0]}/{parts[1]}"
    return parts[0]


def _is_legacy_path(index: RepoIndex, path: Path) -> bool:
    relative = path.relative_to(index.root / "environments")
    parts = relative.parts
    return (
        parts[0] == "parameters"
        or (len(parts) >= 2 and parts[1] == "parameters")
        or (len(parts) >= 4 and parts[2:4] == ("Inventory", "parameters"))
    )


def _candidate_records(
    index: RepoIndex, connections: Connections
) -> dict[Path, tuple[NamedEntityFile | ParamsetFile, _Kind]]:
    candidates: dict[Path, tuple[NamedEntityFile | ParamsetFile, _Kind]] = {
        path: (file, "ParameterSet")
        for path, file in connections.parameter_files.items()
    }
    for file in index.resource_profiles:
        if file.path.resolve() not in connections.resource_profiles:
            continue
        kind: _Kind = "ParameterSet" if _is_legacy_path(index, file.path) else "Resource Profile Override"
        candidates.setdefault(file.path.resolve(), (file, kind))
    for file in index.credential_files:
        if file.path.resolve() in connections.credentials:
            candidates[file.path.resolve()] = (file, "Credentials file")
    return candidates


def _finding(index: RepoIndex, file: NamedEntityFile | ParamsetFile, kind: _Kind) -> Finding:
    location = Location(file.path, 1, 1)
    return Finding(
        rule="PLACE-8",
        severity=Severity.INFORMATION,
        issue_type=IssueType.INFORMATION,
        action=Action.REVIEW,
        path=file.path,
        line=1,
        column=1,
        locations=(location,),
        key=file.stem,
        scope=_scope(index, file.path),
        related=(),
        message=f"{kind} {file.path.name!r} is empty but is referenced or used by the generator.",
        hint=_HINT,
    )


def check(index: RepoIndex, connections: Connections | None = None) -> list[Finding]:
    connections = connections or compute_connections(index)
    bound = connections.selected_paths
    profile_bound = connections.resource_profiles
    findings: list[Finding] = []
    for physical_path, (file, discovered_kind) in _candidate_records(index, connections).items():
        if physical_path not in bound or file.is_jinja or file.loaded is None:
            continue
        kind = discovered_kind
        if kind == "ParameterSet":
            profile_candidate = physical_path in profile_bound or _recognizable_profile(
                file.loaded.doc
            )
            if profile_candidate:
                if _mixed_legacy_profile(file.loaded.doc):
                    continue
                kind = "Resource Profile Override"
        if kind == "ParameterSet":
            empty = _empty_parameter_set(file.loaded.doc)
        elif kind == "Resource Profile Override":
            empty = _empty_profile(file.loaded.doc)
        else:
            empty = _empty_credentials(file.loaded.doc)
        if empty is True:
            findings.append(_finding(index, file, kind))
    return sorted(findings, key=lambda item: (item.path.as_posix(), item.key, item.line))
