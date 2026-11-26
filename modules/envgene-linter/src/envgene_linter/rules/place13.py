"""PLACE-13: a deploy parameter stays where every reached application accepts it."""

from __future__ import annotations

import json
from collections.abc import Sequence
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
    unresolved: tuple[str, ...]


@dataclass(frozen=True)
class DeployedApp:
    name: str
    postfix: str | None


@dataclass
class _SharedView:
    env_name: str
    scope: Scope
    leaf: object
    key: str
    level: str
    consumers: tuple[str, ...]
    affected: tuple[str, ...]
    deployed: tuple[DeployedApp, ...]


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
    shared: list[_SharedView] = []
    for env in index.environments:
        if env.full_name not in full:
            continue
        deployed = _deployed_apps(index, env)
        local, views = _environment_findings(
            index, env, full[env.full_name], connections, catalogs, deployed
        )
        findings.extend(local)
        shared.extend(views)
    findings.extend(_combine_shared(shared, connections))
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
    return AppCatalog(
        exact=frozenset(exact),
        open_maps=frozenset(open_maps),
        internal=frozenset(internal),
        unresolved=_unresolved_services(document.get("unresolvedServices")),
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
) -> tuple[list[Finding], list[_SharedView]]:
    findings: list[Finding] = []
    shared: list[_SharedView] = []
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
            result = _judge(
                env, effective, scope, level, leaf, affected, deployed or [], catalogs, connections
            )
            if isinstance(result, _SharedView):
                shared.append(result)
            elif result is not None:
                findings.append(result)
    return findings, shared


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
) -> Finding | _SharedView | None:
    if not affected:
        return None
    key = leaf.key
    verdicts = [_verdict(catalogs.get(name), key) for name in affected]
    if any(item == "unresolved" for item in verdicts):
        names = [name for name, item in zip(affected, verdicts) if item == "unresolved"]
        return _unresolved_finding(env, scope, leaf, names, catalogs)
    if any(item == "skip" for item in verdicts):
        return None
    consumers = [name for name, item in zip(affected, verdicts) if item == "yes"]
    if len(consumers) == len(affected):
        return None
    shared = _shared(connections, leaf.provenance.file.path)
    if not consumers:
        if shared:
            return _shared_view(env, scope, leaf, key, level, consumers, affected, deployed)
        return _delete_finding(env, scope, leaf, affected)
    if shared:
        return _shared_view(env, scope, leaf, key, level, consumers, affected, deployed)
    conflicts = _priority_conflicts(effective, scope, leaf)
    if conflicts:
        return _priority_finding(env, scope, leaf, consumers, deployed, conflicts)
    return _move_finding(env, scope, leaf, consumers, affected, deployed)


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


def _sharing_environments(connections: Connections, path: Path) -> list[str]:
    uses = connections.parameter_uses.get(path.resolve(), ())
    return sorted({use.environment for use in uses if use.category is Category.DEPLOY})


def _shared(connections: Connections, path: Path) -> bool:
    return len(_sharing_environments(connections, path)) > 1


def _em(value: str) -> str:
    return f"**{value}**"


def _app(name: str) -> str:
    return f"{_em(name)} (application)"


def _name_hint(apps: Sequence[str]) -> str:
    if len(apps) == 1:
        named = f"The ParameterSet name is this project's prefix plus {_em(f'-{apps[0]}-deploy')}."
    else:
        endings = "\n".join(f"{_app(app)}: prefix plus {_em(f'-{app}-deploy')}" for app in apps)
        named = (
            "Each ParameterSet name is this project's prefix plus the application name and -deploy:\n"
            f"{endings}"
        )
    return (
        f"{named}\n"
        "The linter does not choose the prefix.\n"
        "If a ParameterSet for that application already ends with -deploy, add the key to that file."
    )


def _source_path(path: Path) -> str:
    parts = path.parts
    if "environments" in parts:
        return "/".join(parts[parts.index("environments"):])
    return path.name


