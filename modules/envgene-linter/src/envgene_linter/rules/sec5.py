"""SEC-5: review protection of connected secrets without revealing their values."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..connections import Connections, compute_connections
from ..model import Action, Finding, IssueType, Location, RepoIndex, Severity
from ..parameter_objects import safe_parameter_path
from ..security_sources import collect_security_sources
from ..security_values import classify, literal_name, parse_reference, valid_external
from ..yamlio import LoadedYaml, YamlReadError, load
from .sec1 import _secret_name

_MESSAGES = {
    'literal': 'A connected secret candidate contains a literal value without recognized protection.',
    'unknown': 'The protection or source of a connected secret could not be established.',
    'unsupported': 'A connected secret uses encryption other than the accepted SOPS format.',
}
_HINTS = {
    'literal': 'Review this value: use SOPS encryption or a supported CI/CD or external-store source.',
    'unknown': 'Review the source and protection of this value; static inspection cannot confirm them.',
    'unsupported': 'Review the encryption format against the accepted secret-protection policy; this is not a plaintext finding.',
}


def _get(value: Any, path: tuple) -> tuple[bool, Any]:
    for part in path:
        if isinstance(value, dict) and part in value:
            value = value[part]
        elif isinstance(value, list) and isinstance(part, int) and 0 <= part < len(value):
            value = value[part]
        else:
            return False, None
    return True, value


class _Scanner:
    def __init__(self, index: RepoIndex):
        self.index = index
        self.documents: dict[Path, LoadedYaml | None] = {}
        self.findings: dict[tuple, Finding] = {}
        self.active_refs: set[tuple] = set()

    def emit(self, path: Path, prefix: tuple, reason: str, document: LoadedYaml | None = None):
        line, column = document.position(prefix) if document else (1, 1)
        identity = (path.resolve(), line, column, reason)
        self.findings.setdefault(identity, Finding(
            rule='SEC-5', severity=Severity.INFORMATION,
            issue_type=IssueType.INFORMATION, action=Action.REVIEW,
            path=path, line=line, column=column, key='secret', scope='repository',
            locations=(Location(path, line, column),),
            message=_MESSAGES[reason], hint=_HINTS[reason],
        ))

    def read(self, path: Path | None) -> LoadedYaml | None:
        if path is None or not safe_parameter_path(self.index, path):
            return None
        physical = path.resolve()
        if physical not in self.documents:
            try:
                document = load(path) if path.suffix != '.j2' else None
                self.documents[physical] = document if document is not None and (
                    document.doc is None or isinstance(document.doc, dict)
                ) else None
            except (YamlReadError, RecursionError):
                self.documents[physical] = None
        return self.documents[physical]

    def reference(self, reference: tuple, doc: LoadedYaml, prefix: tuple, catalog: Path | None):
        target = self.read(catalog)
        identifier, field, kind = reference
        if target is None or not isinstance(target.doc, dict) or identifier not in target.doc or identifier == 'sops':
            # An unavailable target gives us no secret content to classify.
            # Reference existence is not a secret-protection finding.
            return
        entry = target.doc[identifier]
        if not isinstance(entry, dict):
            self.emit(doc.path, prefix, 'unknown', doc)
            return
        identity = (target.path.resolve(), identifier, field)
        if identity in self.active_refs:
            self.emit(doc.path, prefix, 'unknown', doc)
            return
        self.active_refs.add(identity)
        try:
            if kind == 'external' or (kind == 'any' and entry.get('type') == 'external'):
                if valid_external(entry):
                    properties = entry.get('properties', [])
                    if field is None or (properties and field in {prop['name'] for prop in properties}):
                        return
                self.emit(doc.path, prefix, 'unknown', doc)
                if isinstance(entry.get('data'), dict):
                    self.walk(target, (identifier, 'data'), entry['data'], target.path, force=True, context='stored')
                return
            if entry.get('type') == 'external':
                self.emit(doc.path, prefix, 'unknown', doc)
                return
            if field is None:
                self.entry(target, identifier, entry)
            else:
                found, value = _get(entry, ('data', field))
                if not found:
                    self.emit(doc.path, prefix, 'unknown', doc)
                else:
                    self.walk(target, (identifier, 'data', field), value, target.path, force=True, context='stored')
        finally:
            self.active_refs.remove(identity)

    def walk(self, doc: LoadedYaml, prefix: tuple, value: Any, catalog: Path | None,
             force: bool = False, ancestors: frozenset[int] = frozenset(), context: str = 'runtime'):
        reference = parse_reference(value)
        if reference is not None:
            expected = 'system' if context == 'system' else 'local'
            if context == 'stored' or reference[2] not in (expected, 'external'):
                self.emit(doc.path, prefix, 'unknown', doc)
            else:
                self.reference(reference, doc, prefix, catalog)
            return
        if isinstance(value, (dict, list)):
            if id(value) in ancestors:
                self.emit(doc.path, prefix, 'unknown', doc)
                return
            ancestors = ancestors | {id(value)}
            if isinstance(value, dict):
                if value.get('$type') == 'credRef':
                    self.emit(doc.path, prefix, 'unknown', doc)
                    return
                for key, child in value.items():
                    self.walk(doc, (*prefix, key), child, catalog, force, ancestors, context)
            else:
                for i, child in enumerate(value):
                    self.walk(doc, (*prefix, i), child, catalog, force, ancestors, context)
            return
        name = next((part for part in reversed(prefix) if isinstance(part, str)), '')
        reference_like = isinstance(value, str) and ('creds' in value and ('${' in value or 'envgen.' in value))
        if not force and not _secret_name(name) and not reference_like:
            return
        state = classify(value, doc.doc)
        if state not in ('empty', 'protected'):
            self.emit(doc.path, prefix, state, doc)

    def entry(self, doc: LoadedYaml, identifier: str, entry: Any):
        if not isinstance(entry, dict):
            self.emit(doc.path, (identifier,), 'unknown', doc)
            return
        kind = entry.get('type')
        if kind == 'external':
            if valid_external(entry):
                return
            self.emit(doc.path, (identifier,), 'unknown', doc)
            if isinstance(entry.get('data'), dict):
                self.walk(doc, (identifier, 'data'), entry['data'], doc.path, force=True, context='stored')
            return
        if kind not in ('secret', 'usernamePassword', 'vaultAppRole') and classify(kind, doc.doc) != 'protected':
            self.emit(doc.path, (identifier, 'type'), 'unknown', doc)
        data = entry.get('data')
        if data is None:
            return
        if not isinstance(data, dict):
            self.emit(doc.path, (identifier, 'data'), 'unknown', doc)
            return
        self.walk(doc, (identifier, 'data'), data, doc.path, force=True, context='stored')


def check(index: RepoIndex, connections: Connections | None = None) -> list[Finding]:
    connections = connections or compute_connections(index)
    inputs = collect_security_sources(index, connections)
    scanner = _Scanner(index)
    for issue in inputs.issues:
        document = scanner.read(issue.path)
        scanner.emit(issue.path, issue.prefix, 'unknown', document)
    for source in inputs.sources:
        document = scanner.read(source.path)
        if document is None:
            scanner.emit(source.path, (), 'unknown')
        elif isinstance(document.doc, dict):
            for identifier, entry in document.doc.items():
                if identifier != 'sops':
                    scanner.entry(document, identifier, entry)
    for bag in inputs.bags:
        document = scanner.read(bag.path)
        if document is None:
            scanner.emit(bag.path, (), 'unknown')
            continue
        found, value = _get(document.doc, bag.prefix)
        if not found or value is None:
            continue
        if not isinstance(value, dict):
            scanner.emit(bag.path, bag.prefix, 'unknown', document)
            continue
        if bag.fields is None:
            scanner.walk(document, bag.prefix, value, bag.catalog)
        else:
            for field in bag.fields:
                if field not in value or value[field] is None or value[field] == '':
                    continue
                prefix = (*bag.prefix, field)
                if field in ('credentialsId', 'defaultCredentialsId', 'tokenSecret'):
                    if literal_name(value[field]):
                        scanner.reference((value[field], None, 'any'), document, prefix, bag.catalog)
                    else:
                        scanner.emit(document.path, prefix, 'unknown', document)
                else:
                    scanner.walk(document, prefix, value[field], bag.catalog, force=True, context='system')
    return sorted(scanner.findings.values(), key=lambda f: (f.path.as_posix(), f.line, f.column, f.message))
