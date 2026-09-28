"""TPL-1: check template placement and Jinja in EnvGene repository YAML."""

from __future__ import annotations

import os
import re
from bisect import bisect_right
from collections.abc import Iterator
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError
from ruamel.yaml.nodes import MappingNode, ScalarNode, SequenceNode

from ..connections import Connections
from ..model import Action, Finding, IssueType, RepoIndex, Severity
from ..parameter_objects import safe_parameter_path
from ..rulemeta import RULES

_ROOTS = ('environments', 'configuration', 'templates')
_OPENING = re.compile(r'{{|{%|{#')
_CLOSING = {'{{': '}}', '{%': '%}', '{#': '#}'}
_ENVGENE_NAME = re.compile(
    r'(?<![\w.])(?:current_env|current_env_template|peer_env_template|origin_env_template|'
    r'templates_dir|templates_dirs|env_definition|cloud_passport|env_vars|namespace_by_deploy_postfix)(?!\w)'
)
_QUOTED = re.compile(r'''"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*' ''', re.VERBOSE)


def _paths(index: RepoIndex) -> Iterator[Path]:
    def onerror(error: OSError) -> None:
        note = 'TPL-1: cannot enumerate a repository configuration directory'
        if note not in index.skipped:
            index.skipped.append(note)

    for name in _ROOTS:
        directory = index.root / name
        if directory.is_symlink() or not directory.exists():
            continue
        for parent, directories, files in os.walk(directory, followlinks=False, onerror=onerror):
            parent = Path(parent)
            directories[:] = sorted(child for child in directories
                                    if child not in ('.git', '.venv', 'node_modules', '__pycache__')
                                    and not (parent / child).is_symlink())
            for filename in sorted(files):
                path = parent / filename
                if path.suffix in ('.yml', '.yaml', '.j2') and safe_parameter_path(index, path):
                    yield path


def _spans(text: str) -> Iterator[tuple[int, int]]:
    exhausted: set[str] = set()
    offset = 0
    while match := _OPENING.search(text, offset):
        token = match.group()
        offset = match.end()
        if token in exhausted:
            continue
        end = text.find(_CLOSING[token], offset)
        if end < 0:
            # An unmatched family is searched only once through the remaining suffix.
            exhausted.add(token)
            continue
        offset = end + 2
        yield match.start(), offset


def _descriptor_exemptions(relative: Path, text: str) -> list[tuple[int, int]]:
    if relative.parts[:2] != ('templates', 'env_templates'):
        return []
    try:
        root = YAML(typ='safe', pure=True).compose(text)
    except (YAMLError, ValueError, RecursionError):
        return []
    if not isinstance(root, MappingNode):
        return []

    def fields(node):
        if not isinstance(node, MappingNode):
            return {}
        return {key.value: (key, value) for key, value in node.value if isinstance(key, ScalarNode)}

    top = fields(root)
    composed = 'parent-templates' in top and isinstance(top['parent-templates'][1], MappingNode)
    if not composed and not {'tenant', 'cloud', 'namespaces'} <= top.keys():
        return []
    if 'namespaces' not in top or not isinstance(top['namespaces'][1], SequenceNode):
        return []
    selected = [top[key] for key in ('tenant', 'composite_structure', 'bg_domain', 'external_credential_template')
                if key in top and isinstance(top[key][1], ScalarNode)]
    def rendered_fields(node, namespace=False):
        members = fields(node)
        for name in ('template_path', 'name') if namespace else ('template_path',):
            if name in members and isinstance(members[name][1], ScalarNode):
                selected.append(members[name])
        if 'template_override' in members and isinstance(members['template_override'][1], MappingNode):
            selected.append(members['template_override'])
        implicit_parent = (namespace and composed and len(fields(top['parent-templates'][1])) == 1
                           and 'template_path' not in members)
        if composed and ('parent' in members or implicit_parent) and 'overrides-parent' in members:
            overrides = fields(members['overrides-parent'][1])
            for name, kind in (('name', ScalarNode), ('deployParameters', MappingNode),
                               ('e2eParameters', MappingNode), ('technicalConfigurationParameters', MappingNode)):
                if name in overrides and isinstance(overrides[name][1], kind):
                    selected.append(overrides[name])

    cloud_key, cloud = top.get('cloud', (None, None))
    if isinstance(cloud, ScalarNode):
        selected.append((cloud_key, cloud))
    else:
        rendered_fields(cloud)
    for namespace in top['namespaces'][1].value:
        rendered_fields(namespace, namespace=True)

    spans = []
    for key, value in selected:
        # An alias points to its anchor's node. Do not exempt source outside the allowed field.
        lower, upper = key.end_mark.index, value.end_mark.index
        pending = [value]
        seen = set()
        while pending:
            node = pending.pop()
            if id(node) in seen or not lower <= node.start_mark.index < node.end_mark.index <= upper:
                continue
            seen.add(id(node))
            if isinstance(node, ScalarNode):
                spans.append((node.start_mark.index, node.end_mark.index))
            elif isinstance(node, MappingNode):
                pending.extend(child for pair in node.value for child in pair)
            elif isinstance(node, SequenceNode):
                pending.extend(node.value)
    return spans


