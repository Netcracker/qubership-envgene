"""PLACE-3: place by the system tier (SHOULD). See docs/algorithms/place3.md."""

from __future__ import annotations

from ..connections import Connections, compute_connections
from ..effective import EnvEffective
from ..model import Finding, PassportFile, RepoIndex, Severity
from ..passport import Catalogs
from ..rulemeta import RULES


def check(
    index: RepoIndex,
    full: dict[str, EnvEffective],
    lower: dict[str, EnvEffective],
    site: dict[str, EnvEffective],
    catalogs: Catalogs,
    connections: Connections | None = None,
) -> list[Finding]:
    del full, lower, site, catalogs
    return _misplaced_files(index, connections or compute_connections(index))


def _file_hint(index: RepoIndex, item: PassportFile) -> str:
    if item.cluster:
        return f"Move it to environments/{item.cluster}/cloud-passport/"
    if len(index.clusters) == 1:
        name = next(iter(index.clusters))
        return f"Move it to environments/{name}/cloud-passport/"
    return "Move it to a cluster's cloud-passport/"


def _misplaced_files(index: RepoIndex, connections: Connections) -> list[Finding]:
    findings: list[Finding] = []
    for item in index.passports:
        if item.path.resolve() not in connections.passports or item.on_cluster:
            continue
        meta = RULES["PLACE-3"]
        findings.append(
            Finding(
                rule="PLACE-3",
                severity=Severity.WARNING,
                path=item.path,
                line=1,
                column=1,
                issue_type=meta.default_issue_type,
                action=meta.default_action,
                key=item.stem,
                scope=item.cluster or "repository",
                message=f"Passport {item.stem} is not at the cluster layer.",
                hint=_file_hint(index, item),
            )
        )
    return findings
