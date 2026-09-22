"""Walk environments/. Do not merge."""

from __future__ import annotations

from pathlib import Path

from .model import (
    Category,
    ClusterModel,
    EnvModel,
    Layer,
    NamedEntityFile,
    ParamsetFile,
    PassportFile,
    RepoIndex,
)
from .yamlio import YamlReadError, load

PARAMETERS_DIR = "parameters"
INVENTORY_DIR = "Inventory"
ENV_DEFINITION_FILE = "env_definition.yml"
PASSPORT_DIRS = ("cloud-passport", "cloud-passports")
RESOURCE_PROFILE_DIRS = ("resource_profiles", "rp_override", "Profiles", "parameters")
CREDENTIAL_DIRS = ("credentials", "Credentials", "shared-credentials")

NON_CLUSTER_DIRS = {
    PARAMETERS_DIR,
    "resource_profiles",
    "rp_override",
    "Profiles",
    "credentials",
    "Credentials",
    "shared-credentials",
    "configuration",
    "configurations",
    "shared_template_variables",
    "shared-template-variables",
    *PASSPORT_DIRS,
}
NON_ENV_DIRS = NON_CLUSTER_DIRS | {"app-deployer", "cloud-deployer"}

NAMED_ENTITY_DIRS = (
    ("appdefs", "Application definition"),
    ("configuration/appdefs", "Application definition"),
    ("regdefs", "Registry definition"),
    ("configuration/regdefs", "Registry definition"),
    ("configuration/artifact_definitions", "Artifact definition"),
)


class DiscoveryError(Exception):
    pass


