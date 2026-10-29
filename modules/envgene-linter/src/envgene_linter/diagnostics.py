"""Safe, located incomplete checks shared by source readers and rules."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .model import RepoIndex, SkippedCheck
from .read_errors import ReadProblem
from .source_scope import is_generated_output

if TYPE_CHECKING:
    from .connections import Connections

_PARAMSET_RULES = {'PLACE-1', 'PLACE-2', 'PLACE-4', 'PLACE-8', 'SEC-1', 'SEC-3', 'SEC-4', 'SEC-5',
                   'NAME-1', 'NAME-2', 'VAL-4'}
_PASSPORT_RULES = {'PLACE-1', 'PLACE-4', 'PLACE-9', 'NAME-2'}


def skip_check(index: RepoIndex, rule: str, path: Path, reason: str,
               line: int = 1, column: int = 1) -> None:
    if is_generated_output(index, path):
        return
    check = SkippedCheck(rule, path, line, column, reason)
    if check not in index.skipped_checks:
        index.skipped_checks.append(check)
        index.skipped.append(f'{rule}: {reason}: {path.relative_to(index.root)}:{line}:{column}')


def skip_read(index: RepoIndex, rule: str, problem: ReadProblem, path: Path | None = None) -> None:
    skip_check(index, rule, path or problem.path, problem.reason, problem.line, problem.column)


def attach_discovery_problems(index: RepoIndex, connections: Connections, enabled: set[str]) -> bool:
    """Associate failed content with surviving inputs, returning promotion uncertainty."""
    definitions = {(env.path / 'Inventory/env_definition.yml').resolve() for env in index.environments}
    incomplete_merge = False
    groups = (
        (connections.parameter_sets, 'ParameterSet', _PARAMSET_RULES),
        (connections.passports, 'Cloud Passport', _PASSPORT_RULES),
        (connections.resource_profiles, 'Resource Profile Override', {'PLACE-8'}),
        (connections.credentials, 'Shared credentials', {'PLACE-8'}),
        (connections.artifact_definitions, 'Artifact definition', {'NAME-2', 'SEC-5'}),
    )
    for problem in index.read_problems:
        physical = problem.path.resolve()
        if physical in definitions:
            incomplete_merge = True
            for rule in sorted(enabled - {'TPL-1', 'TPL-4', 'TPL-6'}):
                skip_read(index, rule, problem)
        for paths, kind, rules in groups:
            if physical not in paths:
                continue
            incomplete_merge |= kind in {'ParameterSet', 'Cloud Passport'}
            alias = connections.selected_aliases.get((kind, physical), problem.path)
            for rule in sorted(enabled & rules):
                skip_read(index, rule, problem, alias)
    return incomplete_merge