def _definite(text: str) -> bool:
    if text.startswith(('{%', '{#')):
        return True
    # Shared delimiters alone do not distinguish Jinja from Helm or application placeholders.
    body = _QUOTED.sub('', text[2:-2])
    if re.search(r'\$|===|!==|=>|&&|\|\|', body):
        return False
    return bool(_ENVGENE_NAME.search(body))


def check(index: RepoIndex, connections: Connections | None = None) -> list[Finding]:
    meta = RULES['TPL-1']
    findings: dict[tuple[Path, int], Finding] = {}
    texts: dict[Path, str | None] = {}
    for path in _paths(index):
        physical = path.resolve()
        relative = path.relative_to(index.root)
        scope = relative.parts[0]
        if path.suffix == '.j2':
            if scope != 'templates':
                findings[(physical, 1)] = Finding(
                    rule=meta.id, severity=Severity.WARNING, issue_type=meta.default_issue_type,
                    action=Action.FIX, path=path, line=1, column=1, key='template-location', scope=scope,
                    message='A .j2 file is outside the templates/ directory.',
                    hint='Keep Jinja templates in templates/ and plain YAML in instance configuration. '
                         'Update the generator inputs and references when moving template logic.',
                )
            continue
        if physical not in texts:
            try:
                texts[physical] = path.read_text(encoding='utf-8')
            except (OSError, UnicodeDecodeError):
                texts[physical] = None
                index.skipped.append(f'TPL-1: cannot read YAML file: {relative}')
        text = texts[physical]
        if text is None:
            continue
        exemptions = _descriptor_exemptions(relative, text)
        newlines = [-1, *(match.start() for match in re.finditer('\n', text))]
        for start, end in _spans(text):
            if any(lower <= start and end <= upper for lower, upper in exemptions):
                continue
            definite = _definite(text[start:end])
            line = bisect_right(newlines, start)
            identity = (physical, line)
            previous = findings.get(identity)
            if previous is not None and (previous.action == Action.FIX or not definite):
                continue
            findings[identity] = Finding(
                rule=meta.id, severity=Severity.WARNING if definite else Severity.INFORMATION,
                issue_type=meta.default_issue_type if definite else IssueType.INFORMATION,
                action=Action.FIX if definite else Action.REVIEW,
                path=path, line=line, column=start - newlines[line - 1], key='jinja', scope=scope,
                message=('Jinja occurs outside a .j2 template or a supported descriptor field.' if definite else
                         'Template delimiters found. Their renderer cannot be determined from the available source.'),
                hint=('Use a concrete value or supported EnvGene macro, or place Jinja logic in a .j2 template '
                      'under templates/ that the generator processes. Renaming alone does not configure rendering.'
                      if definite else 'Review whether this is EnvGene Jinja or syntax consumed by Helm or the application. '
                      'Keep downstream template syntax when the consumer requires it.'),
            )
    return sorted(findings.values(), key=lambda item: (item.path.as_posix(), item.line, item.column))