def _priority_conflicts(effective: EnvEffective, scope: Scope, leaf) -> list[tuple[Scope, object]]:
    current = _rank(scope)
    if current is None:
        return []
    found: list[tuple[Scope, object]] = []
    for other_scope, leaves in effective.scopes.items():
        other = _rank(other_scope)
        if other is None or not current < other < 3:
            continue
        nearer = leaves.get(leaf.path)
        if nearer is not None and equal(nearer.value, leaf.value) is not True:
            found.append((other_scope, nearer))
    return sorted(found, key=lambda item: (_rank(item[0]) or 0, item[0].target, item[0].application or ""))


def _place(scope: Scope) -> str:
    level = _level(scope)
    if level == "cloud":
        return "the whole cloud"
    if level == "ns":
        return f"the namespace {_em(scope.target)}"
    if level == "app@cloud":
        return f"the application {scope.application} at cloud level"
    return f"the application {scope.application} in the namespace {_em(scope.target)}"


def _shown(value: object) -> str:
    if isinstance(value, str) and len(value) <= 80 and "\n" not in value:
        return _em(value)
    if isinstance(value, (int, float, bool)) or value is None:
        return _em(json.dumps(value))
    return "a value too large to quote here"


def _value_row(scope: Scope, leaf) -> str:
    place = _place(scope)
    return (
        f"{place[:1].upper()}{place[1:]}:\n"
        f"{_em(_source_path(leaf.provenance.file.path))}\n"
        f"Value: {_shown(leaf.value)}"
    )


def _unresolved_services(raw: object) -> tuple[str, ...]:
    if not isinstance(raw, list) or not raw:
        return ()
    names: list[str] = []
    for item in raw:
        if isinstance(item, dict) and item.get("serviceName"):
            names.append(str(item["serviceName"]))
        elif isinstance(item, str) and item:
            names.append(item)
    return tuple(names) or ("a service",)


def _unresolved_finding(
    env: EnvModel, scope: Scope, leaf, names: list[str], catalogs: dict[str, AppCatalog]
) -> Finding:
    marked = _em(leaf.key)
    reasons = "\n\n".join(_unresolved_reason(name, catalogs.get(name)) for name in names)
    where = _key_place(scope, marked, env.full_name)
    issue = (
        f"{where}\n"
        "\n"
        f"{_em(_source_path(leaf.provenance.file.path))}\n"
        f"Value: {_shown(leaf.value)}\n"
        "\n"
        f"{reasons}"
    )
    services = [
        service
        for name in names
        for service in (catalogs[name].unresolved if name in catalogs else ())
    ]
    if services:
        hint = (
            f"values.schema.json lists the parameters a service accepts.\n"
            f"Without it, this check cannot tell whether to keep {marked} or remove it.\n"
            "\n"
            f"Add values.schema.json for {_service_list(services)} to the Helm chart, "
            "rebuild the Helm parameter catalog, and run the check again."
        )
    else:
        hint = (
            f"This check cannot tell whether to keep {marked} or remove it.\n"
            "\n"
            "Add the missing application to the Helm parameter catalog and run the check again."
        )
    return _finding(env, leaf, Action.REVIEW, issue, hint)


def _key_place(scope: Scope, marked: str, env_name: str) -> str:
    if scope.application and scope.target == "cloud":
        return f"{marked} is set for {_app(scope.application)} at cloud level in {_em(env_name)}."
    if scope.application:
        return (
            f"{marked} is set for {_app(scope.application)} "
            f"in the namespace {_em(scope.target)} of {_em(env_name)}."
        )
    return f"{marked} is set for {_place(scope)} in {_em(env_name)}."


def _service(name: str) -> str:
    return f"{_em(name)} (service)"


def _service_list(names: Sequence[str]) -> str:
    labeled = [_service(name) for name in names]
    if len(labeled) == 1:
        return labeled[0]
    if len(labeled) == 2:
        return f"{labeled[0]} and {labeled[1]}"
    return ", ".join(labeled[:-1]) + ", and " + labeled[-1]


def _unresolved_reason(name: str, catalog: AppCatalog | None) -> str:
    if catalog is None:
        return f"{_app(name)} is not in the Helm parameter catalog."
    services = catalog.unresolved or ("a service",)
    if len(services) == 1:
        return (
            f"The Helm chart for {_app(name)} includes {_service(services[0])}.\n"
            "That service has no values.schema.json.\n"
            "The catalog cannot tell which parameters it accepts."
        )
    return (
        f"The Helm chart for {_app(name)} includes {_service_list(services)}.\n"
        "Those services have no values.schema.json.\n"
        "The catalog cannot tell which parameters they accept."
    )


