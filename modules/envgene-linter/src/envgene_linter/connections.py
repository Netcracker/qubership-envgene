"""Resolve the physical files that environments visibly use."""

from __future__ import annotations

import os
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from .discovery import paramset_stem
from .effective import resolve_reference
from .model import Category, NamedEntityFile, ParamsetFile, PassportFile, RepoIndex
from .passport import resolve_passport

PROFILE_DIRS = ("resource_profiles", "rp_override", "Profiles", "parameters")
CREDENTIAL_DIRS = ("credentials", "Credentials", "shared-credentials")
ARTIFACT_DEFINITIONS_DIR = "configuration/artifact_definitions"


@dataclass(frozen=True)
class ParameterSetUse:
    environment: str
    category: Category
    target: str
    reference: str


@dataclass
class Connections:
    parameter_sets: frozenset[Path] = frozenset()
    parameter_files: dict[Path, ParamsetFile] = field(default_factory=dict)
    parameter_uses: dict[Path, tuple[ParameterSetUse, ...]] = field(default_factory=dict)
    environment_parameter_sets: dict[str, frozenset[Path]] = field(default_factory=dict)
    environment_paths: dict[str, frozenset[Path]] = field(default_factory=dict)
    passports: frozenset[Path] = frozenset()
    environment_passports: dict[str, PassportFile] = field(default_factory=dict)
    resource_profiles: frozenset[Path] = frozenset()
    credentials: frozenset[Path] = frozenset()
    artifact_definitions: frozenset[Path] = frozenset()
    shared_template_variables: frozenset[Path] = frozenset()
    selected_aliases: dict[tuple[str, Path], Path] = field(default_factory=dict)

    @property
    def selected_paths(self) -> frozenset[Path]:
        return frozenset().union(
            self.parameter_sets,
            self.passports,
            self.resource_profiles,
            self.credentials,
            self.shared_template_variables,
            self.artifact_definitions,
        )


def _under(path: Path, directory: Path) -> bool:
    try:
        path.relative_to(directory)
    except ValueError:
        return False
    return True


def _matching_named_paths(
    records: Iterable[NamedEntityFile], directory: Path, reference: str
) -> dict[Path, Path]:
    matches: dict[Path, Path] = {}
    for record in records:
        if record.is_jinja:
            continue
        for path in (record.path, *record.aliases):
            if paramset_stem(path) == reference and _under(path, directory):
                matches.setdefault(record.path.resolve(), path)
                break
    return matches


def resolve_named_reference(
    index: RepoIndex,
    env,
    reference: str,
    records: list[NamedEntityFile],
    directories: tuple[str, ...],
) -> set[Path]:
    return set(_resolve_named_reference_paths(index, env, reference, records, directories))


def _resolve_named_reference_paths(
    index: RepoIndex,
    env,
    reference: str,
    records: list[NamedEntityFile],
    directories: tuple[str, ...],
) -> dict[Path, Path]:
    bases = (
        env.path / "Inventory",
        index.clusters[env.cluster].path,
        index.root / "environments",
    )
    for base in bases:
        for folder in directories:
            matches = _matching_named_paths(records, base / folder, reference)
            if matches:
                return matches
    return {}


_UNSAFE = object()


def _has_jinja(reference: str) -> bool:
    return any(marker in reference for marker in ("{{", "}}", "{%", "%}", "{#", "#}"))


def _safe_candidate(index: RepoIndex, candidate: Path) -> Path | object:
    try:
        logical = candidate.absolute().relative_to(index.root)
        physical = candidate.resolve()
        relative = physical.relative_to(index.root)
    except (OSError, RuntimeError, ValueError):
        return _UNSAFE
    if ".git" in logical.parts or ".git" in relative.parts or not physical.is_file():
        return _UNSAFE
    return physical


def _safe_search_directory(index: RepoIndex, directory: Path) -> bool:
    try:
        logical = directory.absolute().relative_to(index.root)
        physical = directory.resolve()
        relative = physical.relative_to(index.root)
    except (OSError, RuntimeError, ValueError):
        return False
    if ".git" in logical.parts or ".git" in relative.parts:
        return False
    current = index.root
    for part in logical.parts:
        current /= part
        if current.is_symlink():
            return False
    return True


def _find_shared_template_variable(
    index: RepoIndex, directory: Path, reference: str
) -> tuple[Path, Path] | object | None:
    if not _safe_search_directory(index, directory) or not directory.is_dir():
        return None
    for root, directories, files in os.walk(directory, followlinks=False):
        root_path = Path(root)
        directories[:] = [
            name
            for name in directories
            if name != ".git" and not (root_path / name).is_symlink()
        ]
        for filename in files:
            if not filename.endswith((".yml", ".yaml")):
                continue
            if Path(filename).stem != reference:
                continue
            candidate = root_path / filename
            physical = _safe_candidate(index, candidate)
            if physical is _UNSAFE:
                return _UNSAFE
            return physical, candidate
    return None


def _resolve_shared_template_variable(
    index: RepoIndex, env, reference: str
) -> tuple[Path, Path] | None:
    if _has_jinja(reference):
        return None
    levels = (
        env.path / "Inventory",
        index.clusters[env.cluster].path,
        index.root / "environments",
    )
    directories = [
        level / name
        for level in levels
        for name in ("configuration", "configurations")
    ]
    directories.append(env.path / "Inventory")
    for directory in directories:
        result = _find_shared_template_variable(index, directory, reference)
        if result is _UNSAFE:
            return None
        if result is not None:
            return result
    return None


