"""NAME-4: bound ParameterSet stem is <subject>-<category>."""

from __future__ import annotations

import re
from pathlib import Path

from ..connections import Connections, compute_connections
from ..model import Category, Finding, Location, RepoIndex, Severity
from ..rulemeta import RULES

_TICKET = re.compile(r"(?:^|-)(?:ticket|jira|issue)-\d+", re.I)
_RELEASE = re.compile(r"(?:^|-)(?:r\d+(?:-\d+)?|20\d{2}[.-]\d{1,2})")
_TOKEN = {
    Category.DEPLOY: "deploy",
    Category.E2E: "pipeline",
    Category.TECHNICAL: "technical",
}
_HINT = (
    "Review whether this stem can be <subject>-<category>. "
    "Do not rename it if env_definition or other logic still depends on the current spelling."
)


def check(index: RepoIndex, connections: Connections | None = None) -> list[Finding]:
    connections = connections or compute_connections(index)
    findings: list[Finding] = []
    for physical_path, uses in sorted(
        connections.parameter_uses.items(), key=lambda item: item[0].as_posix()
    ):
        file = connections.parameter_files.get(physical_path)
        if file is None:
            continue
        stem = file.stem
        categories = {use.category for use in uses}
        owners = {
            owner
            for use in uses
            for owner in use.environment.split("/", 1)
        }
        scope = ", ".join(sorted(_TOKEN[item] for item in categories))
        if _bakes(stem, owners):
            findings.append(_finding(stem, scope, file.path, _scope_message(stem)))
            continue
        required = {_TOKEN[item] for item in categories}
        parts = stem.split("-")
        if len(parts) < 2 or not all(parts[:-1]) or required != {parts[-1]}:
            token = "/".join(sorted(required))
            findings.append(
                _finding(stem, scope, file.path, _tail_message(stem, token, scope))
            )
    findings.sort(key=lambda item: (item.path.as_posix(), item.key, item.line))
    return findings


def _bakes(stem: str, names: set[str]) -> bool:
    if _TICKET.search(stem) or _RELEASE.search(stem):
        return True
    lowered = stem.lower()
    for item in names:
        if not item:
            continue
        needle = item.lower()
        if needle == lowered or f"-{needle}-" in f"-{lowered}-":
            return True
        if lowered.startswith(f"{needle}-") or lowered.endswith(f"-{needle}"):
            return True
    return False


def _scope_message(stem: str) -> str:
    return (
        f"ParameterSet {stem!r} bakes a cluster, environment, ticket or release into the name."
    )


def _tail_message(stem: str, token: str, scope: str) -> str:
    return (
        f"ParameterSet {stem!r} must end with -{token} to match its env_definition binding ({scope})."
    )


def _finding(stem: str, scope: str, path: Path, message: str) -> Finding:
    meta = RULES["NAME-4"]
    return Finding(
        rule="NAME-4",
        severity=Severity.INFORMATION,
        path=path,
        line=1,
        column=1,
        issue_type=meta.default_issue_type,
        action=meta.default_action,
        key=stem,
        scope=scope,
        message=message,
        hint=_HINT,
        related=(),
        locations=(Location(path, 1, 1),),
    )