def paramset_stem(path: Path) -> str:
    name = path.name
    if name.endswith(".j2"):
        name = name[: -len(".j2")]
    for suffix in (".yml", ".yaml", ".json"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


def _is_jinja(path: Path) -> bool:
    return path.name.endswith(".yml.j2") or path.name.endswith(".yaml.j2")


def _yaml_files(directory: Path, root: Path | None = None) -> list[Path]:
    if not directory.is_dir():
        return []
    files = [
        path
        for path in directory.iterdir()
        if path.is_file()
        and (root is None or path.resolve().is_relative_to(root))
        and (
            path.suffix in {".yml", ".yaml"}
            or path.name.endswith(".yml.j2")
            or path.name.endswith(".yaml.j2")
        )
    ]
    return sorted(files)


def _recursive_yaml_files(directory: Path, root: Path, skipped: list[str]) -> list[Path]:
    """Return YAML candidates without traversing .git or escaping through symlinks."""
    if not directory.is_dir():
        return []
    files: list[Path] = []
    pending = [directory]
    while pending:
        current = pending.pop()
        try:
            entries = sorted(current.iterdir(), reverse=True)
        except OSError:
            skipped.append(f"{current}: cannot enumerate directory; PLACE-8 skipped")
            continue
        for path in entries:
            if path.name == ".git":
                continue
            try:
                resolved = path.resolve()
            except OSError:
                continue
            if not resolved.is_relative_to(root):
                continue
            if path.is_dir():
                if not path.is_symlink():
                    pending.append(path)
                continue
            if not path.is_file():
                continue
            if (
                path.suffix in {".yml", ".yaml"}
                or path.name.endswith(".yml.j2")
                or path.name.endswith(".yaml.j2")
            ):
                files.append(path)
    return sorted(files)


def _load_place8_entity(
    path: Path,
    kind: str,
    skipped: list[str],
    reused: dict[Path, ParamsetFile],
) -> NamedEntityFile:
    stem = paramset_stem(path)
    paramset = reused.get(path.resolve())
    if paramset is not None:
        return NamedEntityFile(
            path=path,
            stem=stem,
            kind=kind,
            is_jinja=paramset.is_jinja,
            loaded=paramset.loaded,
            error=paramset.error,
        )
    if _is_jinja(path):
        skipped.append(f"{path}: jinja {kind} skipped")
        return NamedEntityFile(path=path, stem=stem, kind=kind, is_jinja=True)
    try:
        loaded = load(path)
    except YamlReadError:
        note = f"{path}: cannot parse YAML; PLACE-8 skipped"
        skipped.append(note)
        return NamedEntityFile(path=path, stem=stem, kind=kind, error=note)
    return NamedEntityFile(path=path, stem=stem, kind=kind, loaded=loaded)


def _load_place8_entities(
    root: Path,
    bases: list[Path],
    directories: tuple[str, ...],
    kind: str,
    skipped: list[str],
    reused: dict[Path, ParamsetFile],
) -> list[NamedEntityFile]:
    files: list[NamedEntityFile] = []
    seen: dict[Path, NamedEntityFile] = {}
    for base in bases:
        for folder in directories:
            for path in _recursive_yaml_files(base / folder, root, skipped):
                resolved = path.resolve()
                if resolved in seen:
                    record = seen[resolved]
                    record.aliases = (*record.aliases, path)
                    continue
                record = _load_place8_entity(path, kind, skipped, reused)
                seen[resolved] = record
                files.append(record)
    return files


def _load_named_entities(root: Path, skipped: list[str]) -> list[NamedEntityFile]:
    files: list[NamedEntityFile] = []
    seen: set[Path] = set()
    for relative, kind in NAMED_ENTITY_DIRS:
        for path in _yaml_files(root / relative, root):
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            stem = paramset_stem(path)
            if _is_jinja(path):
                skipped.append(f"{path}: jinja named entity skipped")
                files.append(NamedEntityFile(path=path, stem=stem, kind=kind, is_jinja=True))
                continue
            try:
                loaded = load(path)
            except YamlReadError as exc:
                skipped.append(str(exc))
                files.append(NamedEntityFile(path=path, stem=stem, kind=kind, error=str(exc)))
                continue
            files.append(NamedEntityFile(path=path, stem=stem, kind=kind, loaded=loaded))
    return files


def _load_paramset(
    path: Path, layer: Layer, cluster: str | None, env: str | None, skipped: list[str]
) -> ParamsetFile:
    stem = paramset_stem(path)
    if _is_jinja(path):
        skipped.append(f"{path}: jinja ParameterSet skipped")
        return ParamsetFile(path=path, layer=layer, stem=stem, cluster=cluster, env=env, is_jinja=True)
    try:
        loaded = load(path)
    except YamlReadError:
        note = f"{path}: cannot parse YAML; ParameterSet skipped"
        skipped.append(note)
        return ParamsetFile(path=path, layer=layer, stem=stem, cluster=cluster, env=env, error=note)
    return ParamsetFile(path=path, layer=layer, stem=stem, cluster=cluster, env=env, loaded=loaded)


def _cloud_passport_name(doc: object) -> str | None:
    doc = doc if isinstance(doc, dict) else {}
    inventory = doc.get("inventory") if isinstance(doc.get("inventory"), dict) else {}
    value = inventory.get("cloudPassport")
    if isinstance(value, str) and value:
        return value
    return None


def _is_creds_passport(path: Path) -> bool:
    name = path.name
    if name.endswith(".j2"):
        name = name[: -len(".j2")]
    return name.endswith("-creds.yml") or name.endswith("-creds.yaml")


def _under_credentials(path: Path, root: Path) -> bool:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return False
    return any(part in {"credentials", "Credentials"} for part in relative.parts)


def _passport_files(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []
    files = [
        path
        for path in directory.rglob("*")
        if path.is_file()
        and not _under_credentials(path, directory)
        and not _is_creds_passport(path)
        and (
            path.suffix in {".yml", ".yaml"}
            or path.name.endswith(".yml.j2")
            or path.name.endswith(".yaml.j2")
        )
    ]
    return sorted(files)


def _load_passport(
    path: Path, cluster: str | None, env: str | None, skipped: list[str]
) -> PassportFile:
    stem = paramset_stem(path)
    if _is_jinja(path):
        skipped.append(f"{path}: jinja Cloud Passport skipped")
        return PassportFile(path=path, stem=stem, cluster=cluster, env=env, is_jinja=True)
    try:
        loaded = load(path)
    except YamlReadError as exc:
        skipped.append(str(exc))
        return PassportFile(path=path, stem=stem, cluster=cluster, env=env, error=str(exc))
    return PassportFile(path=path, stem=stem, cluster=cluster, env=env, loaded=loaded)


def _bindings(doc: object) -> dict[Category, dict[str, list[str]]]:
    doc = doc if isinstance(doc, dict) else {}
    template = doc.get("envTemplate") if isinstance(doc.get("envTemplate"), dict) else {}
    out: dict[Category, dict[str, list[str]]] = {}
    for category in Category:
        raw = template.get(category.binding_field)
        if not isinstance(raw, dict):
            continue
        targets: dict[str, list[str]] = {}
        for target, names in raw.items():
            if isinstance(names, list):
                targets[str(target)] = [str(item) for item in names]
        if targets:
            out[category] = targets
    return out


def _resource_profile_bindings(doc: object) -> dict[str, str]:
    doc = doc if isinstance(doc, dict) else {}
    template = doc.get("envTemplate") if isinstance(doc.get("envTemplate"), dict) else {}
    raw = template.get("envSpecificResourceProfiles")
    if not isinstance(raw, dict):
        return {}
    return {
        target: reference
        for target, reference in raw.items()
        if isinstance(target, str) and isinstance(reference, str)
    }


def _shared_credential_bindings(doc: object) -> list[str]:
    doc = doc if isinstance(doc, dict) else {}
    template = doc.get("envTemplate") if isinstance(doc.get("envTemplate"), dict) else {}
    raw = template.get("sharedMasterCredentialFiles")
    if not isinstance(raw, list):
        return []
    return [reference for reference in raw if isinstance(reference, str)]


def _shared_template_variable_bindings(doc: object) -> list[str]:
    doc = doc if isinstance(doc, dict) else {}
    template = doc.get("envTemplate") if isinstance(doc.get("envTemplate"), dict) else {}
    raw = template.get("sharedTemplateVariables")
    if not isinstance(raw, list):
        return []
    return [reference for reference in raw if isinstance(reference, str)]


def _artifact_selectors(doc: object) -> tuple[str, ...]:
    doc = doc if isinstance(doc, dict) else {}
    template = doc.get("envTemplate") if isinstance(doc.get("envTemplate"), dict) else {}
    background = (
        template.get("bgNsArtifacts")
        if isinstance(template.get("bgNsArtifacts"), dict)
        else {}
    )
    values = (
        template.get("artifact"),
        background.get("origin"),
        background.get("peer"),
    )
    return tuple(value for value in values if isinstance(value, str))


def build_index(root: Path) -> RepoIndex:
    root = root.resolve()
    environments_dir = root / "environments"
    if not environments_dir.is_dir():
        raise DiscoveryError(f"{root} is not an instance repository: no environments/ directory")

    skipped: list[str] = []
    passports: list[PassportFile] = []
    for folder in PASSPORT_DIRS:
        passports.extend(
            _load_passport(path, None, None, skipped) for path in _passport_files(environments_dir / folder)
        )
    site = [
        _load_paramset(path, Layer.REPOSITORY, None, None, skipped)
        for path in _yaml_files(environments_dir / PARAMETERS_DIR, root)
    ]
    clusters: dict[str, ClusterModel] = {}
    for cluster_dir in sorted(p for p in environments_dir.iterdir() if p.is_dir()):
        if cluster_dir.name in NON_CLUSTER_DIRS:
            continue
        cluster = ClusterModel(name=cluster_dir.name, path=cluster_dir)
        cluster.paramsets = [
            _load_paramset(path, Layer.CLUSTER, cluster.name, None, skipped)
            for path in _yaml_files(cluster_dir / PARAMETERS_DIR, root)
        ]
        for folder in PASSPORT_DIRS:
            passports.extend(
                _load_passport(path, cluster.name, None, skipped)
                for path in _passport_files(cluster_dir / folder)
            )
        for env_dir in sorted(p for p in cluster_dir.iterdir() if p.is_dir()):
            if env_dir.name in NON_ENV_DIRS:
                continue
            definition = env_dir / INVENTORY_DIR / ENV_DEFINITION_FILE
            if not definition.is_file():
                continue
            try:
                loaded_definition = load(definition)
                doc = loaded_definition.doc
                bindings = _bindings(doc)
                cloud_passport = _cloud_passport_name(doc)
                resource_profile_bindings = _resource_profile_bindings(doc)
                shared_credential_bindings = _shared_credential_bindings(doc)
                shared_template_variable_bindings = _shared_template_variable_bindings(doc)
                artifact_selectors = _artifact_selectors(doc)
            except YamlReadError as exc:
                skipped.append(str(exc))
                bindings = {}
                cloud_passport = None
                resource_profile_bindings = {}
                shared_credential_bindings = []
                shared_template_variable_bindings = []
                artifact_selectors = ()
            env = EnvModel(
                cluster=cluster.name,
                name=env_dir.name,
                path=env_dir,
                bindings=bindings,
                cloud_passport=cloud_passport,
                resource_profile_bindings=resource_profile_bindings,
                shared_credential_bindings=shared_credential_bindings,
                shared_template_variable_bindings=shared_template_variable_bindings,
                artifact_selectors=artifact_selectors,
            )
            env.paramsets = [
                _load_paramset(path, Layer.ENVIRONMENT, cluster.name, env.name, skipped)
                for path in _yaml_files(env_dir / INVENTORY_DIR / PARAMETERS_DIR, root)
            ]
            for folder in PASSPORT_DIRS:
                passports.extend(
                    _load_passport(path, cluster.name, env.name, skipped)
                    for path in _passport_files(env_dir / INVENTORY_DIR / folder)
                )
            cluster.environments.append(env)
        clusters[cluster.name] = cluster
    named_entities = _load_named_entities(root, skipped)
    all_paramsets = [*site]
    bases = [environments_dir]
    for cluster in clusters.values():
        all_paramsets.extend(cluster.paramsets)
        bases.append(cluster.path)
        for env in cluster.environments:
            all_paramsets.extend(env.paramsets)
            bases.append(env.path / INVENTORY_DIR)
    reused = {item.path.resolve(): item for item in all_paramsets}
    resource_profiles = _load_place8_entities(
        root,
        bases,
        RESOURCE_PROFILE_DIRS,
        "Resource Profile Override",
        skipped,
        reused,
    )
    credential_files = _load_place8_entities(
        root,
        bases,
        CREDENTIAL_DIRS,
        "Credentials file",
        skipped,
        reused,
    )
    return RepoIndex(
        root=root,
        site_paramsets=site,
        clusters=clusters,
        passports=passports,
        skipped=skipped,
        named_entities=named_entities,
        resource_profiles=resource_profiles,
        credential_files=credential_files,
    )
