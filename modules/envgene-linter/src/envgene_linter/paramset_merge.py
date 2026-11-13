"""Plan conservative existing-ParameterSet edits without changing source files."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from .model import Category, Scope
from .security_values import literal_name
from .template_context import ExistingParameterSet, TemplateContext
from .yaml_values import equal


def selector(path: tuple) -> str:
    first, *rest = path
    return str(first) + "".join(
        f"[{part}]"
        if isinstance(part, int)
        else f"[{json.dumps(part, ensure_ascii=False)}]"
        for part in rest
    )


def parameter_payload(scope: Scope, entries: list) -> dict:
    parameters = {}
    for path, value in entries:
        node = parameters
        for part in path[:-1]:
            node = node.setdefault(part, {})
        node[path[-1]] = value
    if scope.application is not None:
        return {
            "applications": [{"appName": scope.application, "parameters": parameters}]
        }
    return {"parameters": parameters}


def _ordinary(value: Any) -> bool:
    pending, seen = [value], set()
    for _ in range(20000):
        if not pending:
            return True
        node = pending.pop()
        if getattr(getattr(node, "tag", None), "value", None) or getattr(
            getattr(node, "anchor", None), "value", None
        ):
            return False
        if isinstance(node, (dict, list)):
            if id(node) in seen:
                return False
            seen.add(id(node))
            if isinstance(node, dict):
                if any(
                    isinstance(key, str)
                    and any(marker in key for marker in ("{{", "{%", "{#", "$" + "{"))
                    for key in node
                ):
                    return False
                pending.extend(node)
                pending.extend(node.values())
            else:
                pending.extend(node)
    return False


def _compare(container: dict, path: tuple, expected: Any) -> str:
    node = container
    for part in path:
        if not isinstance(node, dict):
            return "conflict"
        if part not in node:
            return "add"
        node = node[part]
    pending = [node]
    for _ in range(20000):
        if not pending:
            return "reuse" if equal(node, expected) is True else "conflict"
        item = pending.pop()
        if isinstance(item, str) and any(
            x in item for x in ("{{", "{%", "$" + "{", "{#")
        ):
            return "conflict"
        if isinstance(item, (dict, list)):
            pending.extend(item.values() if isinstance(item, dict) else item)
    return "conflict"


@dataclass
class MergePlan:
    target: ExistingParameterSet
    scope: Scope
    entries: list
    original_binding: bool
    states: dict[tuple, str] = field(default_factory=dict)

    @property
    def accepted(self) -> set[tuple]:
        return {
            path for path, state in self.states.items() if state in {"add", "reuse"}
        }

    @property
    def additions(self) -> list:
        return [
            (path, value)
            for path, value in self.entries
            if self.states.get(path) == "add"
        ]


class MergePlanner:
    def __init__(self, context: TemplateContext):
        self.context = context
        self.claims: dict[tuple, list] = {}

    def propose(
        self, name: str, scope: Scope, entries: list, references: tuple
    ) -> MergePlan | None:
        if scope.category is Category.E2E and scope.application is not None:
            return None
        target = self.context.existing_paramset(name, scope, entries, references)
        if target is None:
            return None
        plan = MergePlan(target, scope, entries, references == (target.reference,))
        if target.reason:
            return plan
        doc = target.loaded.doc
        if (
            not _ordinary(doc)
            or set(doc) - {"name", "version", "parameters", "applications"}
            or not isinstance(doc.get("parameters", {}), dict)
            or not isinstance(doc.get("applications", []), list)
        ):
            target.reason = "The existing ParameterSet has unsupported fields, containers, anchors, or tags."
            return plan
        applications = doc.get("applications", [])
        names = []
        for app in applications:
            if (
                not isinstance(app, dict)
                or set(app) - {"appName", "name", "parameters"}
                or not literal_name(app.get("appName") or app.get("name"))
                or not isinstance(app.get("parameters"), dict)
            ):
                target.reason = (
                    "The existing Application parameters cannot be resolved."
                )
                return plan
            names.append(app.get("appName") or app["name"])
        if len(set(names)) != len(names):
            target.reason = "The existing Application name is ambiguous."
            return plan
        container = doc.get("parameters", {})
        if scope.application is not None:
            container = next(
                (
                    a["parameters"]
                    for a, n in zip(applications, names)
                    if n == scope.application
                ),
                {},
            )
        for path, value in entries:
            plan.states[path] = _compare(container, path, value)
            if target.path.suffix == ".json":
                try:
                    converted = json.loads(json.dumps(value, allow_nan=False))
                    if equal(value, converted) is not True:
                        plan.states[path] = "conflict"
                except (TypeError, ValueError, OverflowError):
                    plan.states[path] = "conflict"
            logical = (scope.application, *path)
            for (file, other), claims in self.claims.items():
                if file != target.path.resolve() or other[0] != logical[0]:
                    continue
                overlap = (
                    other[: len(logical)] == logical or logical[: len(other)] == other
                )
                if overlap and (
                    other != logical
                    or any(equal(v, value) is not True for _, _, v in claims)
                ):
                    plan.states[path] = "conflict"
                    for previous, previous_path, _ in claims:
                        previous.states[previous_path] = "conflict"
            self.claims.setdefault((target.path.resolve(), logical), []).append(
                (plan, path, value)
            )
        return plan
