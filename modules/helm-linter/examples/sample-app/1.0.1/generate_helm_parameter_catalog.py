#!/usr/bin/env python3
"""Build per-application Helm values-schema catalogs from EnvGene SDs."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tarfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment-specific message
    raise SystemExit(
        "PyYAML is required. Run this script through ~/git/venv/bin/python."
    ) from exc

try:
    import app_ver_helper
    from helpers.artifactory_downloader import ArtifactDownloadError
except ImportError:  # Imported as scripts.generate_helm_parameter_catalog.
    from scripts import app_ver_helper
    from scripts.helpers.artifactory_downloader import ArtifactDownloadError


CATALOG_SCHEMA_VERSION = 1
GENERATOR_NAME = "generate_helm_parameter_catalog.py"
SUPPORTED_SD_VERSIONS = {"2.1", "2.2"}
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[1] / "artifacts" / "helm-parameter-catalog"
DEFAULT_CACHE_DIR = Path(__file__).resolve().parents[1] / "tmp" / "helm-parameter-catalog"


class CatalogError(RuntimeError):
    """Expected input, resolution, or download failure."""


@dataclass(frozen=True)
class ApplicationRequest:
    name: str
    version: str
    deploy_postfixes: tuple[str, ...]
    source_descriptors: tuple[Path, ...] = ()

    @property
    def app_version(self) -> str:
        return f"{self.name}:{self.version}"

    @property
    def primary_descriptor(self) -> Path:
        if not self.source_descriptors:
            raise CatalogError(f"Application {self.name!r} has no source Solution Descriptor")
        return self.source_descriptors[0]


@dataclass(frozen=True)
class ArtifactCoordinates:
    application: str
    version: str
    group_id: str
    artifact_id: str
    registry_name: str
    repository_domain: str
    repositories: tuple[str, ...]
    repository_config: tuple[tuple[str, str], ...] = ()


class NoAliasDumper(yaml.SafeDumper):
    """Keep generated catalogs explicit and stable."""

    def ignore_aliases(self, data: Any) -> bool:
        return True


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise CatalogError(f"Cannot read YAML file {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise CatalogError(f"Expected a YAML mapping in {path}")
    return data


def parse_app_version(value: Any, source: Path) -> tuple[str, str]:
    if not isinstance(value, str) or ":" not in value:
        raise CatalogError(
            f"Invalid applications[].version in {source}: expected App:Ver, got {value!r}"
        )
    name, version = value.split(":", 1)
    name, version = name.strip(), version.strip()
    if not name or not version:
        raise CatalogError(f"Invalid App:Ver value {value!r} in {source}")
    if "/" in name or "\\" in name or name in {".", ".."}:
        raise CatalogError(f"Application name is unsafe for an output filename: {name!r}")
    return name, version


def parse_solution_descriptor(path: Path) -> list[ApplicationRequest]:
    return parse_solution_descriptors([path])


def parse_solution_descriptors(paths: Sequence[Path]) -> list[ApplicationRequest]:
    if not paths:
        raise CatalogError("At least one Solution Descriptor is required")
    grouped: dict[str, tuple[str, set[str], list[Path]]] = {}
    for path in paths:
        resolved = path.resolve()
        if not resolved.is_file():
            raise CatalogError(f"Solution Descriptor does not exist: {resolved}")
        data = load_yaml(resolved)
        sd_version = str(data.get("version", ""))
        if sd_version not in SUPPORTED_SD_VERSIONS:
            raise CatalogError(
                f"Unsupported Solution Descriptor version {sd_version!r} in {resolved}; "
                f"expected one of {sorted(SUPPORTED_SD_VERSIONS)}"
            )
        applications = data.get("applications")
        if not isinstance(applications, list) or not applications:
            raise CatalogError(f"No applications list found in {resolved}")
        for item in applications:
            if not isinstance(item, dict):
                raise CatalogError(f"Invalid application entry in {resolved}: {item!r}")
            name, version = parse_app_version(item.get("version"), resolved)
            postfix = item.get("deployPostfix")
            postfixes = {str(postfix)} if postfix is not None else set()
            if name in grouped:
                existing_version, existing_postfixes, existing_sources = grouped[name]
                if existing_version != version:
                    raise CatalogError(
                        f"Application {name!r} occurs with versions {existing_version!r} "
                        f"and {version!r}; version-independent catalog filenames are ambiguous"
                    )
                existing_postfixes.update(postfixes)
                if resolved not in existing_sources:
                    existing_sources.append(resolved)
            else:
                grouped[name] = (version, postfixes, [resolved])

    return [
        ApplicationRequest(
            name, version, tuple(sorted(postfixes)), tuple(sources)
        )
        for name, (version, postfixes, sources) in sorted(grouped.items())
    ]


def descriptor_sources(paths: Sequence[Path]) -> list[dict[str, str]]:
    return [
        {
            "path": str(path.resolve()),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        for path in paths
    ]


def infer_environment_root(sd_path: Path) -> Path:
    resolved = sd_path.resolve()
    for parent in resolved.parents:
        if parent.name == "Inventory":
            return parent.parent
    raise CatalogError(
        "Cannot infer the environment root from the Solution Descriptor path. "
        "Place it under <environment>/Inventory/solution-descriptor/ or pass "
        "--appdefs-dir and --regdefs-dir."
    )


def resolve_named_yaml(directory: Path, name: str, kind: str) -> Path:
    candidates = [directory / f"{name}.yaml", directory / f"{name}.yml"]
    matches = [candidate for candidate in candidates if candidate.is_file()]
    if not matches:
        raise CatalogError(f"{kind} {name!r} not found in {directory}")
    if len(matches) > 1:
        raise CatalogError(
            f"Both YAML filename variants exist for {kind} {name!r}: "
            + ", ".join(str(match) for match in matches)
        )
    return matches[0]


def resolve_coordinates(
    request: ApplicationRequest, appdefs_dir: Path, regdefs_dir: Path
) -> ArtifactCoordinates:
    appdef_path = resolve_named_yaml(appdefs_dir, request.name, "AppDef")
    appdef = load_yaml(appdef_path)
    declared_name = appdef.get("name")
    if declared_name != request.name:
        raise CatalogError(
            f"AppDef filename/name mismatch in {appdef_path}: "
            f"expected {request.name!r}, got {declared_name!r}"
        )
    required = ("registryName", "groupId", "artifactId")
    missing = [key for key in required if not appdef.get(key)]
    if missing:
        raise CatalogError(f"AppDef {appdef_path} lacks: {', '.join(missing)}")

    registry_name = str(appdef["registryName"])
    regdef_path = resolve_named_yaml(regdefs_dir, registry_name, "RegDef")
    regdef = load_yaml(regdef_path)
    if regdef.get("name") != registry_name:
        raise CatalogError(
            f"RegDef filename/name mismatch in {regdef_path}: "
            f"expected {registry_name!r}, got {regdef.get('name')!r}"
        )
    maven = regdef.get("mavenConfig")
    if not isinstance(maven, dict):
        raise CatalogError(f"RegDef {regdef_path} has no mavenConfig mapping")
    domain = str(maven.get("repositoryDomainName") or "").rstrip("/")
    if not domain:
        raise CatalogError(f"RegDef {regdef_path} has no Maven repositoryDomainName")
    repository_config = tuple(
        (key, str(maven[key]).strip("/"))
        for key in ("targetRelease", "targetStaging", "targetSnapshot")
        if maven.get(key)
    )
    repositories = tuple(dict.fromkeys(value for _, value in repository_config))
    if not repositories:
        raise CatalogError(f"RegDef {regdef_path} has no target Maven repositories")
    return ArtifactCoordinates(
        application=request.name,
        version=request.version,
        group_id=str(appdef["groupId"]),
        artifact_id=str(appdef["artifactId"]),
        registry_name=registry_name,
        repository_domain=domain,
        repositories=repositories,
        repository_config=repository_config,
    )


def write_resolved_appdef(
    coordinates: ArtifactCoordinates, destination: Path
) -> Path:
    """Create the embedded-registry AppDef format consumed by app_ver_helper."""
    maven_config: dict[str, str] = {
        "repositoryDomainName": coordinates.repository_domain
    }
    repository_config = coordinates.repository_config or tuple(
        zip(
            ("targetRelease", "targetStaging", "targetSnapshot"),
            coordinates.repositories,
        )
    )
    for key, repository in repository_config:
        maven_config[key] = repository
    data = {
        "name": coordinates.application,
        "groupId": coordinates.group_id,
        "artifactId": coordinates.artifact_id,
        "registry": {"mavenConfig": maven_config},
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        yaml.safe_dump(data, sort_keys=False),
        encoding="utf-8",
    )
    return destination


def decode_json(data: bytes, source: str) -> dict[str, Any]:
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CatalogError(f"Invalid JSON in {source}: {exc}") from exc
    if not isinstance(value, dict):
        raise CatalogError(f"Expected a JSON object in {source}")
    return value


def json_pointer_get(document: Mapping[str, Any], pointer: str) -> Any:
    if not pointer.startswith("#/"):
        raise CatalogError(f"Only local JSON Schema references are supported: {pointer}")
    current: Any = document
    for raw_part in pointer[2:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, Mapping) or part not in current:
            raise CatalogError(f"Unresolvable local JSON Schema reference: {pointer}")
        current = current[part]
    return current


def merge_schema(base: Mapping[str, Any], overlay: Mapping[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in overlay.items():
        if key == "properties" and isinstance(value, Mapping):
            properties = dict(merged.get("properties") or {})
            properties.update(value)
            merged[key] = properties
        elif key == "required" and isinstance(value, list):
            merged[key] = list(dict.fromkeys([*(merged.get(key) or []), *value]))
        else:
            merged[key] = value
    return merged


def normalize_schema(
    schema: Mapping[str, Any],
    document: Mapping[str, Any],
    seen_refs: frozenset[str] = frozenset(),
) -> dict[str, Any]:
    result = dict(schema)
    reference = result.pop("$ref", None)
    if reference:
        if reference in seen_refs:
            raise CatalogError(f"Cyclic local JSON Schema reference: {reference}")
        target = json_pointer_get(document, str(reference))
        if not isinstance(target, Mapping):
            raise CatalogError(f"JSON Schema reference does not target an object: {reference}")
        resolved = normalize_schema(target, document, seen_refs | {str(reference)})
        result = merge_schema(resolved, result)
    all_of = result.pop("allOf", None)
    if isinstance(all_of, list):
        combined: dict[str, Any] = {}
        for part in all_of:
            if isinstance(part, Mapping):
                combined = merge_schema(combined, normalize_schema(part, document, seen_refs))
        result = merge_schema(combined, result)
    return result


def pointer_escape(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def schema_types(schema: Mapping[str, Any]) -> str | list[str] | None:
    value = schema.get("type")
    if isinstance(value, (str, list)):
        return value
    if "properties" in schema or "additionalProperties" in schema:
        return "object"
    return None


def flatten_schema(document: Mapping[str, Any]) -> list[dict[str, Any]]:
    root = normalize_schema(document, document)
    properties = root.get("properties")
    if not isinstance(properties, Mapping):
        return []
    output: list[dict[str, Any]] = []

    def walk(
        node_properties: Mapping[str, Any],
        required_names: set[str],
        key_prefix: tuple[str, ...],
        pointer_prefix: str,
    ) -> None:
        for name in sorted(node_properties):
            raw_schema = node_properties[name]
            if not isinstance(raw_schema, Mapping):
                continue
            schema = normalize_schema(raw_schema, document)
            key_parts = (*key_prefix, str(name))
            key = ".".join(key_parts)
            pointer = f"{pointer_prefix}/{pointer_escape(str(name))}"
            children = schema.get("properties")
            has_children = isinstance(children, Mapping) and bool(children)
            is_open_map = "additionalProperties" in schema
            if not has_children or is_open_map:
                item: dict[str, Any] = {
                    "key": key,
                    "jsonPointer": pointer,
                    "required": str(name) in required_names,
                }
                value_type = schema_types(schema)
                if value_type is not None:
                    item["type"] = value_type
                for field in ("description", "title", "default", "internal", "envSpecific"):
                    if field in schema:
                        item[field] = schema[field]
                if is_open_map:
                    item["additionalProperties"] = schema["additionalProperties"]
                output.append(item)
            if has_children:
                child_required = {
                    str(value) for value in schema.get("required", []) if isinstance(value, str)
                }
                walk(
                    children,
                    child_required,
                    key_parts,
                    f"{pointer}/properties",
                )

    root_required = {
        str(value) for value in root.get("required", []) if isinstance(value, str)
    }
    walk(properties, root_required, (), "#/properties")
    return sorted(output, key=lambda item: item["key"])


def archive_members(archive_path: Path) -> tuple[str, Sequence[str], Any]:
    """Open a Helm .tgz or a ZIP archive and return (kind, names, reader)."""
    if tarfile.is_tarfile(archive_path):
        archive = tarfile.open(archive_path)
        names = [
            member.name
            for member in archive.getmembers()
            if member.isfile()
        ]
        return "tar", names, archive
    try:
        archive = zipfile.ZipFile(archive_path)
    except (OSError, zipfile.BadZipFile) as exc:
        raise CatalogError(f"Invalid Helm chart archive {archive_path}: {exc}") from exc
    return "zip", archive.namelist(), archive


def read_archive_member(kind: str, archive: Any, member: str) -> bytes:
    if kind == "tar":
        extracted = archive.extractfile(member)
        if extracted is None:
            raise CatalogError(f"Cannot read archive member {member}")
        return extracted.read()
    return archive.read(member)


def select_schema_member(
    members: Sequence[str], application: str, service: str
) -> str | None:
    suffixes = (
        f"deployment-artifacts/{service}/helm-templates/{service}/values.schema.json",
        f"helm-templates/{service}/values.schema.json",
        f"charts/{service}/values.schema.json",
        f"{service}/values.schema.json",
    )
    for suffix in suffixes:
        matches = [member for member in members if member.rstrip("/").endswith(suffix)]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise CatalogError(
                f"Multiple values.schema.json files found for {application}/{service}"
            )
    return None


def services_from_dd(dd: Mapping[str, Any], source: Path) -> list[str]:
    services = dd.get("services")
    if not isinstance(services, list):
        return []
    names: list[str] = []
    for service in services:
        if not isinstance(service, Mapping) or not service.get("service_name"):
            raise CatalogError(f"Invalid service entry in Deployment Descriptor {source}")
        names.append(str(service["service_name"]))
    return sorted(dict.fromkeys(names))


def charts_from_dd(dd: Mapping[str, Any]) -> list[dict[str, Any]]:
    charts = dd.get("charts")
    if not isinstance(charts, list):
        return []
    output: list[dict[str, Any]] = []
    for chart in charts:
        if not isinstance(chart, Mapping):
            continue
        output.append(
            {
                "helmChartName": chart.get("helm_chart_name"),
                "helmChartVersion": chart.get("helm_chart_version"),
                "helmRegistry": chart.get("helm_registry"),
                "fullChartName": chart.get("full_chart_name"),
                "type": chart.get("type"),
            }
        )
    return output


def build_catalog(
    request: ApplicationRequest,
    coordinates: ArtifactCoordinates,
    dd_path: Path,
    chart_paths: Sequence[Path],
) -> dict[str, Any]:
    dd = decode_json(dd_path.read_bytes(), str(dd_path))
    service_names = services_from_dd(dd, dd_path)
    service_catalogs: list[dict[str, Any]] = []
    unresolved: list[dict[str, str]] = []
    union: dict[str, set[str]] = {}
    matched_services: set[str] = set()

    if not chart_paths:
        raise CatalogError(f"No Helm charts downloaded for {request.app_version}")

    for chart_path in chart_paths:
        kind, members, archive = archive_members(chart_path)
        try:
            for service_name in service_names:
                schema_member = select_schema_member(members, request.name, service_name)
                if schema_member is None:
                    continue
                matched_services.add(service_name)
                schema = decode_json(
                    read_archive_member(kind, archive, schema_member),
                    f"{chart_path}!/{schema_member}",
                )
                parameters = flatten_schema(schema)
                for parameter in parameters:
                    union.setdefault(parameter["key"], set()).add(service_name)
                service_catalogs.append(
                    {
                        "serviceName": service_name,
                        "chartArchive": chart_path.name,
                        "schemaPath": schema_member,
                        "parameters": parameters,
                    }
                )
            if not service_names:
                root_schemas = [
                    member
                    for member in members
                    if member.rstrip("/").endswith("/values.schema.json")
                    or member == "values.schema.json"
                ]
                for schema_member in sorted(root_schemas):
                    schema = decode_json(
                        read_archive_member(kind, archive, schema_member),
                        f"{chart_path}!/{schema_member}",
                    )
                    parameters = flatten_schema(schema)
                    owner = Path(schema_member).parent.name or chart_path.stem
                    for parameter in parameters:
                        union.setdefault(parameter["key"], set()).add(owner)
                    service_catalogs.append(
                        {
                            "serviceName": owner,
                            "chartArchive": chart_path.name,
                            "schemaPath": schema_member,
                            "parameters": parameters,
                        }
                    )
        finally:
            archive.close()

    for service_name in service_names:
        if service_name not in matched_services:
            unresolved.append(
                {"serviceName": service_name, "reason": "values.schema.json not found"}
            )

    supported = sorted(union)
    parameter_union = [
        {"key": key, "definedByServices": sorted(union[key])} for key in supported
    ]
    return {
        "schemaVersion": CATALOG_SCHEMA_VERSION,
        "application": {
            "name": request.name,
            "version": request.version,
            "appVersion": request.app_version,
            "deployPostfixes": list(request.deploy_postfixes),
        },
        "source": {
            "solutionDescriptors": descriptor_sources(request.source_descriptors),
            "artifact": {
                "registryName": coordinates.registry_name,
                "repositories": list(coordinates.repositories),
                "groupId": coordinates.group_id,
                "artifactId": coordinates.artifact_id,
                "charts": charts_from_dd(dd),
            },
        },
        "generatedBy": {
            "name": GENERATOR_NAME,
            "catalogSchemaVersion": CATALOG_SCHEMA_VERSION,
        },
        "supportedParameters": supported,
        "parameters": parameter_union,
        "services": service_catalogs,
        "unresolvedServices": unresolved,
    }


def write_catalog(catalog: Mapping[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = yaml.dump(
        dict(catalog),
        Dumper=NoAliasDumper,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
        width=120,
    )
    output_path.write_text(content, encoding="utf-8")


def download_resource_profiles(
    request: ApplicationRequest,
    chart_paths: Sequence[Path],
    output_dir: Path,
    resource_profile: str | None,
) -> tuple[list[Path], list[str]]:
    """Copy all, or one requested, profiles from downloaded Helm chart archives."""
    destination_root = output_dir.resolve() / request.name / "resource-profiles"
    shutil.rmtree(destination_root, ignore_errors=True)
    written: list[Path] = []
    missing: list[str] = []
    for chart_path in chart_paths:
        kind, members, archive = archive_members(chart_path)
        try:
            matching_members = [
                member
                for member in members
                if "/resource-profiles/" in member
                and member.lower().endswith((".yaml", ".yml"))
                and (
                    resource_profile is None
                    or member.rstrip("/").endswith(
                        f"/resource-profiles/{resource_profile}.yaml"
                    )
                    or member.rstrip("/").endswith(
                        f"/resource-profiles/{resource_profile}.yml"
                    )
                )
            ]
            if not matching_members:
                missing.append(chart_path.name)
                continue
            for member in sorted(matching_members):
                parts = Path(member).parts
                resource_profiles_index = parts.index("resource-profiles")
                chart_name = parts[resource_profiles_index - 1]
                destination = (
                    destination_root / chart_name / Path(member).name
                )
                content = read_archive_member(kind, archive, member)
                if destination.is_file() and destination.read_bytes() != content:
                    raise CatalogError(
                        f"Conflicting resource profile for "
                        f"{request.name}/{chart_name}"
                    )
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(content)
                written.append(destination)
        finally:
            archive.close()
    return written, missing


def download_chart_default_values(
    request: ApplicationRequest,
    chart_paths: Sequence[Path],
    output_dir: Path,
) -> list[Path]:
    """Copy default values.yaml files from downloaded Helm chart archives."""
    destination_root = output_dir.resolve() / request.name / "default-values"
    shutil.rmtree(destination_root, ignore_errors=True)
    written: list[Path] = []
    for chart_path in chart_paths:
        kind, members, archive = archive_members(chart_path)
        try:
            matching_members = [
                member
                for member in members
                if member.rstrip("/").endswith("/values.yaml") or member == "values.yaml"
            ]
            for member in sorted(matching_members):
                parts = Path(member).parts
                chart_name = parts[-2] if len(parts) > 1 else chart_path.stem
                destination = destination_root / chart_name / "values.yaml"
                content = read_archive_member(kind, archive, member)
                if destination.is_file() and destination.read_bytes() != content:
                    raise CatalogError(
                        f"Conflicting default values for {request.name}/{chart_name}"
                    )
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(content)
                written.append(destination)
        finally:
            archive.close()
    return written


def default_definition_dirs(
    sd_path: Path,
    appdefs_dir: Path | None,
    regdefs_dir: Path | None,
) -> tuple[Path, Path]:
    if appdefs_dir and regdefs_dir:
        return appdefs_dir.resolve(), regdefs_dir.resolve()
    root = infer_environment_root(sd_path)
    return (
        (appdefs_dir or root / "AppDefs").resolve(),
        (regdefs_dir or root / "RegDefs").resolve(),
    )


def normalize_descriptor_paths(sd_paths: Path | Sequence[Path]) -> list[Path]:
    paths = [sd_paths] if isinstance(sd_paths, Path) else list(sd_paths)
    resolved: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        item = path.resolve()
        if item in seen:
            continue
        seen.add(item)
        if not item.is_file():
            raise CatalogError(f"Solution Descriptor does not exist: {item}")
        resolved.append(item)
    if not resolved:
        raise CatalogError("At least one Solution Descriptor is required")
    return resolved


def generate_catalogs(
    sd_paths: Path | Sequence[Path],
    output_dir: Path,
    cache_dir: Path,
    appdefs_dir: Path | None = None,
    regdefs_dir: Path | None = None,
    resource_profile: str | None = None,
) -> list[Path]:
    if resource_profile is not None and (
        not resource_profile
        or "/" in resource_profile
        or "\\" in resource_profile
    ):
        raise CatalogError(f"Resource profile name is unsafe: {resource_profile!r}")
    descriptors = normalize_descriptor_paths(sd_paths)
    requests = parse_solution_descriptors(descriptors)
    written: list[Path] = []
    index_applications: list[dict[str, Any]] = []
    for request in requests:
        resolved_appdefs, resolved_regdefs = default_definition_dirs(
            request.primary_descriptor, appdefs_dir, regdefs_dir
        )
        coordinates = resolve_coordinates(request, resolved_appdefs, resolved_regdefs)
        app_cache = cache_dir.resolve() / request.name
        resolved_appdef = write_resolved_appdef(
            coordinates, app_cache / "resolved-appdef.yml"
        )
        try:
            dd, dd_path, chart_paths = app_ver_helper.download_application_artifacts(
                request.app_version,
                str(resolved_appdef),
                str(app_cache),
            )
        except (ArtifactDownloadError, ReferenceError, ValueError, OSError) as exc:
            raise CatalogError(
                f"Cannot download deployment artifacts for {request.app_version}: {exc}"
            ) from exc
        catalog = build_catalog(
            request,
            coordinates,
            Path(dd_path),
            [Path(path) for path in chart_paths],
        )
        try:
            resource_profiles, missing_resource_profiles = download_resource_profiles(
                request, [Path(path) for path in chart_paths], output_dir, resource_profile
            )
        except CatalogError as exc:
            resource_profiles, missing_resource_profiles = [], []
            print(f"  Resource profiles unavailable: {exc}")
        default_values = download_chart_default_values(
            request, [Path(path) for path in chart_paths], output_dir
        )
        output_path = output_dir.resolve() / f"{request.name}.yaml"
        write_catalog(catalog, output_path)
        written.append(output_path)
        index_applications.append(
            {
                "name": request.name,
                "version": request.version,
                "appVersion": request.app_version,
                "deployPostfixes": list(request.deploy_postfixes),
                "catalog": output_path.name,
                "supportedParameterCount": len(catalog["supportedParameters"]),
                "unresolvedServiceCount": len(catalog["unresolvedServices"]),
            }
        )
        unresolved_count = len(catalog["unresolvedServices"])
        print(
            f"{request.app_version}: {len(catalog['supportedParameters'])} parameters, "
            f"{len(catalog['services'])} schemas, {unresolved_count} unresolved services, "
            f"{len(resource_profiles)} resource profiles, {len(default_values)} default values files"
        )
        if missing_resource_profiles:
            print(
                f"  Charts without requested resource profiles: "
                f"{', '.join(missing_resource_profiles)}"
            )
    index = {
        "schemaVersion": CATALOG_SCHEMA_VERSION,
        "source": {
            "solutionDescriptors": descriptor_sources(descriptors),
        },
        "generatedBy": {
            "name": GENERATOR_NAME,
            "catalogSchemaVersion": CATALOG_SCHEMA_VERSION,
        },
        "applications": index_applications,
    }
    index_path = output_dir.resolve() / "index.yaml"
    write_catalog(index, index_path)
    written.append(index_path)
    return written


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Download deployment descriptor artifacts for applications in one "
            "or more Solution Descriptors and catalog their Helm values schemas."
        )
    )
    parser.add_argument("solution_descriptors", nargs="+", type=Path)
    parser.add_argument("--appdefs-dir", type=Path)
    parser.add_argument("--regdefs-dir", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR)
    parser.add_argument(
        "--resource-profile",
        help="Download only this profile instead of every profile in the Helm charts.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    try:
        written = generate_catalogs(
            args.solution_descriptors,
            args.output_dir,
            args.cache_dir,
            args.appdefs_dir,
            args.regdefs_dir,
            args.resource_profile,
        )
    except CatalogError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print("Generated catalogs:")
    for path in written:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