def _who_receives(scope: Scope, marked: str) -> str:
    if _level(scope) == "ns":
        return f"Every application in the namespace {_em(scope.target)} receives {marked}."
    return f"Every application in this environment receives {marked}."


def _names(apps: Sequence[str]) -> str:
    labeled = [_app(name) for name in apps]
    if len(labeled) == 1:
        return labeled[0]
    if len(labeled) == 2:
        return f"{labeled[0]} and {labeled[1]}"
    return ", ".join(labeled[:-1]) + ", and " + labeled[-1]


def _delete_finding(env: EnvModel, scope: Scope, leaf, affected: list[str]) -> Finding:
    marked = _em(leaf.key)
    lines = "\n".join(f"{_app(name)} does not accept {marked}." for name in affected)
    issue = (
        f"{marked} is set for {_place(scope)} in {_em(env.full_name)}.\n"
        "\n"
        f"{_em(_source_path(leaf.provenance.file.path))}\n"
        f"Value: {_shown(leaf.value)}\n"
        "\n"
        f"{_who_receives(scope, marked)}\n"
        "None of them accept it:\n"
        f"{lines}"
    )
    hint = (
        f"No application that receives {marked} accepts it.\n"
        f"It can be removed from {_place(scope)}.\n"
        "The linter does not delete parameters.\n"
        "\n"
        f"Decide whether {marked} should stay before you change the file."
    )
    return _finding(env, leaf, Action.REVIEW, issue, hint)


def _move_finding(env: EnvModel, scope: Scope, leaf, consumers: list[str], affected: list[str], deployed) -> Finding:
    marked = _em(leaf.key)
    accepted = set(consumers)
    verdicts = "\n".join(
        f"{_app(name)} accepts {marked}." if name in accepted else f"{_app(name)} does not accept {marked}."
        for name in affected
    )
    issue = (
        f"{marked} is set for {_place(scope)} in {_em(env.full_name)}.\n"
        "\n"
        f"{_em(_source_path(leaf.provenance.file.path))}\n"
        f"Value: {_shown(leaf.value)}\n"
        "\n"
        f"{_who_receives(scope, marked)}\n"
        f"{verdicts}"
    )
    rejected = [name for name in affected if name not in accepted]
    if len(consumers) == 1:
        app = consumers[0]
        opening = (
            f"Put {marked} on a ParameterSet for {_app(app)}, "
            f"in the namespace {_em(_namespace(deployed, app))}.\n"
            f"{_name_hint(consumers)}"
        )
    else:
        lines = "\n".join(
            f"{_app(app)}, in the namespace {_em(_namespace(deployed, app))}."
            for app in consumers
        )
        opening = (
            f"Put {marked} on a separate ParameterSet for each application that accepts it:\n"
            "\n"
            f"{lines}\n"
            "\n"
            f"{_name_hint(consumers)}"
        )
    if not rejected:
        kept = f"{_names(consumers)} still {'receives' if len(consumers) == 1 else 'receive'} the value."
    else:
        verb = "receives" if len(rejected) == 1 else "receive"
        kept = (
            f"{_names(consumers)} still {'receives' if len(consumers) == 1 else 'receive'} the value.\n"
            f"{_names(rejected)} no longer {verb} it."
        )
    hint = (
        f"{opening}\n"
        "\n"
        f"Then remove {marked} from {_place(scope)}.\n"
        f"{kept}"
    )
    return _finding(env, leaf, Action.FIX, issue, hint)


