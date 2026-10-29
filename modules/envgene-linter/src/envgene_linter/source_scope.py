"""Recognize generated instance paths without inferring repository build state."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .model import Finding, RepoIndex

_OUTPUT_DIRECTORIES = frozenset({'Applications', 'Namespaces', 'Profiles', 'Credentials', 'effective-set'})
_OUTPUT_FILES = frozenset({'cloud.yml', 'tenant.yml', 'bg_domain.yml', 'composite_structure.yml'})
_INVENTORY_OUTPUTS = frozenset({
    'namespace-map.yml', 'deploy-plan.yml', 'deploy-plan-calculated.yml', 'deploy-plan-mapped.yml',
})


def _generated_path(scope: SourceScope, path: Path) -> bool:
    try:
        parts = path.relative_to(scope.root).parts
    except ValueError:
        return False
    if len(parts) < 4 or parts[0] != 'environments':
        return False
    if scope.root.joinpath(*parts[:3]) not in scope.environments:
        return False
    tail = parts[3:]
    return (tail[0] in _OUTPUT_DIRECTORIES
            or (len(tail) == 1 and tail[0] in _OUTPUT_FILES)
            or (len(tail) == 2 and tail[0] == 'Inventory' and tail[1] in _INVENTORY_OUTPUTS))


@dataclass(frozen=True)
class SourceScope:
    root: Path
    environments: frozenset[Path]

    def is_generated(self, path: Path) -> bool:
        """Retain the logical role even when the physical target has another path."""
        if _generated_path(self, path.absolute()):
            return True
        try:
            return _generated_path(self, path.resolve())
        except (OSError, RuntimeError):
            # Eligibility never relaxes the separate filesystem-safety guards.
            return False


def is_generated_output(index: RepoIndex, path: Path) -> bool:
    scope = index.source_scope or SourceScope(index.root, frozenset(env.path for env in index.environments))
    return scope.is_generated(path)


def finding_in_scope(index: RepoIndex, finding: Finding) -> bool:
    return not is_generated_output(index, finding.path) and all(
        not is_generated_output(index, location.path) for location in finding.file_locations()
    )
