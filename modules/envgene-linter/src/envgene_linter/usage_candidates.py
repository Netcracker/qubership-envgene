"""Inventory authored entities without broadening connected inputs to other rules."""
from dataclasses import replace
from pathlib import Path

from .connections import Connections
from .discovery import NON_CLUSTER_DIRS, NON_ENV_DIRS
from .model import RepoIndex
from .security_sources import collect_security_sources
from .usage_model import Candidate
from .yamlio import YamlReadError, load


def safe_file(index, path):
    try:
        logical = path.absolute().relative_to(index.root)
        physical = path.resolve(strict=True)
        relative = physical.relative_to(index.root)
        if '.git' in logical.parts or '.git' in relative.parts or not physical.is_file():
            return None
        if any(parent.is_symlink() for parent in path.parents if parent != index.root and index.root in parent.parents):
            return None
        return physical
    except (OSError, RuntimeError, ValueError):
        return None


def read_mapping(index, path):
    if safe_file(index, path) is None:
        return None
    try:
        document = load(path)
        return document if isinstance(document.doc, dict) else None
    except YamlReadError:
        return None


def child_directories(path):
    try:
        return sorted(p for p in path.iterdir() if p.name != '.git' and not p.is_symlink() and p.is_dir())
    except OSError:
        return []


def yaml_files(path, recursive=True):
    if path.is_symlink():
        return []
    try:
        entries = sorted(path.iterdir())
    except OSError:
        return []
    result = [p for p in entries if p.suffix in ('.yml', '.yaml') and not p.is_dir()]
    if recursive:
        for directory in child_directories(path):
            result.extend(yaml_files(directory))
    return result


def authored_scopes(index):
    root = index.root / 'environments'
    yield root, tuple(env.full_name for env in index.environments)
    for cluster in child_directories(root):
        if cluster.name in NON_CLUSTER_DIRS:
            continue
        yield cluster, tuple(env.full_name for env in index.environments if env.cluster == cluster.name)
        for env in child_directories(cluster):
            if env.name not in NON_ENV_DIRS:
                yield env / 'Inventory', tuple(e.full_name for e in index.environments if e.path == env)


def collect_candidates(index: RepoIndex, connections: Connections) -> list[Candidate]:
    found = {}
    implicit = set()
    for env in index.environments:
        path = env.path / 'Inventory/credentials/inventory_generation_creds.yml'
        physical = safe_file(index, path)
        if physical:
            implicit.add(physical)
    generated = {p for env in index.environments
                 if (p := safe_file(index, env.path / 'Credentials/credentials.yml'))}

    def add(path, kind, environments):
        physical = safe_file(index, path)
        if physical is None or physical in implicit or physical in generated:
            return
        document = read_mapping(index, path)
        if document is None or (not document.doc and kind != 'Credential'):
            note = f'INT-4: skipped unreadable or invalid {kind} candidate: {path.relative_to(index.root)}'
            if note not in index.skipped:
                index.skipped.append(note)
            return
        if kind == 'ParameterSet' and not isinstance(document.doc.get('parameters'), dict) and not isinstance(document.doc.get('applications'), list):
            note = f'INT-4: skipped invalid ParameterSet candidate: {path.relative_to(index.root)}'
            if note not in index.skipped:
                index.skipped.append(note)
            return
        names = [k for k, v in document.doc.items() if isinstance(k, str) and k != 'sops' and isinstance(v, dict)] if kind == 'Credential' else [path.stem]
        stat = physical.stat()
        for name in names:
            # Inode identity also handles casing aliases on case-insensitive filesystems.
            key = (stat.st_dev, stat.st_ino, kind, name if kind == 'Credential' else '')
            line, column = document.position((name,)) if kind == 'Credential' else (1, 1)
            candidate = Candidate(path, physical, kind, name, tuple(sorted(environments)), (path,), line, column)
            if key in found:
                old = found[key]
                candidate = replace(old, environments=tuple(sorted(set(old.environments) | set(environments))),
                                    aliases=tuple(sorted(set(old.aliases) | {path})))
            found[key] = candidate

    for base, contexts in authored_scopes(index):
        directories = [('parameters', 'ParameterSet', False),
                       ('resource_profiles', 'Resource Profile Override', True),
                       ('rp_override', 'Resource Profile Override', True),
                       ('shared-template-variables', 'Shared Template Variable', True),
                       ('shared_template_variables', 'Shared Template Variable', True),
                       ('credentials', 'Credential', True), ('Credentials', 'Credential', True),
                       ('shared-credentials', 'Credential', True)]
        if base.name == 'Inventory':
            directories.append(('Profiles', 'Resource Profile Override', True))
        seen_directories = set()
        for directory, kind, recursive in directories:
            try:
                stat = (base / directory).stat()
            except OSError:
                continue
            identity = (stat.st_dev, stat.st_ino, kind)
            if identity in seen_directories:
                continue
            seen_directories.add(identity)
            for path in yaml_files(base / directory, recursive):
                add(path, kind, contexts)
    for kind, paths in [('Resource Profile Override', connections.resource_profiles),
                        ('Shared Template Variable', connections.shared_template_variables)]:
        for path in sorted(paths):
            aliases = [alias for (label, physical), alias in connections.selected_aliases.items() if physical == path]
            add(aliases[0] if aliases else path, kind,
                tuple(env for env, selected in connections.environment_paths.items() if path in selected))
    add(index.root / 'configuration/credentials/credentials.yml', 'Credential', ())
    inputs = collect_security_sources(index, connections)
    for bag in inputs.bags:
        if bag.catalog is not None:
            for logical in sorted(inputs.logical_paths.get(bag.catalog, {bag.catalog})):
                add(logical, 'Credential', (bag.environment,) if bag.environment else ())
    for source in inputs.sources:
        if source.kind != 'generated':
            for logical in sorted(inputs.logical_paths.get(source.path, {source.path})):
                add(logical, 'Credential', (source.environment,) if source.environment else ())
    return sorted(found.values(), key=lambda item: (str(item.path), item.kind, item.line, item.column))