def _priority_finding(env: EnvModel, scope: Scope, leaf, consumers: list[str], deployed, conflicts) -> Finding:
    marked = _em(leaf.key)
    rows = "\n\n".join([_value_row(scope, leaf), *(_value_row(other, nearer) for other, nearer in conflicts)])
    issue = (
        f"{marked} is set in more than one place in {_em(env.full_name)}, and the values are different.\n"
        "\n"
        f"{rows}"
    )
    specific = conflicts[-1][0]
    if len(consumers) == 1:
        app = consumers[0]
        move = (
            f"Only {_app(app)} accepts {marked}.\n"
            f"The value from {_place(scope)} would normally move to a ParameterSet for that application, "
            f"in the namespace {_em(_namespace(deployed, app))}.\n"
            f"{_name_hint([app])}"
        )
    else:
        names = "\n".join(
            f"{_app(app)} in the namespace {_em(_namespace(deployed, app))}" for app in consumers
        )
        move = (
            f"These applications accept {marked}:\n{names}\n"
            f"The value from {_place(scope)} would normally move onto a ParameterSet for each of them."
        )
    hint = (
        f"{move}\n"
        "\n"
        f"Leave that value where it is.\n"
        f"The application receives the value from {_place(specific)} today, "
        f"because that place is more specific than {_place(scope)}.\n"
        f"Moving the value from {_place(scope)} onto the application would replace it.\n"
        "\n"
        f"Decide which value the application should receive before you change {marked}."
    )
    return _finding(env, leaf, Action.REVIEW, issue, hint)


def _postfixes(deployed: Sequence[DeployedApp], app: str) -> list[str]:
    return sorted({item.postfix for item in deployed if item.name == app and item.postfix})


def _shared_view(
    env: EnvModel,
    scope: Scope,
    leaf,
    key: str,
    level: str,
    consumers: list[str],
    affected: list[str],
    deployed: list[DeployedApp],
) -> _SharedView:
    return _SharedView(
        env.full_name, scope, leaf, key, level, tuple(consumers), tuple(affected), tuple(deployed)
    )


def _combine_shared(views: list[_SharedView], connections: Connections) -> list[Finding]:
    groups: dict[tuple, list[_SharedView]] = {}
    for view in views:
        line, column = view.leaf.provenance.position
        group_key = (view.leaf.provenance.file.path.resolve(), line, column, view.key, view.level)
        groups.setdefault(group_key, []).append(view)
    return [_one_shared(grouped, connections) for grouped in groups.values()]


def _one_shared(views: list[_SharedView], connections: Connections) -> Finding:
    unique: list[_SharedView] = []
    seen: set[str] = set()
    for view in sorted(views, key=lambda item: item.env_name):
        if view.env_name in seen:
            continue
        seen.add(view.env_name)
        unique.append(view)
    first = unique[0]
    marked_key = _em(first.key)
    users = _sharing_environments(connections, first.leaf.provenance.file.path)
    listed = "\n".join(_em(name) for name in users)
    same = all(_story(view) == _story(first) for view in unique)
    if same:
        verdicts = _verdict_lines(first.affected, first.consumers, marked_key)
        covered = {view.env_name for view in unique}
        if covered == set(users):
            lead = f"In each of these environments:\n{verdicts}"
            audience = "these environments"
        else:
            named = "\n".join(_em(view.env_name) for view in unique)
            lead = f"In:\n{named}\n\n{verdicts}"
            audience = " and ".join(view.env_name for view in unique)
        issue = (
            f"{marked_key} is in {_em(_source_path(first.leaf.provenance.file.path))}.\n"
            "\n"
            "Environments that use this ParameterSet:\n"
            f"{listed}\n"
            "\n"
            f"Level: {_em(first.level)}\n"
            "\n"
            f"{lead}"
        )
        advice = _shared_advice(first, marked_key, listed, audience)
    else:
        blocks = "\n\n".join(
            f"{_em(view.env_name)}:\n{_verdict_lines(view.affected, view.consumers, marked_key)}"
            for view in unique
        )
        issue = (
            f"{marked_key} is in {_em(_source_path(first.leaf.provenance.file.path))}.\n"
            "\n"
            "Environments that use this ParameterSet:\n"
            f"{listed}\n"
            "\n"
            f"Level: {_em(first.level)}\n"
            "\n"
            f"{blocks}"
        )
        advice = _split_advice(unique, marked_key, listed)
    return _finding(
        None, first.leaf, Action.REVIEW, issue, advice,
        scope=", ".join(view.env_name for view in unique),
    )


def _story(view: _SharedView) -> tuple:
    return (
        view.level,
        view.scope.target,
        view.consumers,
        view.affected,
        tuple(_namespace(view.deployed, app) for app in view.consumers),
    )


