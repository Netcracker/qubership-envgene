"""INT-2: resolve connected references without evaluating or disclosing secrets."""

from __future__ import annotations

import re
import os
from pathlib import Path
from typing import Any

from ..connections import CREDENTIAL_DIRS, PROFILE_DIRS, Connections, compute_connections
from ..discovery import paramset_stem
from ..model import Action, Category, Finding, IssueType, Location, RepoIndex, Severity
from ..parameter_objects import parameter_object_paths, safe_parameter_path
from ..security_sources import SecurityBag, collect_security_sources
from ..security_values import literal_name
from ..yamlio import LoadedYaml, YamlReadError, load

_CALL = r'''creds\s*\.\s*get\s*\(\s*(["'])([^"'{}\\\r\n]+)\1\s*\)(?:\s*\.\s*[A-Za-z_]\w*)?'''
_RUNTIME = re.compile(r'\$\{\s*' + _CALL + r'\s*\}')
_SYSTEM = re.compile(r'envgen\s*\.\s*' + _CALL)
_INTENT = re.compile(r'(?:envgen\s*\.\s*)?creds\s*\.\s*get\s*\(')
_PARAMSET_FIELDS = ('deployParameterSets', 'e2eParameterSets', 'technicalConfigurationParameterSets')
_MESSAGES = {
    'missing': 'The connected reference has a missing target.',
    'ambiguous': 'The connected reference has an ambiguous target.',
    'unknown': 'The target of the connected reference is unknown to static inspection.',
}


def _at(value: Any, prefix: tuple) -> Any:
    for key in prefix:
        if isinstance(value, dict) and key in value:
            value = value[key]
        elif isinstance(value, list) and isinstance(key, int) and 0 <= key < len(value):
            value = value[key]
        else:
            return None
    return value


def _literal(value: Any) -> bool:
    return literal_name(value) and not any(mark in value for mark in ('}}', '%}', '{#', '#}'))


