"""Resolve data-only reference expressions without rendering templates."""

from __future__ import annotations

import math
import re
from typing import Any

from jinja2 import Environment, nodes
from ruamel.yaml.scalarbool import ScalarBoolean

from .parsing import ParseFailure, parse_jinja
from .security_values import is_secret_parameter_name
from .yamlio import LoadedYaml

_PARSER = Environment()
_MARKERS = ("{{", "{%", "{#", "$" + "{")


class UnresolvedReference(ValueError):
    """The selected name cannot be established from ordinary local data."""


def _data_path(expression: nodes.Node) -> tuple[str, ...]:
    parts = []
    for _ in range(16):
        if isinstance(expression, nodes.Name):
            parts.append(expression.name)
            path = tuple(reversed(parts))
            if path[0] != "current_env" or any(
                part.startswith("_") or is_secret_parameter_name(part) for part in path
            ):
                break
            if path[1:] in {("name",), ("environmentName",)} or (
                len(path) >= 3 and path[1] == "cloud_passport"
            ):
                return path
            break
        if isinstance(expression, nodes.Getattr):
            parts.append(expression.attr)
            expression = expression.node
        elif (
            isinstance(expression, nodes.Getitem)
            and isinstance(expression.arg, nodes.Const)
            and isinstance(expression.arg.value, str)
        ):
            parts.append(expression.arg.value)
            expression = expression.node
        else:
            break
    raise UnresolvedReference(
        "Only supported current_env data paths can select ParameterSets."
    )


def resolve_reference_text(reference: str, context: dict[str, Any]) -> str:
    if len(reference) > 4096 or any(marker in reference for marker in _MARKERS[1:]):
        raise UnresolvedReference("The reference contains unsupported template syntax.")
    try:
        ast = parse_jinja(_PARSER, reference)
    except ParseFailure as exc:
        raise UnresolvedReference(
            "The reference expression has invalid syntax."
        ) from exc
    if len(ast.body) != 1 or not isinstance(ast.body[0], nodes.Output):
        raise UnresolvedReference("The reference is not a data-only expression.")
    result = []
    for part in ast.body[0].nodes:
        if isinstance(part, nodes.TemplateData):
            result.append(part.data)
            continue
        path = _data_path(part)
        value = context
        for key in path:
            if (
                not isinstance(value, dict)
                or getattr(getattr(value, "tag", None), "value", None)
                or key not in value
            ):
                raise UnresolvedReference(f"Unavailable input path: {'.'.join(path)}.")
            value = value[key]
        if (
            getattr(getattr(value, "tag", None), "value", None)
            or isinstance(value, (bool, ScalarBoolean))
            or not isinstance(value, (str, int, float))
            or (isinstance(value, float) and not math.isfinite(value))
            or (
                isinstance(value, str)
                and (not value.strip() or any(marker in value for marker in _MARKERS))
            )
        ):
            raise UnresolvedReference(
                f"Input is not an ordinary selector value: {'.'.join(path)}."
            )
        result.append(str(value))
    name = "".join(result)
    if name in {".", ".."} or not re.fullmatch(r"[\w.-]+", name):
        raise UnresolvedReference(
            "The resolved value is not a supported ParameterSet name."
        )
    return name


def unconditional_reference_prefix(loaded: LoadedYaml, text: str, field: str) -> bool:
    """Accept a closed prefix only when later Jinja cannot add reference entries."""
    offset = text.find("{%")
    if offset < 0:
        return True
    if field not in loaded.doc:
        return False
    position = loaded.exact_position((field,))
    if position is None:
        return False
    # A following unconditional root key closes the list before the control flow.
    if not any(
        (other := loaded.exact_position((key,))) is not None and other[0] > position[0]
        for key in loaded.doc
        if key != field
    ):
        return False
    tail = text[offset:]
    # Only standalone, non-trimming statements preserve YAML line boundaries.
    if any(marker in tail for marker in ("{%-", "-%}", "{#-", "-#}")):
        return False
    for statement in re.finditer(r"\{%.*?%\}", tail, re.DOTALL):
        before = tail[tail.rfind("\n", 0, statement.start()) + 1 : statement.start()]
        end = tail.find("\n", statement.end())
        after = tail[statement.end() : end if end >= 0 else len(tail)]
        if before.strip() or after.strip():
            return False
    if re.search(
        r"(?m)^\s*(?:[\"']?" + re.escape(field) + r"[\"']?\s*:|<<\s*:|---|\.\.\.)", tail
    ):
        return False
    try:
        ast = parse_jinja(_PARSER, text)
    except ParseFailure:
        return False
    forbidden = (
        nodes.Include,
        nodes.Extends,
        nodes.Import,
        nodes.FromImport,
        nodes.Macro,
        nodes.Call,
        nodes.CallBlock,
        nodes.Block,
        nodes.Assign,
        nodes.AssignBlock,
        nodes.FilterBlock,
        nodes.Filter,
    )
    first_line = text.count("\n", 0, offset) + 1
    pending, seen = [ast], set()
    for _ in range(20000):
        if not pending:
            return True
        node = pending.pop()
        if id(node) in seen:
            return False
        seen.add(id(node))
        if isinstance(node, forbidden):
            return False
        if isinstance(node, nodes.Output) and any(
            not isinstance(part, nodes.TemplateData) and part.lineno >= first_line
            for part in node.nodes
        ):
            return False
        if isinstance(node, nodes.Output) and any(
            part.lineno >= first_line for part in node.nodes
        ):
            emitted = "".join(
                part.data for part in node.nodes if isinstance(part, nodes.TemplateData)
            )
            # Later output must stay under the already opened unrelated root key.
            # Exclude escaped, explicit, quoted, and comment-spliced root keys too.
            root_indent = position[1] - 1
            if any(
                line.strip()
                and not line.lstrip().startswith("#")
                and len(line) - len(line.lstrip()) <= root_indent
                for line in emitted.splitlines()
            ):
                return False
        pending.extend(node.iter_child_nodes())
    return False
