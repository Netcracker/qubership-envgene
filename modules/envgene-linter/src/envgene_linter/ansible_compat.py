"""Statically check expressions against known renderer compatibility contracts."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from jinja2 import Environment, TemplateSyntaxError, nodes

from .parsing import ParseFailure, parse_jinja

ENVIRONMENT = Environment()
CUSTOM_FILTERS = {'to_nice_yaml', 'urlsplit'}
LEGACY_CALLS = {'lookup', 'query', 'q'}

# Keep these in the same order and form as replace_ansible_stuff.REPLACEMENTS.
# Importing that module would load EnvGene and its runtime dependencies.
REPLACEMENTS = (
    (re.compile(r'(\|\s*)ansible\.builtin\.to_nice_yaml(\s*(?:\([^)]*\))?)'),
     r'\1to_nice_yaml\2', 'filter'),
    (re.compile(r"lookup\(\s*'ansible\.builtin\.env'\s*,\s*'([^']+)'\s*\)"),
     r'env_vars.\1', 'lookup'),
    (re.compile(r'{{\s*_(\w+)\s*}}'), r'{{ \1 }}', 'underscore'),
)


@dataclass
class CompatibilitySource:
    path: Path
    text: str = field(repr=False)
    rendering: str
    offset: int = 0
    descriptor: bool = False


def _lexical_spans(text: str) -> list[tuple[int, int, str]]:
    """Locate original lexer tokens, including raw data and quoted strings."""
    spans = []
    cursor = 0
    try:
        for _, kind, value in ENVIRONMENT.lex(text):
            # Whitespace control can omit characters between emitted tokens.
            start = text.find(value, cursor)
            if start < 0:
                break
            end = start + len(value)
            spans.append((start, end, kind))
            cursor = end
    except (TemplateSyntaxError, ValueError, RecursionError):
        # Parsing below reports the failure without exposing the exception.
        pass
    return spans


def _rewrite(text: str, review) -> str:
    for pattern, replacement, kind in REPLACEMENTS:
        spans = _lexical_spans(text)

        def replace(match: re.Match) -> str:
            start, end = match.span()
            overlapping = [(left, right, token) for left, right, token in spans
                           if left < end and right > start]
            in_comment = overlapping and all(token.startswith('comment')
                                             for _, _, token in overlapping)
            if not in_comment:
                containing = next(((left, token) for left, right, token in overlapping
                                   if left <= start < right), None)
                literal = containing is None or containing[1] in {'data', 'string'}
                if literal:
                    review(text.count('\n', 0, start) + 1,
                           'Compatibility processing changes literal template content.')
                elif kind == 'lookup':
                    # The regex also matches method calls and name suffixes, and
                    # nonidentifiers become attribute/arithmetic expressions.
                    if (containing != (start, 'name') or text[:start].rstrip().endswith('.')
                            or not match.group(1).isidentifier()):
                        review(text.count('\n', 0, start) + 1,
                               'Compatibility processing cannot confirm the lookup form.')

            rewritten = match.expand(replacement)
            # Keep following AST and parser positions in original source lines.
            return rewritten + '\n' * (match.group().count('\n') - rewritten.count('\n'))

        text = pattern.sub(replace, text)
    return text


def _call_name(node: nodes.Node) -> str:
    parts = []
    while isinstance(node, (nodes.Getattr, nodes.Getitem)):
        if isinstance(node, nodes.Getattr):
            parts.append(node.attr)
        elif isinstance(node.arg, nodes.Const) and isinstance(node.arg.value, str):
            parts.append(node.arg.value)
        else:
            return ''
        node = node.node
    if isinstance(node, nodes.Name):
        return '.'.join([node.name, *reversed(parts)])
    return ''


def _custom_arguments_supported(node: nodes.Filter) -> bool:
    if node.dyn_args is not None or node.dyn_kwargs is not None:
        return False
    if node.name == 'to_nice_yaml':
        return not node.args and not node.kwargs
    if (len(node.args) + len(node.kwargs) > 1
            or any(argument.key != 'part' for argument in node.kwargs)):
        return False
    arguments = node.args + [argument.value for argument in node.kwargs]
    if arguments:
        part = arguments[0]
        # urlsplit passes truthy part values to getattr, which requires a string.
        # Check evident literals only; do not evaluate arbitrary expressions.
        if isinstance(part, nodes.Const):
            return not part.value or isinstance(part.value, str)
        if (isinstance(part, (nodes.Neg, nodes.Pos)) and isinstance(part.node, nodes.Const)
                and isinstance(part.node.value, (int, float))):
            return not part.node.value
        if isinstance(part, (nodes.List, nodes.Tuple, nodes.Dict)):
            return not part.items
    return True


def analyze_compatibility(source: CompatibilitySource, *, on_error=None) -> dict[int, str]:
    """Return generic Review reasons without compiling or executing the source."""
    findings: dict[int, str] = {}

    def review(line: int, reason: str) -> None:
        original = source.offset + (1 if source.descriptor else max(1, line))
        findings.setdefault(original, reason)

    text = source.text.replace('\r\n', '\n').replace('\r', '\n')
    if source.rendering == 'envgene':
        text = _rewrite(text, review)
    try:
        tree = parse_jinja(ENVIRONMENT, text)
    except ParseFailure as exc:
        if on_error is not None:
            original = source.offset + (1 if source.descriptor else exc.line)
            on_error(exc.reason, original)
            return findings
        review(exc.line, 'Cannot confirm compatibility because Jinja syntax cannot be parsed.')
        return findings

    known_custom = source.rendering in {'envgene', 'custom_jinja'}
    uncertain = source.rendering not in {'envgene', 'custom_jinja', 'jinja'}
    pending = [tree]
    while pending:
        node = pending.pop()
        pending.extend(reversed(list(node.iter_child_nodes())))
        if isinstance(node, nodes.Filter):
            if node.name in ENVIRONMENT.filters:
                continue
            if known_custom and node.name in CUSTOM_FILTERS:
                if not _custom_arguments_supported(node):
                    review(node.lineno, 'Filter arguments are unsupported or cannot be confirmed statically.')
            elif uncertain:
                review(node.lineno, 'Filter compatibility is unconfirmed for the unknown rendering contract.')
            else:
                review(node.lineno, 'Filter availability is unsupported by the known rendering contract.')

        elif isinstance(node, nodes.Call):
            name = _call_name(node.node)
            if name in LEGACY_CALLS or name.startswith('ansible.'):
                if uncertain:
                    review(node.lineno, 'Legacy call compatibility is unconfirmed for the unknown rendering contract.')
                else:
                    review(node.lineno, 'Legacy call is unsupported by the known rendering contract.')
    return findings
