"""Shared local input selection for parameter security rules."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from .connections import Connections, PROFILE_DIRS, resolve_named_reference
from .model import RepoIndex


def safe_parameter_path(index: RepoIndex, path: Path) -> bool:
    try:
        logical = path.absolute().relative_to(index.root)
        physical = path.resolve().relative_to(index.root)
        return ".git" not in logical.parts and ".git" not in physical.parts and path.is_file()
    except (ValueError, OSError, RuntimeError):
        return False


def parameter_object_paths(index: RepoIndex, connections: Connections) -> Iterator[tuple[Path, str]]:
    targets: dict[str, set[str]] = {}
    for uses in connections.parameter_uses.values():
        for use in uses:
            targets.setdefault(use.environment, set()).add(use.target)
    for env in index.environments:
        yield env.path / "cloud.yml", env.full_name
        used = set(targets.get(env.full_name, ()))
        for target, reference in env.resource_profile_bindings.items():
            if resolve_named_reference(index, env, reference, index.resource_profiles, PROFILE_DIRS):
                used.add(target)
        for target in sorted(used):
            if target.lower() == "cloud" or target in {".", ".."} or Path(target).name != target:
                continue
            yield env.path / "Namespaces" / target / "namespace.yml", env.full_name


