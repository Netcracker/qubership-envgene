"""PLACE-4: Cloud Passport keys do not belong in ParameterSets."""

from __future__ import annotations

from pathlib import Path

from ..connections import Connections, compute_connections
from ..model import Finding, Layer, Location, ParamsetFile, RepoIndex, Severity
from ..passport import TABLE
from ..rulemeta import RULES
from ..yamlio import LoadedYaml, YamlReadError, leaves, load

_MESSAGE = "{key} is a Cloud Passport contract key; do not store it in a ParameterSet."
_HINT = (
    "Move {key} to the cluster cloud-passport, or to this environment's "
    "cloud-passport if the value is an override."
)


def check(index: RepoIndex, connections: Connections | None = None) -> list[Finding]:
    connections = connections or compute_connections(index)
    findings: list[Finding] = []
    for file in connections.parameter_files.values():
        loaded = _document(file)
        if loaded is None:
            continue
        params = loaded.doc.get("parameters") if isinstance(loaded.doc, dict) else None
        if not isinstance(params, dict):
            continue
        found: set[str] = set()
        for path, _value in leaves(params):
            if not path:
                continue
            key = str(path[0])
            if key not in TABLE or key in found:
                continue
            found.add(key)
            line, column = loaded.position(("parameters", key))
            findings.append(_finding(file, key, line, column))
    findings.sort(key=lambda item: (item.path.as_posix(), item.key, item.line))
    return findings


def _document(file: ParamsetFile) -> LoadedYaml | None:
    if file.loaded is not None:
        return file.loaded
    if file.is_jinja:
        try:
            return load(file.path)
        except YamlReadError:
            return None
    return None


def _scope(file: ParamsetFile) -> str:
    if file.layer is Layer.REPOSITORY:
        return "repository"
    if file.cluster and file.env:
        return f"{file.cluster}/{file.env}"
    if file.cluster:
        return file.cluster
    return "repository"


def _finding(file: ParamsetFile, key: str, line: int, column: int) -> Finding:
    meta = RULES["PLACE-4"]
    return Finding(
        rule="PLACE-4",
        severity=Severity.WARNING,
        path=file.path,
        line=line,
        column=column,
        issue_type=meta.default_issue_type,
        action=meta.default_action,
        key=key,
        scope=_scope(file),
        message=_MESSAGE.format(key=key),
        hint=_HINT.format(key=key),
        related=(),
        locations=(Location(file.path, line, column),),
    )
