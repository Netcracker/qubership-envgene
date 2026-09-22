"""SEC-4: named user/password pairs reference the same Credential ID."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from ..connections import Connections, compute_connections
from ..model import Finding, Location, RepoIndex, Severity
from ..parameter_objects import safe_parameter_path
from ..rulemeta import RULES
from ..security_sources import SecurityBag, collect_security_sources
from ..security_values import parse_reference
from ..yamlio import LoadedYaml, YamlReadError, load

def _pair_key(key: Any) -> tuple[str, str] | None:
    if not isinstance(key, str):
        return None
    key = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', key)
    key = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', key).lower()
    for suffix in ('user_name', 'username', 'login', 'user', 'password', 'passwd', 'pass', 'pwd'):
        if key == suffix or (key.endswith(suffix) and key[-len(suffix)-1] in '_.-'):
            role = 'username' if suffix in ('user_name', 'username', 'login', 'user') else 'password'
            return key[:-len(suffix)], role
    return None


def _at(value: Any, prefix: tuple) -> Any:
    for key in prefix:
        if isinstance(value, dict) and key in value:
            value = value[key]
        elif isinstance(value, list) and isinstance(key, int) and 0 <= key < len(value):
            value = value[key]
        else:
            return None
    return value


class _Checker:
    def __init__(self, index: RepoIndex):
        self.index = index
        self.documents: dict[Path, LoadedYaml | None] = {}
        self.findings: dict[tuple, Finding] = {}

    def read(self, path: Path) -> LoadedYaml | None:
        if not safe_parameter_path(self.index, path):
            return None
        physical = path.resolve()
        if physical not in self.documents:
            try:
                document = load(path)
                self.documents[physical] = document if isinstance(document.doc, dict) else None
            except (YamlReadError, RecursionError):
                self.documents[physical] = None
        return self.documents[physical]

    def emit(self, document: LoadedYaml, bag: SecurityBag, paths: list[tuple]):
        positions = sorted(set(document.position(path) for path in paths))
        identity = (document.path.resolve(), tuple(positions))
        line, column = positions[0]
        meta = RULES['SEC-4']
        self.findings.setdefault(identity, Finding(
            rule=meta.id, severity=Severity.INFORMATION, issue_type=meta.default_issue_type,
            action=meta.default_action, path=document.path, line=line, column=column,
            key='credential-pair', scope=bag.environment,
            locations=tuple(Location(document.path, row, col) for row, col in positions),
            message='The user/password pair must reference the same Credential ID.',
            hint='Use the same Credential ID in both pair references. Secret values are not displayed.',
        ))

    def check_group(self, document: LoadedYaml, bag: SecurityBag, members: list[tuple[tuple, Any]]):
        references = [parse_reference(value) for _, value in members]
        expected = 'system' if bag.fields is not None else 'local'
        if any(ref is None or ref[2] not in (expected, 'external') for ref in references):
            return
        if references[0][0] != references[1][0]:
            self.emit(document, bag, [path for path, _ in members])

    def walk(self, document: LoadedYaml, bag: SecurityBag, value: Any, prefix: tuple,
             ancestors: frozenset[int] = frozenset()):
        if not isinstance(value, (dict, list)) or id(value) in ancestors:
            return
        ancestors = ancestors | {id(value)}
        if isinstance(value, list):
            for position, child in enumerate(value):
                self.walk(document, bag, child, (*prefix, position), ancestors)
            return
        if value.get('$type') == 'credRef':
            return
        groups: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
        for key, child in value.items():
            pair_key = _pair_key(key)
            if pair_key:
                family, field = pair_key
                groups[family][field].append(((*prefix, key), child))
        for group in groups.values():
            if 'username' in group and 'password' in group:
                for user in group['username']:
                    for password in group['password']:
                        self.check_group(document, bag, [user, password])
        for key, child in value.items():
            self.walk(document, bag, child, (*prefix, key), ancestors)


def check(index: RepoIndex, connections: Connections | None = None) -> list[Finding]:
    connections = connections or compute_connections(index)
    inputs = collect_security_sources(index, connections)
    checker = _Checker(index)
    for bag in inputs.bags:
        document = checker.read(bag.path)
        if document is None:
            continue
        value = _at(document.doc, bag.prefix)
        if bag.fields is not None:
            value = {field: value[field] for field in bag.fields if isinstance(value, dict) and field in value}
        checker.walk(document, bag, value, bag.prefix)
    return sorted(checker.findings.values(), key=lambda item: (item.path.as_posix(), item.line, item.column, item.message))
