"""Cloud Passport resolve and key catalogs. See docs/algorithms/place3.md."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from .model import EnvModel, PassportFile, RepoIndex

if TYPE_CHECKING:
    from .connections import Connections

TABLE: frozenset[str] = frozenset(
    {
        "CLOUD_API_HOST",
        "CLOUD_API_PORT",
        "CLOUD_PRIVATE_HOST",
        "CLOUD_PUBLIC_HOST",
        "CLOUD_DASHBOARD_URL",
        "CLOUD_DEPLOY_TOKEN",
        "CLOUD_PROTOCOL",
        "PRODUCTION_MODE",
        "API_DBAAS_ADDRESS",
        "DBAAS_AGGREGATOR_ADDRESS",
        "DBAAS_CLUSTER_DBA_CREDENTIALS_USERNAME",
        "DBAAS_CLUSTER_DBA_CREDENTIALS_PASSWORD",
        "DBAAS_AGGREGATOR_USERNAME",
        "DBAAS_AGGREGATOR_PASSWORD",
        "DBAAS_ENABLED",
        "MAAS_INTERNAL_ADDRESS",
        "MAAS_SERVICE_ADDRESS",
        "MAAS_EXTERNAL_ROUTE",
        "MAAS_CREDENTIALS_USERNAME",
        "MAAS_CREDENTIALS_PASSWORD",
        "MAAS_ENABLED",
        "VAULT_ADDR",
        "VAULT_AUTH_ROLE_ID",
        "VAULT_TOKEN",
        "PUBLIC_VAULT_URL",
        "VAULT_ENABLED",
        "CONSUL_URL",
        "CONSUL_PUBLIC_URL",
        "CONSUL_ENABLED",
        "CONSUL_ADMIN_TOKEN",
    }
)
PASSPORT_FOLDERS = ("cloud-passport", "cloud-passports")
AUTO_FOLDER = "cloud-passport"


@dataclass(frozen=True)
class PassportResolution:
    file: PassportFile | None
    note: str | None = None
    candidates: tuple[PassportFile, ...] = ()


@dataclass
class Catalogs:
    env: dict[str, frozenset[str]]
    cluster: dict[str, frozenset[str]]
    repo: frozenset[str]


def flattened_keys(passport: PassportFile) -> set[str]:
    if passport.loaded is None or not isinstance(passport.loaded.doc, dict):
        return set()
    keys: set[str] = set()
    for section, body in passport.loaded.doc.items():
        if section == "version" or not isinstance(body, dict):
            continue
        keys.update(str(key) for key, value in body.items() if not isinstance(value, dict))
    return keys


def _matches_name(path: Path, name: str) -> bool:
    from .discovery import paramset_stem

    return paramset_stem(path) == name


def _search_explicit(index: RepoIndex, env: EnvModel, name: str) -> list[PassportFile]:
    environments_dir = index.root / "environments"
    levels = [
        env.path / "Inventory",
        env.path.parent,
        environments_dir,
    ]
    found: list[PassportFile] = []
    seen: set[Path] = set()
    for level in levels:
        for folder in PASSPORT_FOLDERS:
            root = level / folder
            for item in index.passports:
                if item.path in seen:
                    continue
                try:
                    item.path.relative_to(root)
                except ValueError:
                    continue
                if _matches_name(item.path, name):
                    found.append(item)
                    seen.add(item.path)
    return found


def _rule_candidates(
    index: RepoIndex, matches: list[PassportFile]
) -> tuple[PassportFile, ...]:
    candidates: list[PassportFile] = []
    seen: set[Path] = set()
    for item in matches:
        try:
            logical_relative = item.path.absolute().relative_to(index.root)
            physical = item.path.resolve()
            relative = physical.relative_to(index.root)
        except (OSError, RuntimeError, ValueError):
            continue
        if ".git" in logical_relative.parts or ".git" in relative.parts or physical in seen:
            continue
        seen.add(physical)
        candidates.append(item)
    return tuple(candidates)


def resolve_passport(index: RepoIndex, env: EnvModel) -> PassportResolution:
    if env.cloud_passport:
        matches = _search_explicit(index, env, env.cloud_passport)
        candidates = _rule_candidates(index, matches)
        if len(matches) == 1:
            return PassportResolution(file=matches[0], candidates=candidates)
        return PassportResolution(
            file=None,
            note=(
                f"{env.path / 'Inventory' / 'env_definition.yml'}: "
                f"cloudPassport {env.cloud_passport!r} matched {len(matches)} file(s); skipped"
            ),
            candidates=candidates,
        )
    cluster_dir = env.path.parent
    for stem in (env.cluster, "passport"):
        matches = [
            item
            for item in index.passports
            if item.cluster == env.cluster
            and item.env is None
            and item.path.parent.name == AUTO_FOLDER
            and _matches_name(item.path, stem)
        ]
        candidates = _rule_candidates(index, matches)
        if len(matches) == 1:
            return PassportResolution(file=matches[0], candidates=candidates)
        if len(matches) > 1:
            return PassportResolution(
                file=None,
                note=f"{cluster_dir}: auto passport {stem!r} matched {len(matches)} file(s); skipped",
                candidates=candidates,
            )
    return PassportResolution(file=None)


def build_catalogs(index: RepoIndex, connections: Connections | None = None) -> Catalogs:
    if connections is None:
        from .connections import compute_connections

        connections = compute_connections(index)
    env_cats: dict[str, frozenset[str]] = {}
    for env in index.environments:
        selected = connections.environment_passports.get(env.full_name)
        extra = flattened_keys(selected) if selected else set()
        env_cats[env.full_name] = TABLE | extra
    cluster_cats: dict[str, frozenset[str]] = {}
    for cluster in index.clusters.values():
        union = set(TABLE)
        for env in cluster.environments:
            union |= env_cats.get(env.full_name, TABLE)
        cluster_cats[cluster.name] = frozenset(union)
    repo = frozenset(set(TABLE).union(*cluster_cats.values())) if cluster_cats else TABLE
    return Catalogs(env=env_cats, cluster=cluster_cats, repo=repo)