class _Checker:
    def __init__(self, index: RepoIndex, connections: Connections):
        self.index = index
        self.connections = connections
        self.inputs = collect_security_sources(index, connections)
        self.envs = {env.full_name: env for env in index.environments}
        self.documents: dict[Path, LoadedYaml | None] = {}
        self.directories: dict[Path, tuple[list[Path], bool]] = {}
        self.findings: dict[tuple, Finding] = {}

    def read(self, path: Path | None) -> LoadedYaml | None:
        if path is None or not safe_parameter_path(self.index, path) or path.name.endswith('.j2'):
            return None
        physical = path.resolve()
        if physical not in self.documents:
            try:
                document = load(path)
                self.documents[physical] = document if isinstance(document.doc, dict) else None
            except (YamlReadError, RecursionError):
                self.documents[physical] = None
        return self.documents[physical]

    def emit(self, document: LoadedYaml, prefix: tuple, environment: str, kind: str, state: str | None):
        if state is None:
            return
        line, column = document.position(prefix)
        identity = (document.path.resolve(), line, column, environment, kind, state)
        review = state == 'unknown'
        self.findings.setdefault(identity, Finding(
            rule='INT-2', severity=Severity.INFORMATION if review else Severity.WARNING,
            issue_type=IssueType.INFORMATION if review else IssueType.WARNING,
            action=Action.REVIEW if review else Action.FIX,
            path=document.path, line=line, column=column,
            key=kind, scope=environment, locations=(Location(document.path, line, column),),
            message=_MESSAGES[state],
            hint=('Review the connected source and rendering context without exposing secret values.' if review
                  else 'Ensure the reference resolves to one object using the applicable source precedence.'),
        ))

    def directory_files(self, directory: Path) -> tuple[list[Path], bool]:
        if directory in self.directories:
            return self.directories[directory]
        paths, uncertain = [], False
        try:
            physical = directory.resolve().relative_to(self.index.root)
            logical = directory.relative_to(self.index.root)
            if '.git' in physical.parts or '.git' in logical.parts:
                return [], True
            if directory.is_symlink():
                return [], True
            if directory.is_dir():
                errors = []
                for base, directories, files in os.walk(directory, followlinks=False, onerror=errors.append):
                    for name in list(directories):
                        child = Path(base) / name
                        if name == '.git' or child.is_symlink():
                            directories.remove(name)
                            uncertain = True
                    paths.extend(Path(base) / name for name in files
                                 if name.endswith(('.yml', '.yaml', '.yml.j2', '.yaml.j2')))
                uncertain |= bool(errors)
            elif directory.exists():
                uncertain = True
        except (OSError, RuntimeError, ValueError):
            uncertain = True
        self.directories[directory] = (paths, uncertain)
        return paths, uncertain

    def named_paths(self, env, reference: str, folders: tuple[str, ...]) -> list[Path]:
        # Inspect logical candidates too: discovery omits unsafe paths, which must block fallback.
        for base in (env.path / 'Inventory', self.index.clusters[env.cluster].path, self.index.root / 'environments'):
            for folder in folders:
                directory = base / folder
                files, uncertain = self.directory_files(directory)
                if uncertain:
                    return [directory]
                matches = {}
                for path in files:
                    if paramset_stem(path) != reference:
                        continue
                    if not safe_parameter_path(self.index, path):
                        return [path]
                    matches.setdefault(path.resolve(), path)
                if matches:
                    return list(matches.values())
        return []

    def named(self, env, reference: Any, kind: str, template_possible=False) -> str | None:
        if not _literal(reference):
            return 'unknown'
        if kind == 'ParameterSet':
            # All matching layers are fragments of one merged ParameterSet.
            staged, paths = {}, []
            bases = (self.index.root / 'environments', self.index.clusters[env.cluster].path, env.path / 'Inventory')
            for tier, base in enumerate(bases):
                files, uncertain = self.directory_files(base / 'parameters')
                if uncertain:
                    return 'unknown'
                for path in sorted(files):
                    if paramset_stem(path) != reference:
                        continue
                    if tier == 2:
                        paths.append(path)
                    else:
                        name = paramset_stem(path) + '.yml' if path.name.endswith('.j2') else path.name
                        staged[name] = path
            paths.extend(staged.values())
        else:
            paths = self.named_paths(env, reference, PROFILE_DIRS)
        if not paths:
            return 'unknown' if template_possible else 'missing'
        if kind != 'ParameterSet' and len(paths) > 1:
            return 'ambiguous'
        return None if all(self.read(path) is not None for path in paths) else 'unknown'

    def credential(self, bag: SecurityBag, identifier: str) -> str | None:
        if not _literal(identifier):
            return 'unknown'
        env = self.envs.get(bag.environment)
        if bag.catalog is not None:
            document = self.read(bag.catalog)
            if document is None:
                return 'unknown'
            if identifier == 'sops' or identifier not in document.doc:
                return 'missing'
            return None if isinstance(document.doc[identifier], dict) else 'unknown'
        runtime_id = bag.fields is not None and set(bag.fields) <= {'credentialsId', 'defaultCredentialsId', 'tokenSecret'}
        if env is None or (bag.fields is not None and not runtime_id):
            # The selected root/deployer catalog is not available.
            return 'unknown'
        generated = env.path / 'Credentials/credentials.yml'
        if generated.exists() or generated.is_symlink():
            return 'unknown'  # collector rejected the selected catalog; never fall back
        paths = [source.path for source in self.inputs.sources
                 if source.environment == env.full_name and source.kind == 'passport']
        for reference in env.shared_credential_bindings:
            if not _literal(reference):
                return 'unknown'
            selected = self.named_paths(env, reference, CREDENTIAL_DIRS)
            if len(selected) > 1:
                return 'ambiguous'
            if not selected or self.read(selected[0]) is None:
                return 'unknown'
            paths.extend(selected)
        entry = None
        for path in paths:
            document = self.read(path)
            if document is None:
                return 'unknown'
            if identifier != 'sops' and identifier in document.doc:
                entry = document.doc[identifier]
        if isinstance(entry, dict):
            return None
        # Templates and generation can supply IDs absent from the authored inputs.
        return 'unknown'

    def walk(self, document: LoadedYaml, bag: SecurityBag, value: Any, prefix: tuple,
             seen: frozenset[int] = frozenset()):
        if isinstance(value, dict) and value.get('$type') == 'credRef':
            identifier = value.get('credId')
            state = self.credential(bag, identifier) if _literal(identifier) else 'unknown'
            self.emit(document, prefix, bag.environment, 'Credential', state)
            return
        if isinstance(value, str) and _INTENT.search(value):
            matcher = _SYSTEM if bag.fields is not None else _RUNTIME
            matches = list(matcher.finditer(value))
            remaining = matcher.sub('', value)
            if not matches or _INTENT.search(remaining):
                self.emit(document, prefix, bag.environment, 'Credential', 'unknown')
            for match in matches:
                self.emit(document, prefix, bag.environment, 'Credential', self.credential(bag, match[2]))
            return
        if not isinstance(value, (dict, list)) or id(value) in seen:
            return
        seen = seen | {id(value)}
        for key, child in (value.items() if isinstance(value, dict) else enumerate(value)):
            self.walk(document, bag, child, (*prefix, key), seen)

    def bindings(self, env):
        document = self.read(env.path / 'Inventory/env_definition.yml')
        if document is None:
            return
        template = document.doc.get('envTemplate')
        if not isinstance(template, dict):
            return
        template_possible = any(template.get(key) for key in ('name', 'artifact', 'templateArtifact'))
        for category in Category:
            field = category.binding_field
            targets = template.get(field)
            if not isinstance(targets, dict):
                continue
            for target, references in targets.items():
                if not isinstance(references, list):
                    continue  # schema validity is INT-1
                for i, reference in enumerate(references):
                    self.emit(document, ('envTemplate', field, target, i), env.full_name, 'ParameterSet',
                              self.named(env, reference, 'ParameterSet', template_possible))
        profiles = template.get('envSpecificResourceProfiles')
        if isinstance(profiles, dict):
            for target, reference in profiles.items():
                self.emit(document, ('envTemplate', 'envSpecificResourceProfiles', target), env.full_name,
                          'Resource Profile', self.named(env, reference, 'Resource Profile'))

    def generated_profile(self, env, reference: Any, baseline: bool) -> str | None:
        if not _literal(reference):
            return 'unknown'
        directory = env.path / 'Profiles'
        try:
            physical = directory.resolve().relative_to(self.index.root)
            logical = directory.relative_to(self.index.root)
            if '.git' in physical.parts or '.git' in logical.parts:
                return 'unknown'
        except (OSError, RuntimeError, ValueError):
            return 'unknown'
        paths = {}
        files, uncertain = self.directory_files(directory)
        if uncertain:
            return 'unknown'
        for path in files:
            if paramset_stem(path) == reference:
                if not safe_parameter_path(self.index, path):
                    return 'unknown'
                paths.setdefault(path.resolve(), path)
        if len(paths) > 1:
            return 'ambiguous'
        if paths:
            return None if self.read(next(iter(paths.values()))) else 'unknown'
        return 'unknown' if baseline else self.named(env, reference, 'Resource Profile', True)

    def object_paths(self):
        paths = set(parameter_object_paths(self.index, self.connections))
        for env in self.index.environments:
            targets = set(env.resource_profile_bindings)
            for category in Category:
                targets.update(env.bound_targets(category))
            for target in targets:
                if isinstance(target, str) and target.lower() != 'cloud' and target not in ('.', '..') and Path(target).name == target:
                    paths.add((env.path / 'Namespaces' / target / 'namespace.yml', env.full_name))
        return sorted(paths)

    def objects(self):
        for path, environment in self.object_paths():
            document = self.read(path)
            if document is None:
                continue
            env = self.envs[environment]
            generated = env.path / 'Credentials/credentials.yml'
            catalog = generated if generated.exists() or generated.is_symlink() else None
            for section in ('deployParameters', 'e2eParameters', 'technicalConfigurationParameters'):
                if section in document.doc:
                    bag = SecurityBag(path, (section,), environment, catalog)
                    self.walk(document, bag, document.doc[section], (section,))
            if path.name == 'namespace.yml' and document.doc.get('credentialsId') not in (None, ''):
                bag = SecurityBag(path, (), environment, catalog, ('credentialsId',))
                identifier = document.doc['credentialsId']
                self.emit(document, ('credentialsId',), environment, 'Credential', self.credential(bag, identifier))
            for field in _PARAMSET_FIELDS:
                references = document.doc.get(field)
                if isinstance(references, list):
                    for i, reference in enumerate(references):
                        self.emit(document, (field, i), environment, 'ParameterSet', self.named(env, reference, 'ParameterSet', True))
            profile = document.doc.get('profile')
            if isinstance(profile, dict):
                for field in ('name', 'baseline', 'override_name'):
                    if profile.get(field):
                        # Baselines belong to the unavailable template, not instance override files.
                        state = self.generated_profile(env, profile[field], field == 'baseline')
                        self.emit(document, ('profile', field), environment, 'Resource Profile', state)

    def run(self):
        for env in self.index.environments:
            self.bindings(env)
        self.objects()
        for bag in self.inputs.bags:
            document = self.read(bag.path)
            if document is None:
                continue
            value = _at(document.doc, bag.prefix)
            if bag.fields is None:
                self.walk(document, bag, value, bag.prefix)
            elif isinstance(value, dict):
                for field in bag.fields:
                    if field not in value or value[field] in (None, ''):
                        continue
                    prefix = (*bag.prefix, field)
                    if field in ('credentialsId', 'defaultCredentialsId', 'tokenSecret'):
                        state = self.credential(bag, value[field]) if _literal(value[field]) else 'unknown'
                        self.emit(document, prefix, bag.environment, 'Credential', state)
                    else:
                        self.walk(document, bag, value[field], prefix)
        return sorted(self.findings.values(), key=lambda f: (f.path.as_posix(), f.line, f.column, f.scope, f.key, f.message))


def check(index: RepoIndex, connections: Connections | None = None) -> list[Finding]:
    return _Checker(index, connections or compute_connections(index)).run()
