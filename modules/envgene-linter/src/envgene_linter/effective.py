"""Effective Set: staging and dict_merge as in feature/modern-toolset.

Canonical code:
- scripts/build_env/main.py :: prepare_folders_for_rendering
- scripts/build_env/build_env.py :: sort_paramsets_with_same_name
- modules/envgene/envgenehelper/collections_helper.py :: dict_merge
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .model import Category, EnvModel, Layer, ParamsetFile, RepoIndex, Scope
from .yamlio import dotted, leaves, plain

ALL_LAYERS = frozenset(Layer)
LOWER_LAYERS = frozenset({Layer.REPOSITORY, Layer.CLUSTER})
SITE_LAYERS = frozenset({Layer.REPOSITORY})
PARAMETERS_CONTAINER = ("parameters",)


@dataclass(frozen=True)
class Provenance:
    file: ParamsetFile
    reference: str
    container: tuple
    leaf: tuple

    @property
    def layer(self) -> Layer:
        return self.file.layer

    @property
    def yaml_path(self) -> tuple:
        return (*self.container, *self.leaf)

    @property
    def position(self) -> tuple[int, int]:
        if self.file.loaded is None:
            return 1, 1
        return self.file.loaded.position(self.yaml_path)

    def describe(self) -> str:
        return f"{self.file.path}:{self.position[0]} ({self.layer.value}, paramset {self.reference})"


@dataclass(frozen=True)
class EffectiveLeaf:
    path: tuple
    value: Any
    provenance: Provenance

    @property
    def key(self) -> str:
        return dotted(self.path)


@dataclass(frozen=True)
class ResolvedEntry:
    file: ParamsetFile
    reference: str
    tier: int
    staged_path: str


@dataclass
class EnvEffective:
    env: EnvModel
    scopes: dict[Scope, dict[tuple, EffectiveLeaf]] = field(default_factory=dict)

    def get(self, scope: Scope, path: tuple) -> EffectiveLeaf | None:
        return self.scopes.get(scope, {}).get(path)


def dict_merge(a: Any, b: Any) -> Any:
    if not isinstance(a, dict) or not isinstance(b, dict):
        return a if b is None else b
    keys = set(a) | set(b)
    return {key: dict_merge(a.get(key), b.get(key)) for key in keys}


def staged_filename(file: ParamsetFile) -> str:
    name = file.path.name
    if name.endswith(".yml.j2"):
        return name[: -len(".yml.j2")] + ".yml"
    if name.endswith(".yaml.j2"):
        return name[: -len(".yaml.j2")] + ".yml"
    return name


def resolve_reference(
    index: RepoIndex, env: EnvModel, reference: str, layers: frozenset[Layer] = ALL_LAYERS
) -> list[ResolvedEntry]:
    cluster = index.clusters[env.cluster]
    flattened: dict[str, ParamsetFile] = {}
    for file in index.site_paramsets:
        if file.stem == reference and not file.is_jinja and file.layer in layers:
            flattened[staged_filename(file)] = file
    for file in cluster.paramsets:
        if file.stem == reference and not file.is_jinja and file.layer in layers:
            flattened[staged_filename(file)] = file
    entries = [
        ResolvedEntry(file=file, reference=reference, tier=1, staged_path=name)
        for name, file in flattened.items()
    ]
    for file in env.paramsets:
        if file.stem == reference and not file.is_jinja and file.layer in layers:
            entries.append(
                ResolvedEntry(
                    file=file,
                    reference=reference,
                    tier=2,
                    staged_path=f"from_instance/{staged_filename(file)}",
                )
            )
    entries.sort(key=lambda entry: (entry.tier, entry.staged_path))
    return entries


class _Accumulator:
    def __init__(self) -> None:
        self.values: dict[str, Any] = {}
        self.provenance: dict[tuple, Provenance] = {}

    def apply(self, params: dict[str, Any], file: ParamsetFile, reference: str, container: tuple) -> None:
        incoming = plain(params)
        if not isinstance(incoming, dict):
            return
        for key, value in incoming.items():
            current = self.values.get(key)
            self.values[key] = dict_merge(current, value)
            for path, leaf_value in leaves(value, (key,)):
                if leaf_value is None and path in self.provenance:
                    continue
                self.provenance[path] = Provenance(
                    file=file, reference=reference, container=container, leaf=path
                )
        live = {path for path, _ in leaves(self.values)}
        self.provenance = {path: prov for path, prov in self.provenance.items() if path in live}

    def result(self) -> dict[tuple, EffectiveLeaf]:
        out: dict[tuple, EffectiveLeaf] = {}
        for path, value in leaves(self.values):
            prov = self.provenance.get(path)
            if prov is None:
                continue
            out[path] = EffectiveLeaf(path=path, value=value, provenance=prov)
        return out


def compute(index: RepoIndex, env: EnvModel, layers: frozenset[Layer] = ALL_LAYERS) -> EnvEffective:
    result = EnvEffective(env=env)
    accumulators: dict[Scope, _Accumulator] = {}
    for category in Category:
        for target, references in sorted(env.bound_targets(category).items()):
            for reference in references:
                for entry in resolve_reference(index, env, reference):
                    if entry.file.layer not in layers:
                        continue
                    if entry.file.error:
                        continue
                    plain_scope = Scope(target=target, category=category)
                    accumulators.setdefault(plain_scope, _Accumulator()).apply(
                        entry.file.parameters, entry.file, reference, PARAMETERS_CONTAINER
                    )
                    for app_index, app_name, app_params in entry.file.applications:
                        app_scope = Scope(target=target, category=category, application=app_name)
                        container = ("applications", app_index, "parameters")
                        accumulators.setdefault(app_scope, _Accumulator()).apply(
                            app_params, entry.file, reference, container
                        )
    for scope, accumulator in accumulators.items():
        mapping = accumulator.result()
        if mapping:
            result.scopes[scope] = mapping
    return result
