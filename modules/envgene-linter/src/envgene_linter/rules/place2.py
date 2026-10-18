"""PLACE-2: override only the delta (SHOULD). See docs/algorithms/place2.md."""

from __future__ import annotations

from pathlib import Path

from ..effective import EnvEffective
from ..model import Action, Finding, IssueType, Layer, RepoIndex, Severity
from ..removal_analysis import RemovalAnalysis
from ..rulemeta import RULES
from ..yaml_values import equal


def check(
    index: RepoIndex,
    full: dict[str, EnvEffective],
    lower: dict[str, EnvEffective],
    site: dict[str, EnvEffective],
) -> list[Finding]:
    findings: list[Finding] = []
    seen: set[tuple[Path, tuple]] = set()
    removals = RemovalAnalysis(index)
    for env in index.environments:
        higher = full.get(env.full_name)
        below = lower.get(env.full_name)
        repo_only = site.get(env.full_name)
        if higher is None or below is None or repo_only is None:
            continue
        _collect(findings, seen, env.full_name, higher, below, Layer.ENVIRONMENT, removals)
        _collect(findings, seen, env.full_name, below, repo_only, Layer.CLUSTER, removals)
    return findings


def _collect(
    findings: list[Finding],
    seen: set[tuple[Path, tuple]],
    env_name: str,
    higher: EnvEffective,
    below_map: EnvEffective,
    layer: Layer,
    removals: RemovalAnalysis,
) -> None:
    for scope, mapping in higher.scopes.items():
        for path, leaf in mapping.items():
            if leaf.provenance.layer is not layer:
                continue
            below = below_map.get(scope, path)
            if below is None:
                continue
            comparison = equal(below.value, leaf.value)
            if comparison is False:
                continue
            owner = env_name if layer is Layer.ENVIRONMENT else (leaf.provenance.file.cluster or "repository")
            scope_label = f"{owner} {scope}"
            marker = (leaf.provenance.file.path.resolve(), leaf.provenance.yaml_path)
            if marker in seen:
                continue
            seen.add(marker)
            preservation = removals.preserves(leaf.provenance)
            if preservation is False:
                continue
            review = comparison is None or preservation is None
            meta = RULES["PLACE-2"]
            line, column = leaf.provenance.position
            findings.append(
                Finding(
                    rule="PLACE-2",
                    severity=Severity.INFORMATION if review else Severity.WARNING,
                    path=leaf.provenance.file.path,
                    line=line,
                    column=column,
                    issue_type=IssueType.INFORMATION if review else meta.default_issue_type,
                    action=Action.REVIEW if review else meta.default_action,
                    key=leaf.key,
                    scope=scope_label,
                    message=(
                        "Cannot confirm that removing this parameter preserves all known local consumers."
                        if review else f"Key {leaf.key} at the {layer.value} layer repeats the lower-layer value."
                    ),
                    hint=(
                        "Review the selected sources and merge context before changing this parameter."
                        if review else f"Remove {leaf.key} from this file, or change the value if the override is intentional."
                    ),
                    related=() if review else (
                        f"value {leaf.value!r} already comes from {below.provenance.describe()}",
                    ),
                )
            )
