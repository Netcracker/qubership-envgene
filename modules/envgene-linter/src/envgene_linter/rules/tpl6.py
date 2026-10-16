"""TPL-6: keep template logic small."""

from __future__ import annotations

from jinja2 import nodes

from ..ansible_compat import analyze_compatibility
from ..ansible_sources import compatibility_sources
from ..jinja_analysis import TemplateSource
from ..model import Action, Finding, IssueType, RepoIndex, Severity

_FORBIDDEN = (nodes.Macro, nodes.Include, nodes.Import, nodes.FromImport, nodes.Extends, nodes.Block)
_REVIEW = (nodes.Assign, nodes.AssignBlock, nodes.CallBlock, nodes.With,
           nodes.ScopedEvalContextModifier)


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
            hint=('Review whether this logic is needed. Prefer simple template logic.'
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
            elif isinstance(node, nodes.For):
                if _static_iterable(node.iter):
                    add(source, node.lineno, 'for', 'This loop iterates a fixed source instead of a dynamic list.')
                elif node.recursive:
                    add(source, node.lineno, 'for', 'Recursive template iteration needs review.', review=True)
    for source in compatibility_sources(index, sources):
        for line, reason in analyze_compatibility(source).items():
            identity = (source.path.resolve(), line, 'ansible_compatibility')
            findings[identity] = Finding(
                rule='TPL-6', severity=Severity.INFORMATION, issue_type=IssueType.INFORMATION,
                action=Action.REVIEW, path=source.path, line=line, column=1,
                key='ansible_compatibility', scope='templates',
                message=f'Compatibility with the available EnvGene rendering contract needs review. {reason}',
                hint='Verify the source consumer and rendering stage, then use a form supported by that renderer.',
            )
    return sorted(findings.values(), key=lambda f: (f.path.as_posix(), f.line, f.key))
