#!/usr/bin/env python3
"""Build a Helm values-schema catalog from a local deployment descriptor and chart.

This is the catalog-writing half of generate_helm_parameter_catalog.py. It does
not read a Solution Descriptor and does not download artifacts. The descriptor
hash is the sha256 of the local dd.json, stored in the same source list the
full generator uses for Solution Descriptors.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tarfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment-specific message
    raise SystemExit("PyYAML is required.") from exc


CATALOG_SCHEMA_VERSION = 1
GENERATOR_NAME = "build_local_helm_parameter_catalog.py"
HERE = Path(__file__).resolve().parent
DEFAULT_DD = HERE / "dd.json"
DEFAULT_CHART = HERE / "sample-chart-1.0.1.tgz"
DEFAULT_APPDEF = HERE.parent / "appdefs" / "sample-app.yml"
DEFAULT_REGDEF = HERE.parent / "regdefs" / "github-maven.yml"
DEFAULT_OUTPUT_DIR = HERE / "helm-parameter-catalog"


class CatalogError(RuntimeError):
    """Expected input failure."""


@dataclass(frozen=True)
class ApplicationRequest:
    name: str
    version: str
    deploy_postfixes: tuple[str, ...]
    source_descriptors: tuple[Path, ...] = ()

    @property
    def app_version(self) -> str:
        return f"{self.name}:{self.version}"


@dataclass(frozen=True)
class ArtifactCoordinates:
    application: str
    version: str
    group_id: str
    artifact_id: str
    registry_name: str
    repository_domain: str
    repositories: tuple[str, ...]


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


def descriptor_sources(paths: Sequence[Path]) -> list[dict[str, str]]:
    return [
        {
            "path": str(path.resolve()),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        for path in paths
    ]


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
        names = [member.name for member in archive.getmembers() if member.isfile()]
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


def application_from_dd(dd: Mapping[str, Any], dd_path: Path) -> ApplicationRequest:
    metadata = dd.get("metadata")
    name = metadata.get("component") if isinstance(metadata, Mapping) else None
    charts = dd.get("charts")
    version = None
    if isinstance(charts, list):
        for chart in charts:
            if isinstance(chart, Mapping) and chart.get("helm_chart_version"):
                version = str(chart["helm_chart_version"])
                break
    if not name or not version:
        raise CatalogError(
            f"Deployment Descriptor {dd_path} lacks metadata.component or charts[].helm_chart_version"
        )
    if "/" in name or "\\" in name or name in {".", ".."}:
        raise CatalogError(f"Application name is unsafe for an output filename: {name!r}")
    return ApplicationRequest(str(name), version, (), (dd_path,))


def coordinates_from_definitions(
    request: ApplicationRequest, appdef_path: Path, regdef_path: Path
) -> ArtifactCoordinates:
    appdef = load_yaml(appdef_path)
    regdef = load_yaml(regdef_path)
    required = ("name", "registryName", "groupId", "artifactId")
    missing = [key for key in required if not appdef.get(key)]
    if missing:
        raise CatalogError(f"AppDef {appdef_path} lacks: {', '.join(missing)}")
    if appdef["name"] != request.name:
        raise CatalogError(
            f"AppDef name {appdef['name']!r} does not match descriptor component {request.name!r}"
        )
    maven = regdef.get("mavenConfig")
    if not isinstance(maven, Mapping) or not maven.get("repositoryDomainName"):
        raise CatalogError(f"RegDef {regdef_path} lacks mavenConfig.repositoryDomainName")
    repositories = tuple(
        str(maven[key])
        for key in ("targetRelease", "targetStaging", "targetSnapshot")
        if maven.get(key)
    )
    return ArtifactCoordinates(
        application=request.name,
        version=request.version,
        group_id=str(appdef["groupId"]),
        artifact_id=str(appdef["artifactId"]),
        registry_name=str(appdef["registryName"]),
        repository_domain=str(maven["repositoryDomainName"]),
        repositories=repositories,
    )


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
        raise CatalogError(f"No Helm charts given for {request.app_version}")

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
                "repositoryDomain": coordinates.repository_domain,
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


def generate_local_catalog(
    dd_path: Path,
    chart_paths: Sequence[Path],
    appdef_path: Path,
    regdef_path: Path,
    output_dir: Path,
) -> list[Path]:
    for path, label in (
        (dd_path, "Deployment Descriptor"),
        (appdef_path, "AppDef"),
        (regdef_path, "RegDef"),
    ):
        if not path.is_file():
            raise CatalogError(f"{label} does not exist: {path}")
    for chart_path in chart_paths:
        if not chart_path.is_file():
            raise CatalogError(f"Helm chart archive does not exist: {chart_path}")

    dd = decode_json(dd_path.read_bytes(), str(dd_path))
    request = application_from_dd(dd, dd_path)
    coordinates = coordinates_from_definitions(request, appdef_path, regdef_path)
    catalog = build_catalog(request, coordinates, dd_path, chart_paths)
    output_path = output_dir.resolve() / f"{request.name}.yaml"
    write_catalog(catalog, output_path)
    index = {
        "schemaVersion": CATALOG_SCHEMA_VERSION,
        "source": {
            "solutionDescriptors": descriptor_sources(request.source_descriptors),
        },
        "generatedBy": {
            "name": GENERATOR_NAME,
            "catalogSchemaVersion": CATALOG_SCHEMA_VERSION,
        },
        "applications": [
            {
                "name": request.name,
                "version": request.version,
                "appVersion": request.app_version,
                "deployPostfixes": list(request.deploy_postfixes),
                "catalog": output_path.name,
                "supportedParameterCount": len(catalog["supportedParameters"]),
                "unresolvedServiceCount": len(catalog["unresolvedServices"]),
            }
        ],
    }
    index_path = output_dir.resolve() / "index.yaml"
    write_catalog(index, index_path)
    print(
        f"{request.app_version}: {len(catalog['supportedParameters'])} parameters, "
        f"{len(catalog['services'])} schemas, {len(catalog['unresolvedServices'])} unresolved services"
    )
    return [output_path, index_path]


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Catalog Helm values schemas from a local deployment descriptor and chart archive."
        )
    )
    parser.add_argument("--dd", type=Path, default=DEFAULT_DD)
    parser.add_argument("--chart", type=Path, action="append", dest="charts")
    parser.add_argument("--appdef", type=Path, default=DEFAULT_APPDEF)
    parser.add_argument("--regdef", type=Path, default=DEFAULT_REGDEF)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    charts = args.charts or [DEFAULT_CHART]
    try:
        written = generate_local_catalog(
            args.dd.resolve(),
            [path.resolve() for path in charts],
            args.appdef.resolve(),
            args.regdef.resolve(),
            args.output_dir,
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
