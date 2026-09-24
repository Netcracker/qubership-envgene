"""Observe direct references in known local consumers without proving deletion safe."""
import re
from pathlib import Path

from .connections import Connections
from .model import Category, RepoIndex
from .security_sources import collect_security_sources
from .security_values import literal_name
from .usage_candidates import authored_scopes, child_directories, read_mapping, safe_file, yaml_files
from .usage_model import Candidate, Gap, Reference, Usage

_KINDS = ('ParameterSet', 'Shared Template Variable', 'Resource Profile Override', 'Credential')
_PARAMSETS = ('deployParameterSets', 'e2eParameterSets', 'technicalConfigurationParameterSets')
_BARE = ('credentialsId', 'defaultCredentialsId', 'tokenSecret')
_CALL = r'''creds\s*\.\s*get\s*\(\s*(["'])([^"'{}\\\r\n]+)\1\s*\)(?:\s*\.\s*[A-Za-z_]\w*)?'''
_RUNTIME = re.compile(r'\$\{\s*' + _CALL + r'\s*\}')
_SYSTEM = re.compile(r'envgen\s*\.\s*' + _CALL)
_INTENT = re.compile(r'(?:envgen\s*\.\s*)?creds\s*\.\s*get\s*\(')


def _literal(value):
    return literal_name(value) and not any(mark in value for mark in ('}}', '%}', '{#', '#}'))


