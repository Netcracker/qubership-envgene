"""NAME-1: different keys may name the same concept (SHOULD, review only)."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from ..connections import Connections, compute_connections
from ..model import Finding, Location, ParamsetFile, RepoIndex, Severity
from ..rulemeta import RULES
from ..yamlio import dotted, leaves

_HINT = (
    "Review whether they mean the same concept for the same consumer. "
    "Do not collapse them unless that is intended."
)

_PAIRS = (
    ("_USER", "_PASSWORD"),
    ("_USERNAME", "_PASSWORD"),
    ("_USER", "_PASS"),
    ("_USERNAME", "_PASS"),
)


@dataclass(frozen=True)
class _Hit:
    path: Path
    line: int
    column: int
    key: str
    value: str


def check(index: RepoIndex, connections: Connections | None = None) -> list[Finding]:
    connections = connections or compute_connections(index)
    grouped: dict[str, list[_Hit]] = defaultdict(list)
    for file in connections.parameter_files.values():
        if file.is_jinja or file.error or file.loaded is None:
            continue
        for hit in _hits(file):
            grouped[hit.value].append(hit)

    findings: list[Finding] = []
    meta = RULES["NAME-1"]
    for value, group in grouped.items():
        names = _drop_cred_pairs({hit.key for hit in group})
        if len(names) < 2:
            continue
        sorted_hits = sorted(
            (hit for hit in group if hit.key in names),
            key=lambda hit: (hit.path.as_posix(), hit.key),
        )
        primary = sorted_hits[0]
        findings.append(
            Finding(
                rule="NAME-1",
                severity=Severity.INFORMATION,
                path=primary.path,
                line=primary.line,
                column=primary.column,
                issue_type=meta.default_issue_type,
                action=meta.default_action,
                key=primary.key,
                scope="repository",
                message=f"Keys {', '.join(sorted(names))} share the value {value!r}.",
                hint=_HINT,
                related=tuple(sorted(names)),
                locations=tuple(
                    Location(hit.path, hit.line, hit.column) for hit in sorted_hits
                ),
            )
        )
    findings.sort(key=lambda item: (item.path.as_posix(), item.key, item.line))
    return findings


def _hits(file: ParamsetFile) -> list[_Hit]:
    assert file.loaded is not None
    out: list[_Hit] = []
    for leaf, value in leaves(file.parameters):
        if isinstance(value, str) and value != "":
            yaml_path = ("parameters", *leaf)
            line, column = file.loaded.position(yaml_path)
            out.append(_Hit(file.path, line, column, dotted(leaf), value))
    for index, app_name, params in file.applications:
        for leaf, value in leaves(params):
            if isinstance(value, str) and value != "":
                yaml_path = ("applications", index, "parameters", *leaf)
                line, column = file.loaded.position(yaml_path)
                out.append(
                    _Hit(
                        file.path,
                        line,
                        column,
                        f"{app_name}.{dotted(leaf)}",
                        value,
                    )
                )
    return out


def _drop_cred_pairs(names: set[str]) -> set[str]:
    last = {name: name.rsplit(".", 1)[-1] for name in names}
    drop: set[str] = set()
    for name, segment in last.items():
        upper = segment.upper()
        for left, right in _PAIRS:
            if not upper.endswith(left):
                continue
            partner = upper[: -len(left)] + right
            for other, other_segment in last.items():
                if other == name:
                    continue
                if other_segment.upper() == partner:
                    drop.add(name)
                    drop.add(other)
    return names - drop
