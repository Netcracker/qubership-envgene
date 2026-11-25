"""Enumerate and stage local ParameterSet sources using one selection contract."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .model import EnvModel, Layer, ParamsetFile, ParamsetLayout, RepoIndex

ALL_LAYERS = frozenset(Layer)
_TEMPLATE_DIRECTORY = re.compile(r'/from_(\\w+_)?template/')
_ROLE_DIRECTORIES = ('from_template', 'from_origin_template', 'from_peer_template')


@dataclass(frozen=True)
class SourceScan:
    paths: tuple[Path, ...] = ()
    unavailable: frozenset[Path] = frozenset()
    incomplete: bool = False
    layout: ParamsetLayout | None = None


def _supported_path(path: Path) -> bool:
    return path.suffix in {'.yml', '.yaml', '.json', '.j2'}


def scan_directory(directory: Path, root: Path) -> SourceScan:
    """Keep unsafe file names as shadow markers, without reading their targets."""
    paths, unavailable, incomplete = [], set(), False
    files, directories = set(), set()
    try:
        logical = directory.relative_to(root)
        physical = directory.resolve().relative_to(root)
        if '.git' in logical.parts or '.git' in physical.parts or any(
            path.is_symlink() for path in (directory, *directory.parents) if path != root and root in path.parents
        ):
            return SourceScan(incomplete=True)
        if not directory.exists():
            return SourceScan()
        if not directory.is_dir():
            return SourceScan(incomplete=True)
    except (OSError, RuntimeError, ValueError):
        return SourceScan(incomplete=True)
    pending = [directory]
    while pending:
        current = pending.pop()
        try:
            entries = sorted(current.iterdir())
        except OSError:
            incomplete = True
            continue
        for path in entries:
            try:
                if path.name == '.git':
                    incomplete = True
                    continue
                if path.is_dir():
                    directories.add(path.relative_to(directory))
                    if path.is_symlink():
                        incomplete = True
                    else:
                        pending.append(path)
                    continue
                files.add(path.relative_to(directory))
                if not _supported_path(path):
                    if path.is_symlink() and not path.exists():
                        incomplete = True
                    continue
                paths.append(path)
                physical = path.resolve(strict=True).relative_to(root)
                if '.git' in physical.parts or not path.is_file():
                    unavailable.add(path)
            except (OSError, RuntimeError, ValueError):
                if _supported_path(path):
                    if path not in paths:
                        paths.append(path)
                    unavailable.add(path)
                else:
                    incomplete = True
    return SourceScan(tuple(sorted(paths)), frozenset(unavailable), incomplete,
                      ParamsetLayout(frozenset(files), frozenset(directories)))


@dataclass(frozen=True)
class ResolvedEntry:
    file: ParamsetFile
    reference: str
    tier: int
    staged_path: str


def staged_filename(file: ParamsetFile) -> str:
    name = (file.relative_path or Path(file.path.name)).as_posix()
    # Keep the existing conservative alias for unrendered YAML Jinja inputs.
    for suffix in ('.yml.j2', '.yaml.j2'):
        if name.endswith(suffix):
            return name[:-len(suffix)] + '.yml'
    return name


def _staged_files(index: RepoIndex, env: EnvModel) -> dict[str, ParamsetFile]:
    staged = {}
    for files in (index.site_paramsets, index.clusters[env.cluster].paramsets, env.paramsets):
        for file in files:
            name = staged_filename(file)
            if file.layer is Layer.ENVIRONMENT:
                name = f'from_instance/{name}'
            staged[name] = file
    return staged


def source_files(index: RepoIndex, env: EnvModel) -> list[ParamsetFile]:
    return [*index.site_paramsets, *index.clusters[env.cluster].paramsets, *env.paramsets]


def staging_complete(index: RepoIndex, env: EnvModel) -> bool:
    directories = (index.root / 'environments/parameters',
                   index.clusters[env.cluster].path / 'parameters', env.path / 'Inventory/parameters')
    if any(directory in index.incomplete_paramset_dirs for directory in directories):
        return False
    staged_files, staged_directories = set(), set()

    def ensure_directory(path: Path) -> bool:
        ancestors = {parent for parent in (path, *path.parents) if parent != Path('.')}
        if ancestors & staged_files:
            return False
        staged_directories.update(ancestors)
        return True

    for number, directory in enumerate(directories):
        layout = index.paramset_layouts.get(directory)
        if layout is None:
            continue
        prefix = Path('from_instance') if number == 2 else Path('.')
        for path in layout.directories:
            if not ensure_directory(prefix / path):
                return False
        for path in layout.files:
            staged = prefix / path
            if staged in staged_directories or not ensure_directory(staged.parent):
                return False
            staged_files.add(staged)
    return True


def reference_complete(index: RepoIndex, env: EnvModel, reference: str) -> bool:
    if not staging_complete(index, env):
        return False
    return not any(file.stem == reference and any(role in path for role in _ROLE_DIRECTORIES)
                   for path, file in _staged_files(index, env).items())


def resolve_reference(
    index: RepoIndex, env: EnvModel, reference: str, layers: frozenset[Layer] = ALL_LAYERS,
    *, include_unavailable: bool = False,
) -> list[ResolvedEntry]:
    if not reference_complete(index, env, reference):
        return []
    entries = []
    for path, file in _staged_files(index, env).items():
        if file.stem != reference or file.layer not in layers:
            continue
        if not include_unavailable and (file.is_jinja or file.unavailable):
            continue
        tier = 2 if 'from_instance' in path else 0 if _TEMPLATE_DIRECTORY.search('/' + path) else 1
        entries.append(ResolvedEntry(file, reference, tier, path))
    return sorted(entries, key=lambda entry: (entry.tier, entry.staged_path))
