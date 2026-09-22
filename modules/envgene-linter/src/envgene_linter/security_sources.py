"""Select connected inputs whose secret protection SEC-5 can inspect."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .connections import Connections
from .model import EnvModel, RepoIndex
from .parameter_objects import parameter_object_paths
from .yamlio import YamlReadError, load


@dataclass(frozen=True)
class SecuritySource:
    path: Path
    kind: str
    environment: str


@dataclass(frozen=True)
class SecurityBag:
    path: Path
    prefix: tuple
    environment: str
    catalog: Path | None
    fields: tuple[str, ...] | None = None


@dataclass(frozen=True)
class SecurityIssue:
    path: Path
    prefix: tuple = ()


@dataclass
class SecurityInputs:
    sources: list[SecuritySource] = field(default_factory=list)
    bags: list[SecurityBag] = field(default_factory=list)
    issues: list[SecurityIssue] = field(default_factory=list)


_UNSAFE = object()
_PARAMETER_SECTIONS = (
    "deployParameters",
    "e2eParameters",
    "technicalConfigurationParameters",
)


def _present(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def _safe_file(index: RepoIndex, path: Path) -> Path | object | None:
    if not _present(path):
        return None
    try:
        logical = path.absolute().relative_to(index.root)
        physical = path.resolve(strict=True)
        relative = physical.relative_to(index.root)
    except (OSError, RuntimeError, ValueError):
        return _UNSAFE
    if ".git" in logical.parts or ".git" in relative.parts or not physical.is_file():
        return _UNSAFE
    return physical


def _safe_directory(index: RepoIndex, path: Path) -> Path | object | None:
    if not _present(path):
        return None
    try:
        logical = path.absolute().relative_to(index.root)
        physical = path.resolve(strict=True)
        relative = physical.relative_to(index.root)
    except (OSError, RuntimeError, ValueError):
        return _UNSAFE
    if ".git" in logical.parts or ".git" in relative.parts or not physical.is_dir():
        return _UNSAFE
    return physical


def _read(path: Path) -> Any | object:
    try:
        return load(path).doc
    except YamlReadError:
        return _UNSAFE


def _append_unique(items: list, value: object) -> None:
    if value not in items:
        items.append(value)


def _nonempty(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, (dict, list, tuple, set, str, bytes)):
        return len(value) > 0
    return True


def _issue(inputs: SecurityInputs, path: Path, prefix: tuple = ()) -> None:
    _append_unique(inputs.issues, SecurityIssue(path, prefix))


def _catalog(
    index: RepoIndex,
    candidate: Path,
) -> Path | None:
    selected = _safe_file(index, candidate)
    return selected if isinstance(selected, Path) else None


def _add_source(
    index: RepoIndex,
    inputs: SecurityInputs,
    candidate: Path,
    kind: str,
    environment: str,
    *,
    issue_path: Path | None = None,
) -> Path | None:
    selected = _safe_file(index, candidate)
    if selected is None:
        return None
    if selected is _UNSAFE or _read(selected) is _UNSAFE:
        _issue(inputs, issue_path or candidate.absolute())
        return None
    _append_unique(inputs.sources, SecuritySource(selected, kind, environment))
    return selected


def _environment_definition(env: EnvModel) -> Path:
    return env.path / "Inventory/env_definition.yml"


def _generated_catalog(index: RepoIndex, env: EnvModel, inputs: SecurityInputs) -> Path | None:
    candidate = env.path / "Credentials/credentials.yml"
    return _add_source(index, inputs, candidate, "generated", env.full_name)


def _collect_shared_sources(
    index: RepoIndex, connections: Connections, inputs: SecurityInputs
) -> None:
    for env in index.environments:
        selected = connections.environment_paths.get(env.full_name, frozenset())
        for path in sorted(connections.credentials & selected):
            _add_source(index, inputs, path, "shared", env.full_name)


def _parameter_set_bags(
    index: RepoIndex,
    connections: Connections,
    env: EnvModel,
    catalog: Path | None,
    inputs: SecurityInputs,
) -> None:
    for candidate in sorted(connections.environment_parameter_sets.get(env.full_name, ())):
        selected = _safe_file(index, candidate)
        if selected is _UNSAFE or selected is None:
            _issue(inputs, candidate)
            continue
        doc = _read(selected)
        if doc is _UNSAFE:
            _issue(inputs, selected)
            continue
        if not isinstance(doc, dict):
            _issue(inputs, selected)
            continue
        parameters = doc.get("parameters")
        if isinstance(parameters, dict):
            _append_unique(
                inputs.bags,
                SecurityBag(selected, ("parameters",), env.full_name, catalog),
            )
        elif _nonempty(parameters):
            _issue(inputs, selected)
        applications = doc.get("applications")
        if isinstance(applications, list):
            for position, application in enumerate(applications):
                if not isinstance(application, dict):
                    if _nonempty(application):
                        _issue(inputs, selected)
                    continue
                app_parameters = application.get("parameters")
                if isinstance(app_parameters, dict):
                    _append_unique(
                        inputs.bags,
                        SecurityBag(
                            selected,
                            ("applications", position, "parameters"),
                            env.full_name,
                            catalog,
                        ),
                    )
                elif _nonempty(app_parameters):
                    _issue(inputs, selected)
        elif _nonempty(applications):
            _issue(inputs, selected)


def _direct_reference_bags(
    path: Path,
    doc: dict,
    environment: str,
    catalog: Path | None,
    inputs: SecurityInputs,
) -> None:
    if "defaultCredentialsId" in doc:
        _append_unique(
            inputs.bags,
            SecurityBag(path, (), environment, catalog, ("defaultCredentialsId",)),
        )
    for section in ("maasConfig", "vaultConfig"):
        value = doc.get(section)
        if isinstance(value, dict) and "credentialsId" in value:
            _append_unique(
                inputs.bags,
                SecurityBag(path, (section,), environment, catalog, ("credentialsId",)),
            )
    consul = doc.get("consulConfig")
    if isinstance(consul, dict) and "tokenSecret" in consul:
        _append_unique(
            inputs.bags,
            SecurityBag(path, ("consulConfig",), environment, catalog, ("tokenSecret",)),
        )
    dbaas = doc.get("dbaasConfigs")
    if isinstance(dbaas, list):
        for position, item in enumerate(dbaas):
            if isinstance(item, dict) and "credentialsId" in item:
                _append_unique(
                    inputs.bags,
                    SecurityBag(
                        path,
                        ("dbaasConfigs", position),
                        environment,
                        catalog,
                        ("credentialsId",),
                    ),
                )


def _parameter_object_bags(
    index: RepoIndex,
    connections: Connections,
    catalogs: dict[str, Path | None],
    inputs: SecurityInputs,
) -> None:
    for candidate, environment in parameter_object_paths(index, connections):
        selected = _safe_file(index, candidate)
        if selected is None:
            continue
        if selected is _UNSAFE:
            _issue(inputs, candidate.absolute())
            continue
        doc = _read(selected)
        if doc is _UNSAFE or not isinstance(doc, dict):
            _issue(inputs, selected)
            continue
        catalog = catalogs.get(environment)
        for section in _PARAMETER_SECTIONS:
            value = doc.get(section)
            if isinstance(value, dict):
                _append_unique(
                    inputs.bags,
                    SecurityBag(selected, (section,), environment, catalog),
                )
            elif _nonempty(value):
                _issue(inputs, selected)
        if candidate.name == "cloud.yml":
            _direct_reference_bags(selected, doc, environment, catalog, inputs)
        elif "credentialsId" in doc:
            _append_unique(
                inputs.bags,
                SecurityBag(selected, (), environment, catalog, ("credentialsId",)),
            )


def _passport_companion(
    index: RepoIndex,
    passport: Path,
    environment: str,
    inputs: SecurityInputs,
) -> Path | None:
    candidates = (
        passport.parent / "credentials" / f"{passport.stem}.yml",
        passport.parent / f"{passport.stem}-creds.yml",
    )
    for candidate in candidates:
        if not _present(candidate):
            continue
        return _add_source(
            index,
            inputs,
            candidate,
            "passport",
            environment,
            issue_path=passport,
        )
    return None


def _passport_bags(
    index: RepoIndex, connections: Connections, inputs: SecurityInputs
) -> None:
    for environment, record in sorted(connections.environment_passports.items()):
        selected = _safe_file(index, record.path)
        if selected is _UNSAFE or selected is None:
            _issue(inputs, record.path)
            continue
        companion = _passport_companion(index, record.path, environment, inputs)
        if record.is_jinja or record.error or _read(selected) is _UNSAFE:
            _issue(inputs, selected)
            continue
        _append_unique(inputs.bags, SecurityBag(selected, (), environment, companion))


def _root_catalog(
    index: RepoIndex,
) -> Path | None:
    return _catalog(
        index,
        index.root / "configuration/credentials/credentials.yml",
    )


def _integration_bags(index: RepoIndex, inputs: SecurityInputs) -> None:
    candidate = index.root / "configuration/integration.yml"
    selected = _safe_file(index, candidate)
    if selected is None:
        return
    if selected is _UNSAFE:
        _issue(inputs, candidate.absolute())
        return
    doc = _read(selected)
    if doc is _UNSAFE or not isinstance(doc, dict):
        _issue(inputs, selected)
        return
    explicit_self_token = "self_token" in doc
    discovery = doc.get("cp_discovery")
    gitlab = discovery.get("gitlab") if isinstance(discovery, dict) else None
    active_discovery = (
        isinstance(gitlab, dict)
        and isinstance(gitlab.get("project"), str)
        and bool(gitlab["project"])
    )
    if not explicit_self_token and not active_discovery:
        return
    catalog = _root_catalog(index)
    if explicit_self_token:
        _append_unique(
            inputs.bags,
            SecurityBag(selected, (), "system", catalog, ("self_token",)),
        )
    if active_discovery:
        _append_unique(
            inputs.bags,
            SecurityBag(
                selected,
                ("cp_discovery", "gitlab"),
                "system",
                catalog,
                ("token",),
            ),
        )
        if "token" not in gitlab:
            _issue(inputs, selected, ("cp_discovery", "gitlab", "token"))


def _artifact_definition_bags(
    index: RepoIndex,
    connections: Connections,
    catalogs: dict[str, Path | None],
    inputs: SecurityInputs,
) -> None:
    for env in index.environments:
        selected_for_env = connections.environment_paths.get(env.full_name, frozenset())
        for candidate in sorted(connections.artifact_definitions & selected_for_env):
            selected = _safe_file(index, candidate)
            if selected is _UNSAFE or selected is None:
                _issue(inputs, candidate)
                continue
            doc = _read(selected)
            if doc is _UNSAFE or not isinstance(doc, dict):
                _issue(inputs, selected)
                continue
            registry = doc.get("registry")
            if not isinstance(registry, dict) or "credentialsId" not in registry:
                _issue(inputs, selected, ("registry",))
                continue
            _append_unique(
                inputs.bags,
                SecurityBag(
                    selected,
                    ("registry",),
                    env.full_name,
                    catalogs.get(env.full_name),
                    ("credentialsId",),
                ),
            )


def _legacy_registry_bag(
    index: RepoIndex,
    env: EnvModel,
    env_doc: dict,
    inputs: SecurityInputs,
) -> None:
    template = env_doc.get("envTemplate")
    artifact = template.get("templateArtifact") if isinstance(template, dict) else None
    registry_name = artifact.get("registry") if isinstance(artifact, dict) else None
    if registry_name is None:
        return
    consumer = _environment_definition(env).resolve()
    prefix = ("envTemplate", "templateArtifact", "registry")
    if not isinstance(registry_name, str) or not registry_name:
        _issue(inputs, consumer, prefix)
        return
    candidate = index.root / "configuration/registry.yml"
    selected = _safe_file(index, candidate)
    if selected is _UNSAFE or selected is None:
        _issue(inputs, consumer, prefix)
        return
    doc = _read(selected)
    if doc is _UNSAFE or not isinstance(doc, dict) or not isinstance(doc.get(registry_name), dict):
        _issue(inputs, consumer, prefix)
        return
    catalog = _root_catalog(index)
    _append_unique(
        inputs.bags,
        SecurityBag(
            selected,
            (registry_name,),
            env.full_name,
            catalog,
            ("username", "password"),
        ),
    )


def _first_deployer_definition(
    index: RepoIndex, env: EnvModel
) -> tuple[Path, Path] | object | None:
    for level in (env.path.parent, env.path):
        for directory_name in ("app-deployer", "cloud-deployer"):
            directory = level / directory_name
            safe_directory = _safe_directory(index, directory)
            if safe_directory is _UNSAFE:
                return _UNSAFE
            if safe_directory is None:
                continue
            try:
                entries = tuple(directory.iterdir())
            except OSError:
                return _UNSAFE
            for basename in ("deployer", "app-deployer"):
                for entry in entries:
                    if entry.suffix not in {".yml", ".yaml"} or entry.stem != basename:
                        continue
                    selected = _safe_file(index, entry)
                    return (entry, selected) if isinstance(selected, Path) else _UNSAFE
    return None


def _deployer_catalog(
    index: RepoIndex,
    definition: Path,
) -> Path | None:
    candidates = (
        definition.parent / "deployer-creds.yml",
        definition.parent / "credentials/credentials.yml",
    )
    for candidate in candidates:
        if not _present(candidate):
            continue
        return _catalog(index, candidate)
    return None


def _deployer_bag(
    index: RepoIndex,
    env: EnvModel,
    env_doc: dict,
    inputs: SecurityInputs,
) -> None:
    inventory = env_doc.get("inventory")
    deployer_name = inventory.get("deployer") if isinstance(inventory, dict) else None
    if deployer_name is None:
        return
    consumer = _environment_definition(env).resolve()
    prefix = ("inventory", "deployer")
    if not isinstance(deployer_name, str) or not deployer_name:
        _issue(inputs, consumer, prefix)
        return
    selection = _first_deployer_definition(index, env)
    if selection is _UNSAFE:
        _issue(inputs, consumer, prefix)
        return
    doc: object = {}
    logical_selected: Path | None = None
    physical_selected: Path | None = None
    if isinstance(selection, tuple):
        logical_selected, physical_selected = selection
        doc = _read(physical_selected)
        if doc is _UNSAFE or not isinstance(doc, dict):
            _issue(inputs, consumer, prefix)
            return
    if physical_selected is None or not isinstance(doc.get(deployer_name), dict):
        root_candidate = index.root / "configuration/deployer.yml"
        root_selected = _safe_file(index, root_candidate)
        if root_selected is _UNSAFE or root_selected is None:
            _issue(inputs, consumer, prefix)
            return
        root_doc = _read(root_selected)
        if (
            root_doc is _UNSAFE
            or not isinstance(root_doc, dict)
            or not isinstance(root_doc.get(deployer_name), dict)
        ):
            _issue(inputs, consumer, prefix)
            return
        logical_selected = root_candidate
        physical_selected = root_selected
    if logical_selected is None or physical_selected is None:
        _issue(inputs, consumer, prefix)
        return
    catalog = _deployer_catalog(index, logical_selected)
    _append_unique(
        inputs.bags,
        SecurityBag(
            physical_selected,
            (deployer_name,),
            env.full_name,
            catalog,
            ("username", "token"),
        ),
    )


def _environment_system_bags(
    index: RepoIndex, inputs: SecurityInputs
) -> None:
    for env in index.environments:
        definition = _environment_definition(env)
        selected = _safe_file(index, definition)
        if selected is _UNSAFE or selected is None:
            _issue(inputs, definition.absolute())
            continue
        doc = _read(selected)
        if doc is _UNSAFE or not isinstance(doc, dict):
            _issue(inputs, selected)
            continue
        _legacy_registry_bag(index, env, doc, inputs)
        _deployer_bag(index, env, doc, inputs)


def collect_security_sources(index: RepoIndex, connections: Connections) -> SecurityInputs:
    """Return connected whole sources, consumer bags and generic selection issues."""

    inputs = SecurityInputs()
    _collect_shared_sources(index, connections, inputs)

    catalogs: dict[str, Path | None] = {}
    for env in index.environments:
        catalog = _generated_catalog(index, env, inputs)
        catalogs[env.full_name] = catalog
        _parameter_set_bags(index, connections, env, catalog, inputs)

    _parameter_object_bags(index, connections, catalogs, inputs)
    _passport_bags(index, connections, inputs)
    _artifact_definition_bags(index, connections, catalogs, inputs)
    _integration_bags(index, inputs)
    _environment_system_bags(index, inputs)
    return inputs