def _verdict_lines(affected: Sequence[str], consumers: Sequence[str], marked_key: str) -> str:
    accepted = set(consumers)
    return "\n".join(
        f"{_app(name)} accepts {marked_key}." if name in accepted else f"{_app(name)} does not accept {marked_key}."
        for name in affected
    )


def _shared_advice(view: _SharedView, marked_key: str, listed: str, audience: str) -> str:
    shared_note = (
        "These environments use this same file:\n"
        f"{listed}\n"
        "\n"
        f"Removing {marked_key} here removes it in every one of them.\n"
        "The linter does not create a separate copy of the file for each environment."
    )
    consumers = view.consumers
    if not consumers:
        move = (
            f"{_reach(marked_key, view.level, view.scope, audience)}\n"
            f"None of those applications accept {marked_key}.\n"
            "\n"
            "In a file used by one environment, this key would be a candidate for deletion.\n"
            "The linter does not delete parameters."
        )
        closing = f"Decide whether {marked_key} should stay in this file."
    elif len(consumers) == 1:
        app = consumers[0]
        move = (
            f"{_reach(marked_key, view.level, view.scope, audience)}\n"
            f"Only {_app(app)} accepts {marked_key}.\n"
            "\n"
            f"Keep {marked_key} on a ParameterSet for that application, "
            f"in the namespace {_em(_namespace(view.deployed, app))}.\n"
            f"{_name_hint([app])}"
        )
        closing = f"Decide which application should keep {marked_key} before you change the file."
    else:
        destinations = "\n".join(
            f"{_app(app)} in the namespace {_em(_namespace(view.deployed, app))}"
            for app in consumers
        )
        move = (
            f"{_reach(marked_key, view.level, view.scope, audience)}\n"
            "These applications accept it:\n"
            f"{destinations}\n"
            "\n"
            "Each of them should have the key on its own ParameterSet.\n"
            f"{_name_hint(consumers)}"
        )
        closing = f"Decide where each accepting application should keep {marked_key} before you change the file."
    return f"{move}\n\n{shared_note}\n\n{closing}"


def _split_advice(views: list[_SharedView], marked_key: str, listed: str) -> str:
    blocks = "\n\n".join(_keep_block(view, marked_key) for view in views)
    return (
        f"These environments do not agree on where {marked_key} should go.\n"
        "\n"
        f"{blocks}\n"
        "\n"
        "These environments use this same file:\n"
        f"{listed}\n"
        "\n"
        f"One edit of this file changes every one of them.\n"
        "The linter does not create a separate copy of the file for each environment.\n"
        "\n"
        f"Decide where {marked_key} should go before you change the file."
    )


def _keep_block(view: _SharedView, marked_key: str) -> str:
    if not view.consumers:
        return f"In {_em(view.env_name)}, no reached application accepts {marked_key}."
    if len(view.consumers) == 1:
        app = view.consumers[0]
        return (
            f"In {_em(view.env_name)}, keep {marked_key} for {_app(app)}, "
            f"in the namespace {_em(_namespace(view.deployed, app))}.\n"
            f"{_name_hint([app])}"
        )
    lines = "\n".join(
        f"{_app(app)} in the namespace {_em(_namespace(view.deployed, app))}"
        for app in view.consumers
    )
    return f"In {_em(view.env_name)}, these applications accept {marked_key}:\n{lines}"


def _namespace(deployed: Sequence[DeployedApp], app: str) -> str:
    postfixes = _postfixes(deployed, app)
    return ", ".join(postfixes) if postfixes else "where that application is deployed"


def _reach(key: str, level: str, scope: Scope, audience: str) -> str:
    if audience != "these environments":
        audience = _em(audience)
    if level == "cloud":
        return f"{key} is set for the whole cloud, so every application in {audience} receives it."
    if level == "ns":
        return (
            f"{key} is set for the namespace {_em(scope.target)}, "
            "so every application in that namespace receives it."
        )
    if level == "app@cloud":
        return f"{key} is set for one application at cloud level in {audience}."
    return f"{key} is set for one application in the namespace {_em(scope.target)}."


def _finding(
    env: EnvModel | None, leaf, action: Action, message: str, hint: str, scope: str | None = None
) -> Finding:
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
        scope=scope if scope is not None else env.full_name,
        message=message,
        hint=hint,
    )
