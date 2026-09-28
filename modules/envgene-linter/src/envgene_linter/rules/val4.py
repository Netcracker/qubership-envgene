"""VAL-4: review serialized collections in connected ParameterSet values."""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError
from ruamel.yaml.nodes import MappingNode, SequenceNode
from ruamel.yaml.scalarstring import FoldedScalarString, LiteralScalarString
from ruamel.yaml.tokens import (
    AliasToken, AnchorToken, BlockEndToken, BlockMappingStartToken, BlockSequenceStartToken,
    DirectiveToken, FlowMappingEndToken, FlowMappingStartToken, FlowSequenceEndToken,
    FlowSequenceStartToken, TagToken,
)

from ..connections import Connections, compute_connections
from ..model import Finding, RepoIndex, Severity
from ..parameter_objects import safe_parameter_path
from ..rulemeta import RULES
from ..yamlio import dotted

_MAX_CHARS = 65_536
_MAX_DEPTH = 64
_MAX_TOKENS = 4_096
_MAX_VISITS = 65_536
_START = (BlockMappingStartToken, BlockSequenceStartToken, FlowMappingStartToken, FlowSequenceStartToken)
_END = (BlockEndToken, FlowMappingEndToken, FlowSequenceEndToken)
_UNSUPPORTED = (AliasToken, AnchorToken, TagToken, DirectiveToken)


class _LimitReached(Exception):
    """A bounded recognition pass cannot inspect this input."""


def _strings(value: Any, prefix: tuple = ()) -> Iterator[tuple[tuple, str | None]]:
    stack = [(value, prefix, frozenset(), 0)]
    visits = 0
    while stack:
        current, path, ancestors, depth = stack.pop()
        visits += 1
        if visits > _MAX_VISITS:
            yield path, None
            return
        if isinstance(current, str):
            yield path, current
        elif isinstance(current, (dict, list)):
            if id(current) in ancestors:
                continue
            if depth >= _MAX_DEPTH:
                yield path, None
                continue
            ancestors = ancestors | {id(current)}
            items = current.items() if isinstance(current, dict) else enumerate(current)
            stack.extend((child, (*path, key), ancestors, depth + 1) for key, child in items)


def _reject_constant(_value: str) -> None:
    raise ValueError('Nonstandard JSON constant')


def _encoded_kind(value: str) -> str | None:
    block = isinstance(value, (LiteralScalarString, FoldedScalarString))
    if any(marker in value for marker in ('${', '{{', '{%', '{#')):
        return None
    text = value.strip()
    json_like = text.startswith(('{', '['))
    if not text or not (block or json_like):
        return None
    if len(value) > _MAX_CHARS:
        raise _LimitReached
    try:
        if json_like:
            try:
                decoded = json.loads(text, parse_constant=_reject_constant)
            except ValueError:
                if not block:
                    return None
            else:
                # Traverse without recursion to enforce a consistent collection-depth limit.
                for _path, child in _strings(decoded):
                    if child is None:
                        raise _LimitReached
                return 'JSON map' if isinstance(decoded, dict) else 'JSON list'
        parser = YAML(typ='safe', pure=True)
        depth = 0
        for count, token in enumerate(parser.scan(text), 1):
            if count > _MAX_TOKENS:
                raise _LimitReached
            if isinstance(token, _UNSUPPORTED):
                return None
            if isinstance(token, _START):
                depth += 1
                if depth > _MAX_DEPTH:
                    raise _LimitReached
            elif isinstance(token, _END):
                depth -= 1
        node = YAML(typ='safe', pure=True).compose(text)
        # Scanner tokens omit indentless sequence starts. Check the actual tree too.
        pending = [(node, 0)]
        while pending:
            current, depth = pending.pop()
            if isinstance(current, (MappingNode, SequenceNode)):
                if depth >= _MAX_DEPTH:
                    raise _LimitReached
                children = (child for pair in current.value for child in pair) if isinstance(
                    current, MappingNode) else iter(current.value)
                pending.extend((child, depth + 1) for child in children)
        if isinstance(node, MappingNode):
            return 'YAML map'
        if isinstance(node, SequenceNode):
            return 'YAML list'
    except RecursionError:
        raise _LimitReached from None
    except (YAMLError, ValueError):
        return None
    return None


def check(index: RepoIndex, connections: Connections | None = None) -> list[Finding]:
    connections = connections if connections is not None else compute_connections(index)
    meta = RULES['VAL-4']
    findings = []
    for physical, file in sorted(connections.parameter_files.items()):
        if file.is_jinja or file.error or file.loaded is None or not safe_parameter_path(index, file.path):
            continue
        scope = ', '.join(sorted({use.environment for use in connections.parameter_uses.get(physical, ())}))
        bags = [(('parameters',), file.parameters)]
        bags.extend((('applications', app_index, 'parameters'), params)
                    for app_index, _name, params in file.applications)
        limited = False
        for prefix, bag in bags:
            for path, value in _strings(bag, prefix):
                if value is None:
                    limited = True
                    continue
                try:
                    kind = _encoded_kind(value)
                except _LimitReached:
                    limited = True
                    continue
                if kind is None:
                    continue
                line, column = file.loaded.position(path)
                findings.append(Finding(
                    rule=meta.id, severity=Severity.WARNING,
                    issue_type=meta.default_issue_type, action=meta.default_action,
                    path=file.path, line=line, column=column, key=dotted(path), scope=scope,
                    message=f'Parameter value contains a {kind} encoded as a string.',
                    hint='Review the consumer contract. Use a native YAML map or list if the consumer accepts '
                         'structured values; retain the string if serialization is required.',
                ))
        if limited:
            note = f'VAL-4: analysis limit reached for ParameterSet: {file.path.relative_to(index.root)}'
            if note not in index.skipped:
                index.skipped.append(note)
    return sorted(findings, key=lambda item: (item.path.as_posix(), item.line, item.column, item.key))
