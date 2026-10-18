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
from .paramset_sources import ALL_LAYERS, resolve_reference
from .yamlio import dotted, leaves, plain

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


class _Accumulator:
    def __init__(self) -> None:
        self.values: dict[str, Any] = {}
        self.provenance: dict[tuple, Provenance] = {}

    def apply(
        self, params: dict[str, Any], file: ParamsetFile, reference: str, container: tuple,
        omission: Provenance | None = None,
    ) -> None:
        incoming = plain(params)
        if not isinstance(incoming, dict):
            return
        if (omission is not None and file.path.resolve() == omission.file.path.resolve()
                and container == omission.container):
            # plain() creates the analysis copy. Keep source records and files intact.
            parent = incoming
            for key in omission.leaf[:-1]:
                parent = parent[key]
            del parent[omission.leaf[-1]]
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


def _accumulate(
    index: RepoIndex, env: EnvModel, layers: frozenset[Layer], omission: Provenance | None = None,
) -> dict[Scope, _Accumulator]:
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
                        entry.file.parameters, entry.file, reference, PARAMETERS_CONTAINER, omission
                    )
                    for app_index, app_name, app_params in entry.file.applications:
                        app_scope = Scope(target=target, category=category, application=app_name)
                        container = ("applications", app_index, "parameters")
                        accumulators.setdefault(app_scope, _Accumulator()).apply(
                            app_params, entry.file, reference, container, omission
                        )
    return accumulators


def compute_values(index: RepoIndex, env: EnvModel, omission: Provenance | None = None) -> dict[Scope, dict]:
    """Compute complete parameter bags, optionally excluding one physical source occurrence."""
    return {scope: accumulator.values
            for scope, accumulator in _accumulate(index, env, ALL_LAYERS, omission).items()}


def compute(index: RepoIndex, env: EnvModel, layers: frozenset[Layer] = ALL_LAYERS) -> EnvEffective:
    result = EnvEffective(env=env)
    accumulators = _accumulate(index, env, layers)
    for scope, accumulator in accumulators.items():
        mapping = accumulator.result()
        if mapping:
            result.scopes[scope] = mapping
    return result
