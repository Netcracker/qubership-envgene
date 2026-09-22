"""SEC-3: Credential references must not enter runtime parameters."""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from ..connections import Connections, compute_connections
from ..model import Category, Finding, Location, RepoIndex, Severity
from ..parameter_objects import parameter_object_paths, safe_parameter_path
from ..rulemeta import RULES
from ..yamlio import LoadedYaml, YamlReadError, dotted, load

# Detect a credential access inside an expression, including a composite string.
# This is reference recognition, not expression evaluation or validation.
_CREDENTIAL = re.compile(r"\$\{\s*creds\s*\.\s*get\s*\(")


def _references(value: Any, path: tuple = (), ancestors: frozenset[int] = frozenset()) -> Iterator[tuple]:
    if isinstance(value, (dict, list)):
        if id(value) in ancestors:
            return
        ancestors = ancestors | {id(value)}
    if isinstance(value, dict):
        if value.get("$type") == "credRef":
            yield path
            return
        for key, child in value.items():
            yield from _references(child, (*path, key), ancestors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _references(child, (*path, index), ancestors)
    elif isinstance(value, str) and _CREDENTIAL.search(value):
        yield path


def _check_bag(document: LoadedYaml, prefix: tuple, bag: dict, scope: str) -> Iterator[Finding]:
    meta = RULES["SEC-3"]
    for path in _references(bag):
        yaml_path = (*prefix, *path)
        key = dotted(yaml_path)
        line, column = document.position(yaml_path)
        yield Finding(
            rule=meta.id,
            severity=Severity.WARNING,
            issue_type=meta.default_issue_type,
            action=meta.default_action,
            path=document.path,
            line=line,
            column=column,
            key=key,
            scope=scope,
            locations=(Location(document.path, line, column),),
            message=f"Runtime parameter {key!r} contains a Credential reference.",
            hint="Move the secret to deployment parameters and keep its Credential reference; runtime parameters expose it through Consul.",
        )


def check(index: RepoIndex, connections: Connections | None = None) -> list[Finding]:
    connections = connections or compute_connections(index)
    findings: list[Finding] = []
    for physical, file in connections.parameter_files.items():
        if not any(use.category is Category.TECHNICAL for use in connections.parameter_uses.get(physical, ())):
            continue
        if file.is_jinja or file.error or file.loaded is None or not safe_parameter_path(index, file.path):
            continue
        scope = "/".join(part for part in (file.cluster, file.env) if part) or "repository"
        findings.extend(_check_bag(file.loaded, ("parameters",), file.parameters, scope))
        for app_index, _app_name, params in file.applications:
            findings.extend(_check_bag(file.loaded, ("applications", app_index, "parameters"), params, scope))
    seen: set[Path] = set()
    for path, scope in parameter_object_paths(index, connections):
        if not safe_parameter_path(index, path) or path.resolve() in seen:
            continue
        seen.add(path.resolve())
        try:
            document = load(path)
        except YamlReadError:
            # Do not emit parser errors containing source values.
            continue
        bag = document.doc.get("technicalConfigurationParameters") if isinstance(document.doc, dict) else None
        if isinstance(bag, dict):
            findings.extend(_check_bag(document, ("technicalConfigurationParameters",), bag, scope))
    return sorted(findings, key=lambda item: (item.path.as_posix(), item.key, item.line))