class _Analysis:
    def __init__(self, index, connections, candidates):
        self.index, self.connections, self.candidates = index, connections, candidates
        self.inputs = collect_security_sources(index, connections)
        self.envs = {env.full_name: env for env in index.environments}
        self.references = []
        self.gaps = []
        self.documents = {}

    def gap(self, source, environment, kind, reason):
        gap = Gap(source, kind, environment, reason)
        if gap not in self.gaps:
            self.gaps.append(gap)

    def read(self, path, environment, kinds=_KINDS):
        origins = self.inputs.logical_paths.get(path, {path})
        if any(safe_file(self.index, logical) is None for logical in origins):
            for kind in kinds:
                self.gap(path, environment, kind, 'unreadable')
            return None
        if path not in self.documents:
            self.documents[path] = read_mapping(self.index, path)
        document = self.documents[path]
        if document is None:
            for kind in kinds:
                self.gap(path, environment, kind, 'unreadable')
        return document.doc if document is not None else None

    def reference(self, source, environment, kind, value, catalog=None, category=None, target=None):
        if not _literal(value):
            self.gap(source, environment, kind, 'dynamic')
            return
        reference = Reference(source, kind, value, environment, catalog, category, target)
        if reference not in self.references:
            self.references.append(reference)

    def walk(self, source, environment, value, catalog=None, system=False, seen=frozenset()):
        if isinstance(value, dict) and value.get('$type') == 'credRef':
            self.reference(source, environment, 'Credential', value.get('credId'), catalog)
            return
        if isinstance(value, str) and _INTENT.search(value):
            matcher = _SYSTEM if system else _RUNTIME
            for match in matcher.finditer(value):
                self.reference(source, environment, 'Credential', match[2], catalog)
            if _INTENT.search(matcher.sub('', value)):
                self.gap(source, environment, 'Credential', 'dynamic')
            return
        if not isinstance(value, (dict, list)) or id(value) in seen:
            return
        seen = seen | {id(value)}
        for child in (value.values() if isinstance(value, dict) else value):
            self.walk(source, environment, child, catalog, system, seen)

    def parameter_bag(self, source, environment, value, catalog):
        if isinstance(value, dict):
            self.walk(source, environment, value, catalog)
        elif value not in (None, ''):
            self.gap(source, environment, 'Credential', 'unreadable')

    def bindings(self, env):
        path = env.path / 'Inventory/env_definition.yml'
        doc = self.read(path, env.full_name)
        if doc is None:
            return
        template = doc.get('envTemplate')
        if not isinstance(template, dict):
            for kind in _KINDS:
                self.gap(path, env.full_name, kind, 'dynamic')
            return
        for category in Category:
            bindings = template.get(category.binding_field, {})
            if not isinstance(bindings, dict):
                self.gap(path, env.full_name, 'ParameterSet', 'dynamic')
                continue
            for target, values in bindings.items():
                if not isinstance(values, list):
                    self.gap(path, env.full_name, 'ParameterSet', 'dynamic')
                    continue
                for value in values:
                    self.reference(path, env.full_name, 'ParameterSet', value, category=category.value, target=str(target))
        for field, kind in [('sharedTemplateVariables', 'Shared Template Variable'),
                            ('envSpecificResourceProfiles', 'Resource Profile Override')]:
            values = template.get(field, {} if field == 'envSpecificResourceProfiles' else [])
            if isinstance(values, dict) and field == 'envSpecificResourceProfiles':
                for target, value in values.items():
                    self.reference(path, env.full_name, kind, value, target=str(target))
            elif isinstance(values, list) and field == 'sharedTemplateVariables':
                for value in values:
                    self.reference(path, env.full_name, kind, value)
            else:
                self.gap(path, env.full_name, kind, 'dynamic')
        shared = template.get('sharedMasterCredentialFiles', [])
        if not isinstance(shared, list) or any(not _literal(value) for value in shared):
            self.gap(path, env.full_name, 'Credential', 'dynamic')

    def objects(self, env):
        paths = [env.path / 'cloud.yml']
        paths.extend(directory / 'namespace.yml' for directory in child_directories(env.path / 'Namespaces'))
        generated = env.path / 'Credentials/credentials.yml'
        catalog = generated if generated.exists() or generated.is_symlink() else None
        for path in paths:
            if not path.exists() and not path.is_symlink():
                continue
            doc = self.read(path, env.full_name)
            if doc is None:
                continue
            for section in ('deployParameters', 'e2eParameters', 'technicalConfigurationParameters'):
                self.parameter_bag(path, env.full_name, doc.get(section), catalog)
            for field in _BARE:
                if field in doc and doc[field] not in (None, ''):
                    self.reference(path, env.full_name, 'Credential', doc[field], catalog)
            for field in _PARAMSETS:
                if field not in doc:
                    continue
                values = doc[field]
                if not isinstance(values, list):
                    self.gap(path, env.full_name, 'ParameterSet', 'dynamic')
                else:
                    for value in values:
                        self.reference(path, env.full_name, 'ParameterSet', value, target=path.parent.name)
            profile = doc.get('profile', {})
            if isinstance(profile, dict):
                for field in ('name', 'override_name'):
                    if profile.get(field):
                        self.reference(path, env.full_name, 'Resource Profile Override', profile[field])
            else:
                self.gap(path, env.full_name, 'Resource Profile Override', 'dynamic')

    def bags(self):
        for bag in self.inputs.bags:
            catalog = bag.catalog
            env = self.envs.get(bag.environment)
            if catalog is None:
                if bag.fields is not None and not set(bag.fields) <= set(_BARE):
                    # Missing system catalogs must not become runtime shared lookup.
                    self.gap(bag.path, bag.environment, 'Credential', 'unreadable')
                    continue
                if env is not None:
                    generated = env.path / 'Credentials/credentials.yml'
                    if generated.exists() or generated.is_symlink():
                        catalog = generated
            doc = self.read(bag.path, bag.environment, ('Credential',))
            value = doc
            for key in bag.prefix:
                if isinstance(value, dict):
                    value = value.get(key)
                elif isinstance(value, list) and isinstance(key, int) and key < len(value):
                    value = value[key]
                else:
                    value = None
            if bag.fields is None:
                self.walk(bag.path, bag.environment, value, catalog)
            elif isinstance(value, dict):
                for field in bag.fields:
                    if field not in value or value[field] in (None, ''):
                        continue
                    if field in _BARE:
                        self.reference(bag.path, bag.environment, 'Credential', value[field], catalog)
                    else:
                        self.walk(bag.path, bag.environment, value[field], catalog, system=True)
        for issue in self.inputs.issues:
            contexts = [env.full_name for env in self.envs.values() if env.path in issue.path.parents]
            for context in contexts or [None]:
                self.gap(issue.path, context, 'Credential', 'unreadable')

    def parameters(self):
        for base, environments in authored_scopes(self.index):
            directory = base / 'parameters'
            try:
                templates = [p for p in directory.iterdir() if p.name.endswith(('.yml.j2', '.yaml.j2'))]
            except OSError:
                templates = []
            for environment in environments or (None,):
                for path in templates:
                    self.gap(path, environment, 'Credential', 'dynamic')
                for path in yaml_files(directory, recursive=False):
                    doc = self.read(path, environment, ('Credential',))
                    if doc is None:
                        continue
                    env = self.envs.get(environment)
                    generated = env.path / 'Credentials/credentials.yml' if env else None
                    catalog = generated if generated and (generated.exists() or generated.is_symlink()) else None
                    if environment is None:
                        continue
                    self.parameter_bag(path, environment, doc.get('parameters'), catalog)
                    applications = doc.get('applications', [])
                    if isinstance(applications, list):
                        for application in applications:
                            if isinstance(application, dict):
                                self.parameter_bag(path, environment, application.get('parameters'), catalog)


    def matches(self, candidate, reference):
        if candidate.kind != reference.kind:
            return False
        if candidate.kind != 'Credential':
            if reference.environment not in candidate.environments:
                return False
            env = self.envs.get(reference.environment)
            if env is None:
                return False
            bases = (env.path / 'Inventory', self.index.clusters[env.cluster].path, self.index.root / 'environments')
            aliases = [alias for alias in candidate.aliases if any(
                alias.is_relative_to(base / directory)
                for base in bases for directory in {
                    'ParameterSet': ('parameters',),
                    'Resource Profile Override': ('resource_profiles', 'rp_override', 'Profiles', 'parameters'),
                    'Shared Template Variable': ('configuration', 'configurations'),
                }[candidate.kind]) or
                (candidate.kind == 'Shared Template Variable' and alias.is_relative_to(env.path / 'Inventory'))]
            if reference.name not in {alias.stem for alias in aliases}:
                return False
            if candidate.kind == 'Shared Template Variable':
                env = self.envs[reference.environment]
                # Canonical repository/cluster folders are not searched by the generator.
                return any(env.path / 'Inventory' in alias.parents or
                           'configuration' in alias.relative_to(self.index.root).parts or
                           'configurations' in alias.relative_to(self.index.root).parts for alias in candidate.aliases)
            return True
        if candidate.name != reference.name or candidate.name == 'sops':
            return False
        env = self.envs.get(reference.environment)
        generated = env.path / 'Credentials/credentials.yml' if env else None
        if reference.catalog is not None:
            physical = safe_file(self.index, reference.catalog)
            if physical is None:
                return False
            doc = self.read(reference.catalog, reference.environment, ('Credential',))
            if doc is None or reference.name not in doc:
                return False
            if generated is None or physical != safe_file(self.index, generated):
                return physical == candidate.physical
            self.gap(reference.source, reference.environment, 'Credential', 'provenance')
        if env is None or reference.environment not in candidate.environments:
            return False
        # Authored source membership, not ID equality or secret-value equality, establishes origin scope.
        sources = {source.path for source in self.inputs.sources
                   if source.environment == reference.environment and source.kind in ('shared', 'passport')
                   and all(safe_file(self.index, logical) is not None
                           for logical in self.inputs.logical_paths.get(source.path, {source.path}))}
        return candidate.physical in sources

    def run(self):
        for env in self.envs.values():
            self.bindings(env)
            self.objects(env)
        self.bags()
        self.parameters()
        matched = [(candidate, tuple(ref for ref in self.references if self.matches(candidate, ref)))
                   for candidate in self.candidates]
        result = []
        for candidate, references in matched:
            gaps = [gap for gap in self.gaps if gap.kind == candidate.kind and
                    (gap.environment is None or gap.environment in candidate.environments)]
            if not candidate.environments:
                gaps.append(Gap(candidate.path, candidate.kind, None, 'no-environment'))
            if candidate.kind == 'Shared Template Variable' and not references:
                if any('shared-template-variables' in alias.parts or 'shared_template_variables' in alias.parts
                       for alias in candidate.aliases):
                    gaps.append(Gap(candidate.path, candidate.kind, None, 'lookup'))
            result.append(Usage(candidate, references, tuple(gaps)))
        return result


def analyze_usage(index: RepoIndex, connections: Connections, candidates: list[Candidate]) -> list[Usage]:
    return _Analysis(index, connections, candidates).run()
