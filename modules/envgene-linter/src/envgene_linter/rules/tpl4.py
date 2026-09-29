"""TPL-4: review references without recognized presence protection."""

from __future__ import annotations

from jinja2 import nodes

from ..jinja_analysis import ENVIRONMENT, TemplateSource
from ..model import Action, Finding, IssueType, RepoIndex, Severity

_REFERENCES = (nodes.Name, nodes.Getattr, nodes.Getitem)
_GUARANTEED = {('current_env',), ('current_env', 'name'), ('current_env', 'environmentName')}
_LOOP_PROPERTIES = {'index', 'index0', 'revindex', 'revindex0', 'first', 'last', 'length',
                    'depth', 'depth0', 'cycle', 'changed'}


def _path(node):
    if isinstance(node, nodes.Name):
        return (node.name,)
    if isinstance(node, nodes.Getattr):
        parent = _path(node.node)
        return (*parent, node.attr) if parent else None
    if isinstance(node, nodes.Getitem) and isinstance(node.arg, nodes.Const):
        if isinstance(node.arg.value, (str, int)):
            parent = _path(node.node)
            return (*parent, node.arg.value) if parent else None
    return None


def _facts(node, truth=True):
    if isinstance(node, nodes.Test) and node.name in ('defined', 'undefined'):
        path = _path(node.node)
        return {path} if path and truth == (node.name == 'defined') else set()
    if isinstance(node, nodes.Not):
        return _facts(node.node, not truth)
    if isinstance(node, (nodes.And, nodes.Or)):
        left, right = _facts(node.left, truth), _facts(node.right, truth)
        return left | right if truth == isinstance(node, nodes.And) else left & right
    return set()


def _targets(node):
    if isinstance(node, nodes.Name):
        return {node.name}
    if isinstance(node, nodes.Tuple):
        return set().union(*(_targets(item) for item in node.items))
    return set()


def _writes(node):
    if isinstance(node, (nodes.Assign, nodes.AssignBlock)):
        return _targets(node.target)
    if isinstance(node, nodes.Macro):
        return {node.name}
    if isinstance(node, nodes.Import):
        return {node.target}
    if isinstance(node, nodes.FromImport):
        return {name[-1] if isinstance(name, tuple) else name for name in node.names}
    if isinstance(node, nodes.If):
        return set().union(*(_writes(child) for child in [*node.body, *node.elif_, *node.else_]))
    return set()


def _bind(bound, names):
    return (bound - {'@loop'} if 'loop' in names else bound) | names