def _artifact_application(selector: str) -> str | None:
    if any(marker in selector for marker in ("{{", "}}", "{%", "%}", "{#", "#}")):
        return None
    parts = selector.split(":")
    if len(parts) < 2 or not parts[0] or not parts[1]:
        return None
    return parts[0]


def _artifact_definition(index: RepoIndex, application: str) -> Path | None:
    directory = (index.root / ARTIFACT_DEFINITIONS_DIR).resolve()
    records = {
        record.path.resolve(): record
        for record in index.named_entities
        if record.kind == "Artifact definition"
        and record.path.resolve().is_relative_to(index.root)
    }
    for suffix in (".yml", ".yaml"):
        candidate = (directory / f"{application}{suffix}").resolve()
        if candidate.parent == directory and candidate in records:
            return candidate
    return None


def compute_connections(index: RepoIndex) -> Connections:
    uses: dict[Path, list[ParameterSetUse]] = defaultdict(list)
    selected_files: dict[Path, ParamsetFile] = {}
    by_environment: dict[str, set[Path]] = defaultdict(set)
    all_by_environment: dict[str, set[Path]] = defaultdict(set)
    passports: set[Path] = set()
    environment_passports: dict[str, PassportFile] = {}
    profiles: set[Path] = set()
    credentials: set[Path] = set()
    shared_template_variables: set[Path] = set()
    artifacts: set[Path] = set()
    selected_aliases: dict[tuple[str, Path], Path] = {}

    credential_records = {record.path.resolve() for record in index.credential_files}
    for env in index.environments:
        for category in Category:
            for target, references in env.bound_targets(category).items():
                for reference in references:
                    use = ParameterSetUse(env.full_name, category, target, reference)
                    for entry in resolve_reference(index, env, reference):
                        path = entry.file.path.resolve()
                        selected_files.setdefault(path, entry.file)
                        selected_aliases.setdefault(("ParameterSet", path), entry.file.path)
                        uses[path].append(use)
                        by_environment[env.full_name].add(path)
                        all_by_environment[env.full_name].add(path)

        passport = resolve_passport(index, env)
        if passport.note and passport.note not in index.skipped:
            index.skipped.append(passport.note)
        if passport.file is not None:
            path = passport.file.path.resolve()
            passports.add(path)
            selected_aliases.setdefault(("Cloud Passport", path), passport.file.path)
            environment_passports[env.full_name] = passport.file
            all_by_environment[env.full_name].add(path)

        for reference in env.resource_profile_bindings.values():
            selected_paths = _resolve_named_reference_paths(
                index, env, reference, index.resource_profiles, PROFILE_DIRS
            )
            selected = set(selected_paths)
            profiles.update(selected)
            all_by_environment[env.full_name].update(selected)
            for path, alias in selected_paths.items():
                selected_aliases.setdefault(("Resource Profile Override", path), alias)
        for reference in env.shared_credential_bindings:
            selected_paths = _resolve_named_reference_paths(
                index, env, reference, index.credential_files, CREDENTIAL_DIRS
            )
            selected = set(selected_paths)
            credentials.update(selected)
            all_by_environment[env.full_name].update(selected)
            for path, alias in selected_paths.items():
                selected_aliases.setdefault(("Shared credentials", path), alias)
        fixed_credentials = (
            env.path / "Inventory/credentials/inventory_generation_creds.yml"
        ).resolve()
        if fixed_credentials in credential_records:
            credentials.add(fixed_credentials)
            all_by_environment[env.full_name].add(fixed_credentials)
            selected_aliases.setdefault(
                ("Shared credentials", fixed_credentials),
                env.path / "Inventory/credentials/inventory_generation_creds.yml",
            )

        for reference in env.shared_template_variable_bindings:
            selected = _resolve_shared_template_variable(index, env, reference)
            if selected is None:
                continue
            physical, alias = selected
            shared_template_variables.add(physical)
            all_by_environment[env.full_name].add(physical)
            selected_aliases.setdefault(("Shared Template Variables", physical), alias)

        for selector in env.artifact_selectors:
            application = _artifact_application(selector)
            if application is None:
                continue
            selected = _artifact_definition(index, application)
            if selected is not None:
                artifacts.add(selected)
                all_by_environment[env.full_name].add(selected)

    return Connections(
        parameter_sets=frozenset(uses),
        parameter_files=selected_files,
        parameter_uses={path: tuple(items) for path, items in uses.items()},
        environment_parameter_sets={
            env.full_name: frozenset(by_environment.get(env.full_name, set()))
            for env in index.environments
        },
        environment_paths={
            env.full_name: frozenset(all_by_environment.get(env.full_name, set()))
            for env in index.environments
        },
        passports=frozenset(passports),
        environment_passports=environment_passports,
        resource_profiles=frozenset(profiles),
        credentials=frozenset(credentials),
        shared_template_variables=frozenset(shared_template_variables),
        artifact_definitions=frozenset(artifacts),
        selected_aliases=selected_aliases,
    )
