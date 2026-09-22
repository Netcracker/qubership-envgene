"""SEC-1: literal values in secret-named parameters of connected objects."""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from ..connections import Connections, compute_connections
from ..parameter_objects import parameter_object_paths, safe_parameter_path
from ..model import Finding, Location, RepoIndex, Severity
from ..rulemeta import RULES
from ..yamlio import LoadedYaml, YamlReadError, dotted, load

_SECRET_SUFFIX = re.compile(r"(?:^|[_.-])(?:password|passwd|pass|secret|token|private_key|api_key)$")
_PARAMETER_SECTIONS = ("deployParameters", "e2eParameters", "technicalConfigurationParameters")


def _secret_name(name: str) -> bool:
    # Treat camelCase and snake_case alike, while preserving token boundaries.
    if _SECRET_SUFFIX.search(name.lower()):
        return True
    normalized = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", normalized).lower()
    return bool(_SECRET_SUFFIX.search(normalized))


def _leaves(value: Any, path: tuple = (), ancestors: frozenset[int] = frozenset()) -> Iterator[tuple[tuple, Any]]:
    if isinstance(value, (dict, list)):
        if id(value) in ancestors:
            return  # Recursive YAML aliases must not recurse forever.
        ancestors = ancestors | {id(value)}
    if isinstance(value, dict):
        if value.get("$type") == "credRef":
            return
        for key, child in value.items():
            yield from _leaves(child, (*path, key), ancestors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _leaves(child, (*path, index), ancestors)
    else:
        yield path, value


def _literal(value: Any) -> bool:
    if value is None or value == "":
        return False
    # Expressions are not evaluated; skipping one is not a claim it is safe.
    return not isinstance(value, str) or not any(mark in value for mark in ("${", "{{", "{%"))


def _check_bag(document: LoadedYaml, prefix: tuple, bag: dict, scope: str) -> Iterator[Finding]:
    meta = RULES["SEC-1"]
    for path, value in _leaves(bag):
        name = next((part for part in reversed(path) if isinstance(part, str)), "")
        if not _secret_name(name) or not _literal(value):
            continue
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
            message=f"Parameter {key!r} has a literal value and a secret-like name.",
            hint="Store the secret in a Credential and reference it with ${creds.get(\"<id>\").<field>}.",
        )


def check(index: RepoIndex, connections: Connections | None = None) -> list[Finding]:
    connections = connections or compute_connections(index)
    findings: list[Finding] = []
    for file in connections.parameter_files.values():
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
            # Parser exceptions can contain source values; never emit their text.
            continue
        if not isinstance(document.doc, dict):
            continue
        for section in _PARAMETER_SECTIONS:
            bag = document.doc.get(section)
            if isinstance(bag, dict):
                findings.extend(_check_bag(document, (section,), bag, scope))
    return sorted(findings, key=lambda item: (item.path.as_posix(), item.key, item.line))
