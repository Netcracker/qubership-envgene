"""TPL-6: keep template logic small."""

from __future__ import annotations

import re

from jinja2 import nodes

from ..jinja_analysis import ENVIRONMENT, TemplateSource
from ..model import Action, Finding, IssueType, RepoIndex, Severity

_FORBIDDEN = (nodes.Macro, nodes.Include, nodes.Import, nodes.FromImport, nodes.Extends, nodes.Block)
_REVIEW = (nodes.Assign, nodes.AssignBlock, nodes.CallBlock, nodes.FilterBlock, nodes.With,
           nodes.ScopedEvalContextModifier)
_FILTERS = {'default', 'd', 'join', 'upper', 'lower'}
_HELM_ROOT = re.compile(r'(?<![\w.])\.(?:Values|Release|Chart|Capabilities|Files|Template|Subcharts)\b')
_QUOTED = re.compile(r'''"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|`[^`]*`''')


def _helm_passthrough(text: str) -> bool:
    if '{%' in text or '{#' in text:
        return False
    expressions = re.findall(r'{{-?\s*(.*?)\s*-?}}', text, re.DOTALL)
    if not expressions or text.count('{{') != len(expressions):
        return False
    evidence = False
    for expression in expressions:
        body = _QUOTED.sub('', expression).strip()
        helm_include = re.match(r'^include\s+"(?:\\.|[^"\\])*"\s+(?:\.|\$)[\w.]*\s*(?:\||$)', expression.strip())
        if _HELM_ROOT.search(body) or helm_include:
            evidence = True
        elif not (re.fullmatch(r'(?:else|end|else\s+if\s+\$[\w.]+)', body)
                  or re.match(r'^(?:(?:if|range|with)\s+)?\$[\w.]+', body)
                  or (body.startswith('/*') and body.endswith('*/'))):
            return False
    return evidence


def _static_iterable(node: nodes.Node) -> bool:
    if isinstance(node, (nodes.List, nodes.Tuple, nodes.Dict, nodes.Const)):
        return True
    return (isinstance(node, nodes.Call) and isinstance(node.node, nodes.Name)
            and node.node.name == 'range' and bool(node.args)
            and all(isinstance(arg, nodes.Const) for arg in node.args)
            and not node.kwargs and node.dyn_args is None and node.dyn_kwargs is None)


def check(index: RepoIndex, sources: list[TemplateSource]) -> list[Finding]:
    findings = {}

    def add(source, line, key, message, review=False):
        line = source.source_line(line)
        identity = (source.path.resolve(), line, key)
        previous = findings.get(identity)
        if previous is not None and (previous.action == Action.FIX or review):
            return
        findings[identity] = Finding(
            rule='TPL-6', severity=Severity.INFORMATION if review else Severity.WARNING,
            issue_type=IssueType.INFORMATION if review else IssueType.WARNING,
            action=Action.REVIEW if review else Action.FIX,
            path=source.path, line=line, column=1, key=key, scope='templates', message=message,
            hint=('Review whether this logic is needed. Keep Helm passthrough protected and prefer simple template logic.'
                  if review else 'Use template composition or explicit values to keep template logic small.'),
        )

    for source in sources:
        pending = [source.tree]
        while pending:
            node = pending.pop()
            pending.extend(reversed(list(node.iter_child_nodes())))
            if isinstance(node, _FORBIDDEN):
                add(source, node.lineno, type(node).__name__.lower(),
                    'This Jinja statement is prohibited by TPL-6.')
            elif isinstance(node, _REVIEW):
                add(source, node.lineno, 'statement',
                    'This Jinja statement is outside the simple logic described by TPL-6.', review=True)
            elif isinstance(node, nodes.Filter) and node.name not in _FILTERS:
                builtin = node.name in ENVIRONMENT.filters
                add(source, node.lineno, 'filter',
                    'This built-in filter is outside the subset described by TPL-6.' if builtin else
                    'A custom Jinja filter is prohibited by TPL-6.', review=builtin)
            elif isinstance(node, nodes.For):
                if _static_iterable(node.iter):
                    add(source, node.lineno, 'for', 'This loop iterates a fixed source instead of a dynamic list.')
                elif node.recursive:
                    add(source, node.lineno, 'for', 'Recursive template iteration needs review.', review=True)
        for line, body in source.raw_blocks:
            if not _helm_passthrough(body):
                add(source, line, 'raw',
                    'This raw block cannot be confirmed as Helm passthrough from the available source.', review=True)
    return sorted(findings.values(), key=lambda f: (f.path.as_posix(), f.line, f.key))