class _References:
    def __init__(self, descriptor):
        self.lines = set()
        self.guaranteed = _GUARANTEED | ({('templates_dir',)} if descriptor else set())

    def sequence(self, body, bound, guards):
        bound, guards = set(bound), set(guards)
        for node in body:
            self.visit(node, bound, guards)
            names = _writes(node)
            # An if shares its enclosing scope but does not guarantee that every branch assigns a name.
            known = bound | ENVIRONMENT.globals.keys() | {path[0] for path in self.guaranteed}
            bound.update(names & known if isinstance(node, nodes.If) else names)
            if 'loop' in names:
                bound.discard('@loop')
            guards = {path for path in guards if path[0] not in names}

    def reference(self, node, bound, guards, protected=False):
        path = _path(node)
        known = (path in guards or (path in self.guaranteed and path[0] not in bound)
                 or (path and len(path) == 1 and path[0] in bound | ENVIRONMENT.globals.keys())
                 or (path and len(path) == 2 and path[0] == 'loop' and '@loop' in bound
                     and path[1] in _LOOP_PROPERTIES))
        if not protected and not known:
            self.lines.add(node.lineno)
        # Dynamic index expressions are evaluated even when the selected value has a default.
        current = node
        while isinstance(current, (nodes.Getattr, nodes.Getitem)):
            if isinstance(current, nodes.Getitem):
                self.visit(current.arg, bound, guards)
            current = current.node
        if not isinstance(current, nodes.Name):
            self.visit(current, bound, guards)

    def visit(self, node, bound, guards):
        if node is None:
            return
        if isinstance(node, _REFERENCES):
            if getattr(node, 'ctx', 'load') == 'load':
                self.reference(node, bound, guards)
        elif isinstance(node, nodes.Filter) and node.name in ('default', 'd'):
            if isinstance(node.node, _REFERENCES):
                self.reference(node.node, bound, guards, protected=True)
            else:
                self.visit(node.node, bound, guards)
            for child in [*node.args, *node.kwargs, node.dyn_args, node.dyn_kwargs]:
                self.visit(child, bound, guards)
        elif isinstance(node, nodes.Test) and node.name in ('defined', 'undefined'):
            if isinstance(node.node, _REFERENCES):
                self.reference(node.node, bound, guards, protected=True)
            else:
                self.visit(node.node, bound, guards)
        elif isinstance(node, (nodes.And, nodes.Or)):
            self.visit(node.left, bound, guards)
            self.visit(node.right, bound, guards | _facts(node.left, isinstance(node, nodes.And)))
        elif isinstance(node, nodes.If):
            remaining = set(guards)
            for branch in [node, *node.elif_]:
                self.visit(branch.test, bound, remaining)
                self.sequence(branch.body, bound, remaining | _facts(branch.test))
                remaining |= _facts(branch.test, False)
            self.sequence(node.else_, bound, remaining)
        elif isinstance(node, nodes.CondExpr):
            self.visit(node.test, bound, guards)
            self.visit(node.expr1, bound, guards | _facts(node.test))
            self.visit(node.expr2, bound, guards | _facts(node.test, False))
        elif isinstance(node, nodes.For):
            self.visit(node.iter, bound, guards)
            names = _targets(node.target)
            inner = _bind(bound, names)
            scoped = {path for path in guards if path[0] not in names}
            self.visit(node.test, inner, scoped)
            self.sequence(node.body, inner | {'loop', '@loop'}, scoped | _facts(node.test))
            self.sequence(node.else_, bound, guards)
        elif isinstance(node, nodes.Assign):
            self.visit(node.node, bound, guards)
        elif isinstance(node, nodes.Macro):
            for default in node.defaults:
                self.visit(default, bound, guards)
            names = {arg.name for arg in node.args} | {'caller', 'kwargs', 'varargs', node.name}
            self.sequence(node.body, _bind(bound, names), {path for path in guards if path[0] not in names})
        elif isinstance(node, nodes.With):
            for value in node.values:
                self.visit(value, bound, guards)
            names = set().union(*(_targets(target) for target in node.targets))
            self.sequence(node.body, _bind(bound, names), {path for path in guards if path[0] not in names})
        elif isinstance(node, nodes.CallBlock):
            self.visit(node.call, bound, guards)
            for default in node.defaults:
                self.visit(default, bound, guards)
            names = {arg.name for arg in node.args}
            self.sequence(node.body, _bind(bound, names), {path for path in guards if path[0] not in names})
        elif isinstance(node, nodes.FilterBlock):
            self.visit(node.filter, bound, guards)
            self.sequence(node.body, bound, guards)
        elif isinstance(node, (nodes.Template, nodes.Block, nodes.AssignBlock, nodes.Scope)):
            self.sequence(node.body, bound, guards)
            if isinstance(node, nodes.AssignBlock):
                self.visit(node.filter, bound, guards)
        else:
            for child in node.iter_child_nodes():
                self.visit(child, bound, guards)


def check(index: RepoIndex, sources: list[TemplateSource]) -> list[Finding]:
    findings = {}
    for source in sources:
        visitor = _References(source.descriptor)
        try:
            visitor.visit(source.tree, set(), set())
        except RecursionError:
            index.skipped.append(f'TPL-4: cannot analyze deeply nested Jinja: {source.path.relative_to(index.root)}')
            continue
        for line in visitor.lines:
            line = source.source_line(line)
            findings[(source.path.resolve(), line)] = Finding(
                rule='TPL-4', severity=Severity.INFORMATION, issue_type=IssueType.INFORMATION, action=Action.REVIEW,
                path=source.path, line=line, column=1, key='presence-protection', scope='templates',
                message='A potentially optional reference has no recognized presence protection. '
                        'Its availability cannot be confirmed from the template source.',
                hint='Verify the input contract. For optional inputs, use default before dependent operations '
                     'or an appropriate is defined guard. Choose fallback values according to the configuration layers.',
            )
    return sorted(findings.values(), key=lambda f: (f.path.as_posix(), f.line))
