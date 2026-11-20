"""Prove individual ParameterSet removals against known local consumers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .effective import Provenance, compute_values
from .model import Category, EnvModel, RepoIndex, Scope
from .paramset_sources import reference_complete, resolve_reference, source_files
from .yaml_values import equal


def _literal_name(value: Any) -> bool:
    return (
        isinstance(value, str) and bool(value.strip())
        and not any(mark in value for mark in ("${", "{{", "{%", "{#"))
    )


def _supported(document: Any) -> bool:
    """Aliases, merge keys, and unsupported values require source-aware review."""
    pending, seen = [document], set()
    for _ in range(20000):
        if not pending:
            return True
        node = pending.pop()
        if getattr(node, "_yaml_anchor", None) or getattr(node, "_yaml_merge", None):
            return False
        if getattr(getattr(node, "tag", None), "value", None) is not None:
            return False
        if isinstance(node, (dict, list)):
            if id(node) in seen:
                return False
            seen.add(id(node))
            if isinstance(node, dict):
                pending.extend(child for pair in node.items() for child in pair)
            else:
                pending.extend(node)
        elif equal(node, node) is not True:
            return False
    return False


class RemovalAnalysis:
    def __init__(self, index: RepoIndex):
        self.index = index
        self.environments = {env.full_name: env for env in index.environments}
        self.consumers: dict[Path, dict[str, set[tuple[Category, str]]]] = {}
        self.uncertain_consumers: set[Path] = set()
        self.before: dict[str, dict[Scope, dict]] = {}
        self.results: dict[tuple[Path, tuple], bool | None] = {}
        self.documents: dict[Path, bool] = {}
        self.complete: dict[tuple[str, Category, str], bool] = {}
        unreadable = {problem.path.resolve() for problem in index.read_problems}
        for env in index.environments:
            if (env.path / 'Inventory/env_definition.yml').resolve() in unreadable:
                # Unknown bindings can use any source in this environment's applicable layers.
                self.uncertain_consumers.update(file.path.resolve() for file in source_files(index, env)
                                                if not file.unavailable)
            for category in Category:
                for target, references in env.bound_targets(category).items():
                    for reference in references:
                        if not reference_complete(index, env, reference):
                            self.uncertain_consumers.update(
                                file.path.resolve() for file in source_files(index, env)
                                if file.stem == reference and not file.unavailable
                            )
                        for entry in resolve_reference(index, env, reference):
                            uses = self.consumers.setdefault(entry.file.path.resolve(), {})
                            uses.setdefault(env.full_name, set()).add((category, target))

    def _complete(self, env: EnvModel, category: Category, target: str) -> bool:
        identity = (env.full_name, category, target)
        if identity in self.complete:
            return self.complete[identity]
        complete = True
        for reference in env.bound_targets(category)[target]:
            entries = resolve_reference(self.index, env, reference, include_unavailable=True)
            if (
                not entries or not _literal_name(reference) or not reference_complete(self.index, env, reference)
                or any(entry.file.is_jinja or entry.file.unavailable for entry in entries)
            ):
                complete = False
                break
            for entry in entries:
                file = entry.file
                physical = file.path.resolve()
                if physical not in self.documents:
                    doc = file.loaded.doc if file.loaded is not None else None
                    supported = not file.error and isinstance(doc, dict) and _supported(doc)
                    if supported:
                        params, apps = doc.get("parameters"), doc.get("applications")
                        supported = (
                            (params is None or isinstance(params, dict))
                            and (apps is None or isinstance(apps, list))
                        )
                        if isinstance(apps, list):
                            supported &= all(
                                isinstance(app, dict)
                                and _literal_name(app.get("appName") or app.get("name"))
                                and (app.get("parameters") is None or isinstance(app.get("parameters"), dict))
                                for app in apps
                            )
                    self.documents[physical] = bool(supported)
                if not self.documents[physical]:
                    complete = False
        self.complete[identity] = complete
        return complete

    def preserves(self, source: Provenance) -> bool | None:
        """True proves preservation, False disproves it, None requires Review."""
        physical = source.file.path.resolve()
        identity = (physical, source.yaml_path)
        if identity not in self.results:
            self.results[identity] = self._preserves(source, self.consumers.get(physical, {}))
        return self.results[identity]

    def _preserves(self, source: Provenance, consumers: dict[str, set[tuple[Category, str]]]) -> bool | None:
        uncertain = not consumers or source.file.path.resolve() in self.uncertain_consumers
        for name, targets in consumers.items():
            env = self.environments[name]
            if not all(self._complete(env, category, target) for category, target in targets):
                uncertain = True
                continue
            try:
                if name not in self.before:
                    self.before[name] = compute_values(self.index, env)
                before = self.before[name]
                after = compute_values(self.index, env, source)
                if before.keys() != after.keys():
                    return False
                for scope, values in before.items():
                    comparison = equal(values, after[scope])
                    if comparison is False:
                        return False
                    uncertain |= comparison is None
            except (RecursionError, ValueError, TypeError, KeyError, IndexError):
                uncertain = True
        return None if uncertain else True
