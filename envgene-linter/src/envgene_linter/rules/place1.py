"""PLACE-1: highest correct layer (SHOULD). See docs/algorithms/place1.md."""

from __future__ import annotations

from collections import defaultdict

from ..effective import EffectiveLeaf, EnvEffective
from ..model import ClusterModel, Finding, Layer, Location, RepoIndex, Scope, Severity
from ..passport import Catalogs
from ..rulemeta import RULES

MIN_AGREEMENT = 2
Contribution = dict[Scope, dict[tuple, EffectiveLeaf]]


def _locations_from_owners(owners: list[tuple[str, EffectiveLeaf]]) -> tuple[Location, ...]:
    seen: set[tuple[str, int, int]] = set()
    out: list[Location] = []
    for _, owned in owners:
        line, column = owned.provenance.position
        path = owned.provenance.file.path
        marker = (str(path), line, column)
        if marker in seen:
            continue
        seen.add(marker)
        out.append(Location(path, line, column))
    return tuple(out)


def check(
    index: RepoIndex,
    full: dict[str, EnvEffective],
    lower: dict[str, EnvEffective],
    site: dict[str, EnvEffective],
    catalogs: Catalogs | None = None,
) -> list[Finding]:
    return [
        *_hoist_to_cluster(index, full, lower, catalogs),
        *_hoist_to_repository(index, lower, site, catalogs),
    ]


def _hoist_to_cluster(
    index: RepoIndex,
    full: dict[str, EnvEffective],
    lower: dict[str, EnvEffective],
    catalogs: Catalogs | None = None,
) -> list[Finding]:
    findings: list[Finding] = []
    for cluster in index.clusters.values():
        groups: list[tuple[str, Contribution]] = []
        for env in sorted(cluster.environments, key=lambda item: item.name):
            higher = full.get(env.full_name)
            below = lower.get(env.full_name)
            if higher is None or below is None:
                continue
            skip_keys = catalogs.env.get(env.full_name, frozenset()) if catalogs else frozenset()
            groups.append((env.full_name, _authored_at(higher, below, Layer.ENVIRONMENT, skip_keys)))
        meta = RULES["PLACE-1"]
        for scope, leaf, owners in _shared_across(groups, MIN_AGREEMENT):
            line, column = leaf.provenance.position
            findings.append(
                Finding(
                    rule="PLACE-1",
                    severity=Severity.WARNING,
                    path=leaf.provenance.file.path,
                    line=line,
                    column=column,
                    issue_type=meta.default_issue_type,
                    action=meta.default_action,
                    key=leaf.key,
                    scope=f"{cluster.name} {scope}",
                    message=(
                        f"Key {leaf.key} has the same value in {len(owners)} environments "
                        f"of cluster {cluster.name}."
                    ),
                    hint=(
                        f"Move {leaf.key} to environments/{cluster.name}/parameters/ "
                        f"and remove the environment copies."
                    ),
                    related=tuple(f"{name}: {owned.provenance.describe()}" for name, owned in owners),
                    locations=_locations_from_owners(owners),
                )
            )
    return findings


def _hoist_to_repository(
    index: RepoIndex,
    lower: dict[str, EnvEffective],
    site: dict[str, EnvEffective],
    catalogs: Catalogs | None = None,
) -> list[Finding]:
    groups: list[tuple[str, Contribution]] = []
    for cluster in index.clusters.values():
        if not cluster.environments:
            continue
        groups.append((cluster.name, _cluster_contribution(cluster, lower, site, catalogs)))
    findings: list[Finding] = []
    meta = RULES["PLACE-1"]
    for scope, leaf, owners in _shared_across(groups, MIN_AGREEMENT):
        line, column = leaf.provenance.position
        findings.append(
            Finding(
                rule="PLACE-1",
                severity=Severity.WARNING,
                path=leaf.provenance.file.path,
                line=line,
                column=column,
                issue_type=meta.default_issue_type,
                action=meta.default_action,
                key=leaf.key,
                scope=f"repository {scope}",
                message=f"Key {leaf.key} has the same value in {len(owners)} clusters.",
                hint=(
                    f"Move {leaf.key} to a repository paramset and remove the cluster copies."
                ),
                related=tuple(f"{name}: {owned.provenance.describe()}" for name, owned in owners),
                locations=_locations_from_owners(owners),
            )
        )
    return findings


def _authored_at(
    higher: EnvEffective,
    below_map: EnvEffective,
    layer: Layer,
    skip_keys: frozenset[str] = frozenset(),
) -> Contribution:
    contribution: Contribution = defaultdict(dict)
    for scope, mapping in higher.scopes.items():
        for path, leaf in mapping.items():
            if leaf.provenance.layer is not layer:
                continue
            if skip_keys and (str(leaf.path[0]) if leaf.path else leaf.key) in skip_keys:
                continue
            below = below_map.get(scope, path)
            if below is not None and below.value == leaf.value:
                continue
            contribution[scope][path] = leaf
    return dict(contribution)


def _cluster_contribution(
    cluster: ClusterModel,
    lower: dict[str, EnvEffective],
    site: dict[str, EnvEffective],
    catalogs: Catalogs | None = None,
) -> Contribution:
    skip_keys = catalogs.cluster.get(cluster.name, frozenset()) if catalogs else frozenset()
    merged: Contribution = defaultdict(dict)
    conflicting: set[tuple[Scope, tuple]] = set()
    for env in sorted(cluster.environments, key=lambda item: item.name):
        below = lower.get(env.full_name)
        repo_only = site.get(env.full_name)
        if below is None or repo_only is None:
            continue
        for scope, mapping in _authored_at(below, repo_only, Layer.CLUSTER, skip_keys).items():
            for path, leaf in mapping.items():
                existing = merged[scope].get(path)
                if existing is not None and existing.value != leaf.value:
                    conflicting.add((scope, path))
                merged[scope].setdefault(path, leaf)
    for scope, path in conflicting:
        merged[scope].pop(path, None)
    return {scope: mapping for scope, mapping in merged.items() if mapping}


def _shared_across(
    groups: list[tuple[str, Contribution]], minimum: int
) -> list[tuple[Scope, EffectiveLeaf, list[tuple[str, EffectiveLeaf]]]]:
    by_scope: dict[Scope, list[tuple[str, dict[tuple, EffectiveLeaf]]]] = defaultdict(list)
    for name, contribution in groups:
        for scope, mapping in contribution.items():
            by_scope[scope].append((name, mapping))
    shared: list[tuple[Scope, EffectiveLeaf, list[tuple[str, EffectiveLeaf]]]] = []
    for scope in sorted(by_scope, key=str):
        participants = by_scope[scope]
        if len(participants) < minimum:
            continue
        common = set(participants[0][1])
        for _, mapping in participants[1:]:
            common &= set(mapping)
        for path in sorted(common):
            owners = [(name, mapping[path]) for name, mapping in participants]
            first = owners[0][1].value
            if any(owned.value != first for _, owned in owners[1:]):
                continue
            shared.append((scope, owners[0][1], owners))
    return shared
