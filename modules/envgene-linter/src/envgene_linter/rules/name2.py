"""NAME-2: filename stem must equal the name field (SHOULD)."""

from __future__ import annotations

from pathlib import Path

from ..connections import Connections, compute_connections
from ..model import Action, Finding, IssueType, Location, RepoIndex, Severity
from ..rulemeta import RULES
from ..yamlio import LoadedYaml


def check(index: RepoIndex, connections: Connections | None = None) -> list[Finding]:
    connections = connections or compute_connections(index)
    findings: list[Finding] = []
    for file in connections.parameter_files.values():
        finding = _check_file(file.path, file.stem, "ParameterSet", file.is_jinja, file.error, file.loaded)
        if finding is not None:
            findings.append(finding)
    for entity in index.named_entities:
        if entity.path.resolve() not in connections.artifact_definitions:
            continue
        finding = _check_file(
            entity.path, entity.stem, entity.kind, entity.is_jinja, entity.error, entity.loaded
        )
        if finding is not None:
            findings.append(finding)
    findings.sort(key=lambda item: (item.path.as_posix(), item.key, item.line))
    return findings


def _check_file(
    path: Path,
    stem: str,
    kind: str,
    is_jinja: bool,
    error: str | None,
    loaded: LoadedYaml | None,
) -> Finding | None:
    if is_jinja or error or loaded is None:
        return None
    present, value = _root_name(loaded)
    if not present or value is None or value == "":
        line, column = loaded.position(("name",)) if present else (1, 1)
        return _finding(
            path,
            stem,
            line,
            column,
            severity=Severity.INFORMATION,
            issue_type=IssueType.INFORMATION,
            action=Action.REVIEW,
            message=(
                f"{kind} {path.name} has no name field; EnvGene requires it to "
                f"equal the filename stem {stem!r}."
            ),
            hint=f"Set name: {stem}",
        )
    declared = str(value)
    if declared == stem:
        return None
    line, column = loaded.position(("name",))
    meta = RULES["NAME-2"]
    return _finding(
        path,
        stem,
        line,
        column,
        severity=Severity.WARNING,
        issue_type=meta.default_issue_type,
        action=meta.default_action,
        message=(
            f"{kind} filename stem {stem!r} does not equal the name field {declared!r}."
        ),
        hint=f"Set name: {stem} to match the filename, which is the reference key.",
    )


def _root_name(loaded: LoadedYaml) -> tuple[bool, object]:
    if not isinstance(loaded.doc, dict):
        return False, None
    if "name" not in loaded.doc:
        return False, None
    return True, loaded.doc.get("name")


def _finding(
    path: Path,
    stem: str,
    line: int,
    column: int,
    *,
    severity: Severity,
    issue_type: IssueType,
    action: Action,
    message: str,
    hint: str,
) -> Finding:
    return Finding(
        rule="NAME-2",
        severity=severity,
        path=path,
        line=line,
        column=column,
        issue_type=issue_type,
        action=action,
        key="name",
        scope=stem,
        message=message,
        hint=hint,
        related=(),
        locations=(Location(path, line, column),),
    )
