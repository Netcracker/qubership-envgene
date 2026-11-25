"""PLACE-6: Pipeline ParameterSets bind to the Cloud."""

from __future__ import annotations

from pathlib import Path

from ..connections import Connections, compute_connections
from ..discovery import ENV_DEFINITION_FILE, INVENTORY_DIR
from ..model import Category, Finding, Location, RepoIndex, Severity
from ..rulemeta import RULES
from ..yamlio import LoadedYaml, YamlReadError, load

_MESSAGE = (
    "{target} is not the Cloud; pipeline ParameterSets must bind under "
    "envSpecificE2EParamsets.cloud."
)
_HINT = "Move the envSpecificE2EParamsets.{target} list to cloud."


def check(index: RepoIndex, connections: Connections | None = None) -> list[Finding]:
    connections = connections or compute_connections(index)
    selected_targets = {
        (use.environment, use.target)
        for uses in connections.parameter_uses.values()
        for use in uses
        if use.category is Category.E2E
    }
    findings: list[Finding] = []
    for env in index.environments:
        path = env.path / INVENTORY_DIR / ENV_DEFINITION_FILE
        loaded: LoadedYaml | None = None
        for target in env.bound_targets(Category.E2E):
            if target.lower() == "cloud" or (env.full_name, target) not in selected_targets:
                continue
            if loaded is None:
                try:
                    loaded = load(path)
                except YamlReadError:
                    break
            line, column = loaded.position(
                ("envTemplate", "envSpecificE2EParamsets", target)
            )
            findings.append(_finding(env.cluster, env.name, path, target, line, column))
    findings.sort(key=lambda item: (item.path.as_posix(), item.key, item.line))
    return findings


def _finding(
    cluster: str,
    env_name: str,
    path: Path,
    target: str,
    line: int,
    column: int,
) -> Finding:
    meta = RULES["PLACE-6"]
    return Finding(
        rule="PLACE-6",
        severity=Severity.WARNING,
        path=path,
        line=line,
        column=column,
        issue_type=meta.default_issue_type,
        action=meta.default_action,
        key=target,
        scope=f"{cluster}/{env_name}",
        message=_MESSAGE.format(target=target),
        hint=_HINT.format(target=target),
        related=(),
        locations=(Location(path, line, column),),
    )
