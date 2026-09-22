"""PLACE-2: override only the delta (SHOULD). See docs/algorithms/place2.md."""

from __future__ import annotations

from ..effective import EnvEffective
from ..model import Finding, Layer, RepoIndex, Severity
from ..rulemeta import RULES


def check(
    index: RepoIndex,
    full: dict[str, EnvEffective],
    lower: dict[str, EnvEffective],
    site: dict[str, EnvEffective],
) -> list[Finding]:
    findings: list[Finding] = []
    seen: set[tuple[str, str]] = set()
    for env in index.environments:
        higher = full.get(env.full_name)
        below = lower.get(env.full_name)
        repo_only = site.get(env.full_name)
        if higher is None or below is None or repo_only is None:
            continue
        _collect(findings, seen, env.full_name, higher, below, Layer.ENVIRONMENT)
        _collect(findings, seen, env.full_name, below, repo_only, Layer.CLUSTER)
    return findings


def _collect(
    findings: list[Finding],
    seen: set[tuple[str, str]],
    env_name: str,
    higher: EnvEffective,
    below_map: EnvEffective,
    layer: Layer,
) -> None:
    for scope, mapping in higher.scopes.items():
        for path, leaf in mapping.items():
            if leaf.provenance.layer is not layer:
                continue
            below = below_map.get(scope, path)
            if below is None or below.value != leaf.value:
                continue
            owner = env_name if layer is Layer.ENVIRONMENT else (leaf.provenance.file.cluster or "repository")
            scope_label = f"{owner} {scope}"
            marker = (str(leaf.provenance.file.path), leaf.key)
            if marker in seen:
                continue
            seen.add(marker)
            meta = RULES["PLACE-2"]
            line, column = leaf.provenance.position
            findings.append(
                Finding(
                    rule="PLACE-2",
                    severity=Severity.WARNING,
                    path=leaf.provenance.file.path,
                    line=line,
                    column=column,
                    issue_type=meta.default_issue_type,
                    action=meta.default_action,
                    key=leaf.key,
                    scope=scope_label,
                    message=(
                        f"Key {leaf.key} at the {layer.value} layer repeats the lower-layer value."
                    ),
                    hint=(
                        f"Remove {leaf.key} from this file, or change the value if the override "
                        f"is intentional."
                    ),
                    related=(f"value {leaf.value!r} already comes from {below.provenance.describe()}",),
                )
            )
