"""Instance-repository types. No I/O, no merge."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .yamlio import LoadedYaml


class Layer(Enum):
    REPOSITORY = "repository"
    CLUSTER = "cluster"
    ENVIRONMENT = "environment"


class Category(Enum):
    DEPLOY = "deploy"
    E2E = "e2e"
    TECHNICAL = "technical"

    @property
    def binding_field(self) -> str:
        return {
            "deploy": "envSpecificParamsets",
            "e2e": "envSpecificE2EParamsets",
            "technical": "envSpecificTechnicalParamsets",
        }[self.value]


class Severity(Enum):
    WARNING = "warning"
    INFORMATION = "information"


class IssueType(Enum):
    ERROR = "Error"
    WARNING = "Warning"
    INFORMATION = "Information"


class Action(Enum):
    FIX = "Fix"
    REVIEW = "Review"


@dataclass(frozen=True)
class Scope:
    target: str
    category: Category
    application: str | None = None

    def __str__(self) -> str:
        base = f"{self.target}/{self.category.value}"
        return f"{base}/{self.application}" if self.application else base


@dataclass
class ParamsetFile:
    path: Path
    layer: Layer
    stem: str
    cluster: str | None = None
    env: str | None = None
    is_jinja: bool = False
    loaded: LoadedYaml | None = None
    error: str | None = None

    @property
    def parameters(self) -> dict[str, Any]:
        if self.loaded is None or not isinstance(self.loaded.doc, dict):
            return {}
        value = self.loaded.doc.get("parameters")
        return value if isinstance(value, dict) else {}

    @property
    def applications(self) -> list[tuple[int, str, dict[str, Any]]]:
        if self.loaded is None or not isinstance(self.loaded.doc, dict):
            return []
        entries = self.loaded.doc.get("applications")
        if not isinstance(entries, list):
            return []
        out: list[tuple[int, str, dict[str, Any]]] = []
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                continue
            app_name = entry.get("appName") or entry.get("name")
            params = entry.get("parameters")
            if app_name and isinstance(params, dict):
                out.append((index, str(app_name), params))
        return out


@dataclass
class PassportFile:
    path: Path
    stem: str
    cluster: str | None = None
    env: str | None = None
    is_jinja: bool = False
    loaded: LoadedYaml | None = None
    error: str | None = None

    @property
    def on_cluster(self) -> bool:
        return self.cluster is not None and self.env is None


@dataclass
class NamedEntityFile:
    path: Path
    stem: str
    kind: str
    is_jinja: bool = False
    loaded: LoadedYaml | None = None
    error: str | None = None
    aliases: tuple[Path, ...] = ()


@dataclass
class EnvModel:
    cluster: str
    name: str
    path: Path
    paramsets: list[ParamsetFile] = field(default_factory=list)
    bindings: dict[Category, dict[str, list[str]]] = field(default_factory=dict)
    cloud_passport: str | None = None
    resource_profile_bindings: dict[str, str] = field(default_factory=dict)
    shared_credential_bindings: list[str] = field(default_factory=list)
    artifact_selectors: tuple[str, ...] = ()
    shared_template_variable_bindings: list[str] = field(default_factory=list)

    @property
    def full_name(self) -> str:
        return f"{self.cluster}/{self.name}"

    def bound_targets(self, category: Category) -> dict[str, list[str]]:
        return self.bindings.get(category, {})


@dataclass
class ClusterModel:
    name: str
    path: Path
    environments: list[EnvModel] = field(default_factory=list)
    paramsets: list[ParamsetFile] = field(default_factory=list)


@dataclass
class RepoIndex:
    root: Path
    site_paramsets: list[ParamsetFile] = field(default_factory=list)
    clusters: dict[str, ClusterModel] = field(default_factory=dict)
    passports: list[PassportFile] = field(default_factory=list)
    named_entities: list[NamedEntityFile] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    resource_profiles: list[NamedEntityFile] = field(default_factory=list)
    credential_files: list[NamedEntityFile] = field(default_factory=list)

    @property
    def environments(self) -> list[EnvModel]:
        return [env for cluster in self.clusters.values() for env in cluster.environments]


@dataclass(frozen=True)
class Location:
    path: Path
    line: int
    column: int


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: Severity
    path: Path
    line: int
    key: str
    scope: str
    message: str
    hint: str
    related: tuple[str, ...] = ()
    column: int = 1
    issue_type: IssueType = IssueType.WARNING
    action: Action = Action.FIX
    locations: tuple[Location, ...] = ()

    def file_locations(self) -> tuple[Location, ...]:
        if self.locations:
            return self.locations
        return (Location(self.path, self.line, self.column),)
