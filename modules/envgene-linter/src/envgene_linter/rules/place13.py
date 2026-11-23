"""PLACE-13: a deploy parameter stays where every reached application accepts it."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..connections import Connections
from ..diagnostics import skip_check
from ..effective import EnvEffective
from ..model import (
    Action,
    Category,
    EnvModel,
    Finding,
    IssueType,
    RepoIndex,
    Scope,
    Severity,
)
from ..passport import TABLE
from ..yaml_values import equal
from ..yamlio import YamlReadError, load

RULE = "PLACE-13"
_SD_DIR = Path("Inventory") / "solution-descriptor"


@dataclass(frozen=True)
class AppCatalog:
    exact: frozenset[str]
    open_maps: frozenset[str]
    internal: frozenset[str]
    unresolved: bool


@dataclass(frozen=True)
class DeployedApp:
    name: str
    postfix: str | None


def check(
    index: RepoIndex,
    full: dict[str, EnvEffective],
    connections: Connections,
    catalog_dir: Path | None,
) -> list[Finding]:
    if catalog_dir is None:
        return []
    catalogs = _load_catalogs(index, catalog_dir)
    findings: list[Finding] = []
    for env in index.environments:
        if env.full_name not in full:
            continue
        deployed = _deployed_apps(index, env)
        findings.extend(_environment_findings(index, env, full[env.full_name], connections, catalogs, deployed))
    return sorted(findings, key=lambda item: (item.path.as_posix(), item.line, item.key, item.scope))


def _load_catalogs(index: RepoIndex, catalog_dir: Path) -> dict[str, AppCatalog]:
    catalogs: dict[str, AppCatalog] = {}
    if not catalog_dir.is_dir():
        skip_check(index, RULE, catalog_dir, "Helm parameter catalog directory is missing")
        return catalogs
    for path in sorted(catalog_dir.glob("*.yaml")) + sorted(catalog_dir.glob("*.yml")):
        try:
            loaded = load(path)
        except (OSError, YamlReadError) as exc:
            skip_check(index, RULE, path, f"cannot read Helm parameter catalog: {exc}")
            continue
        document = loaded.doc
        if not isinstance(document, dict):
            continue
        application = document.get("application")
        if not isinstance(application, dict) or not application.get("name"):
            continue
        catalogs[str(application["name"])] = _app_catalog(document)
    return catalogs


def _app_catalog(document: dict) -> AppCatalog:
    exact: set[str] = set()
    open_maps: set[str] = set()
    internal: set[str] = set()
    services = document.get("services")
    if isinstance(services, list):
        for service in services:
            if not isinstance(service, dict):
                continue
            parameters = service.get("parameters")
            if not isinstance(parameters, list):
                continue
            for item in parameters:
                if not isinstance(item, dict) or not item.get("key"):
                    continue
                key = str(item["key"])
                if item.get("internal") is True or item.get("envSpecific") is True:
                    internal.add(key)
                    continue
                exact.add(key)
                opened = item.get("additionalProperties")
                if opened is True or isinstance(opened, dict):
                    open_maps.add(key)
    supported = document.get("supportedParameters")
    if isinstance(supported, list):
        exact.update(str(key) for key in supported if str(key) not in internal)
    unresolved = document.get("unresolvedServices")
    return AppCatalog(
        exact=frozenset(exact),
        open_maps=frozenset(open_maps),
        internal=frozenset(internal),
        unresolved=isinstance(unresolved, list) and bool(unresolved),
    )


def _deployed_apps(index: RepoIndex, env: EnvModel) -> list[DeployedApp] | None:
    directory = env.path / _SD_DIR
    if not directory.is_dir():
        skip_check(index, RULE, env.path / "Inventory" / "env_definition.yml", "solution descriptor is missing")
        return None
    deployed: list[DeployedApp] = []
    paths = sorted(directory.glob("*.yaml")) + sorted(directory.glob("*.yml"))
    if not paths:
        skip_check(index, RULE, directory, "solution descriptor is missing")
        return None
    for path in paths:
        try:
            loaded = load(path)
        except (OSError, YamlReadError) as exc:
            skip_check(index, RULE, path, f"cannot read solution descriptor: {exc}")
            return None
        document = loaded.doc
        applications = document.get("applications") if isinstance(document, dict) else None
        if not isinstance(applications, list):
            skip_check(index, RULE, path, "solution descriptor has no applications list")
            return None
        for item in applications:
            if not isinstance(item, dict) or not isinstance(item.get("version"), str) or ":" not in item["version"]:
                skip_check(index, RULE, path, "solution descriptor application version is not App:Ver")
                return None
            name = item["version"].split(":", 1)[0].strip()
            postfix = item.get("deployPostfix")
            deployed.append(DeployedApp(name, str(postfix) if postfix is not None else None))
    return deployed


def _environment_findings(
    index: RepoIndex,
    env: EnvModel,
    effective: EnvEffective,
    connections: Connections,
    catalogs: dict[str, AppCatalog],
    deployed: list[DeployedApp] | None,
) -> list[Finding]:
    findings: list[Finding] = []
    for scope, leaves in effective.scopes.items():
        if scope.category is not Category.DEPLOY:
            continue
        level = _level(scope)
        if level is None:
            continue
        for leaf in leaves.values():
            if not leaf.path or str(leaf.path[0]) in TABLE:
                continue
            affected = _affected(scope, deployed)
            if affected is None:
                continue
            finding = _judge(
                env, effective, scope, level, leaf, affected, deployed or [], catalogs, connections
            )
            if finding is not None:
                findings.append(finding)
    return findings


def _level(scope: Scope) -> str | None:
    if scope.target == "cloud" and scope.application is None:
        return "cloud"
    if scope.target == "cloud":
        return "app@cloud"
    if scope.application is None:
        return "ns"
    return "app@ns"


def _rank(scope: Scope) -> int | None:
    level = _level(scope)
    return {"cloud": 0, "app@cloud": 1, "ns": 2, "app@ns": 3}.get(level or "")


def _affected(scope: Scope, deployed: list[DeployedApp] | None) -> list[str] | None:
    if scope.application:
        return [scope.application]
    if deployed is None:
        return None
    if scope.target == "cloud":
        return sorted({app.name for app in deployed})
    return sorted({app.name for app in deployed if app.postfix == scope.target})


def _judge(
    env: EnvModel,
    effective: EnvEffective,
    scope: Scope,
    level: str,
    leaf,
    affected: list[str],
    deployed: list[DeployedApp],
    catalogs: dict[str, AppCatalog],
    connections: Connections,
) -> Finding | None:
    if not affected:
        return None
    key = leaf.key
    verdicts = [_verdict(catalogs.get(name), key) for name in affected]
    if any(item == "unresolved" for item in verdicts):
        names = [name for name, item in zip(affected, verdicts) if item == "unresolved"]
        return _finding(
            env, leaf, Action.REVIEW,
            f"{key} cannot be checked because {', '.join(names)} has a service without a values schema.",
            "Add the missing values schema to the Helm parameter catalog and rerun PLACE-13.",
        )
    if any(item == "skip" for item in verdicts):
        return None
    consumers = [name for name, item in zip(affected, verdicts) if item == "yes"]
    if len(consumers) == len(affected):
        return None
    shared = _shared(connections, leaf.provenance.file.path)
    if not consumers:
        if shared:
            return _shared_finding(env, leaf, key)
        return _finding(
            env, leaf, Action.REVIEW,
            f"{key} is not accepted by any application reached from {level}.",
            f"Review whether to delete {key}. PLACE-13 does not delete parameters.",
        )
    if shared:
        return _shared_finding(env, leaf, key)
    if _priority_conflict(effective, scope, leaf):
        return _finding(
            env, leaf, Action.REVIEW,
            f"{key} also has a different value closer to the application than {level}.",
            "Review the move. Putting the wider value on the application would hide the nearer value.",
        )
    if len(consumers) != 1:
        names = ", ".join(consumers)
        return _finding(
            env, leaf, Action.FIX,
            f"{key} is accepted only by {names} at {level}.",
            f"Move {key} to each accepting application at app@ns and remove it from {level}.",
        )
    app = consumers[0]
    postfixes = _postfixes(deployed, app)
    where = ", ".join(postfixes) if postfixes else "its namespace"
    return _finding(
        env, leaf, Action.FIX,
        f"{key} is accepted only by {app} at {level}.",
        f"Move {key} to *-{app}-deploy at app@ns ({where}) and remove it from {level}.",
    )


def _verdict(catalog: AppCatalog | None, key: str) -> str:
    if catalog is None or catalog.unresolved:
        return "unresolved"
    if key in catalog.internal or any(key == prefix or key.startswith(prefix + ".") for prefix in catalog.internal):
        return "skip"
    if key in catalog.exact:
        return "yes"
    if any(key == prefix or key.startswith(prefix + ".") for prefix in catalog.open_maps):
        return "yes"
    return "no"


def _shared(connections: Connections, path: Path) -> bool:
    uses = connections.parameter_uses.get(path.resolve(), ())
    environments = {use.environment for use in uses if use.category is Category.DEPLOY}
    return len(environments) > 1


def _priority_conflict(effective: EnvEffective, scope: Scope, leaf) -> bool:
    current = _rank(scope)
    if current is None:
        return False
    for other_scope, leaves in effective.scopes.items():
        other = _rank(other_scope)
        if other is None or not current < other < 3:
            continue
        nearer = leaves.get(leaf.path)
        if nearer is not None and equal(nearer.value, leaf.value) is not True:
            return True
    return False


def _postfixes(deployed: list[DeployedApp], app: str) -> list[str]:
    return sorted({item.postfix for item in deployed if item.name == app and item.postfix})


def _shared_finding(env: EnvModel, leaf, key: str) -> Finding:
    return _finding(
        env, leaf, Action.REVIEW,
        f"{key} is in a ParameterSet used by more than one environment.",
        f"Review which application should own {key}. PLACE-13 does not split a shared ParameterSet.",
    )


def _finding(env: EnvModel, leaf, action: Action, message: str, hint: str) -> Finding:
    line, column = leaf.provenance.position
    return Finding(
        rule=RULE,
        severity=Severity.WARNING,
        issue_type=IssueType.WARNING,
        action=action,
        path=leaf.provenance.file.path,
        line=line,
        column=column,
        key=leaf.key,
        scope=env.full_name,
        message=message,
        hint=hint,
    )
