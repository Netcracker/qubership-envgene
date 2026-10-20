"""Select legacy-expression sources and conservative rendering contracts."""

from __future__ import annotations

import re

from ruamel.yaml.nodes import MappingNode, ScalarNode, SequenceNode

from .ansible_compat import CompatibilitySource
from .jinja_analysis import TemplateSource, skip_check
from .model import RepoIndex
from .parameter_objects import safe_parameter_path
from .parsing import ParseFailure, compose_yaml
from .template_sources import configuration_paths, descriptor_scalars

_LEGACY = re.compile(
    r'\bansible\.|\b(?:lookup|query|q)\s*\(|'
    r'\|\s*(?:to_nice_yaml|urlsplit|from_yaml|to_yaml|combine|regex_replace|dict2items|items2dict|'
    r'json_query|mandatory|ternary|bool|b64encode|b64decode)\b'
)


def _compose(index, path, text):
    try:
        return compose_yaml(text)
    except ParseFailure as exc:
        skip_check(index, 'TPL-6', path, exc.reason, exc.line, exc.column)
        return None


def _scalars(node):
    pending, seen = [node], set()
    while pending:
        node = pending.pop()
        if node is None or id(node) in seen:
            continue
        seen.add(id(node))
        if isinstance(node, ScalarNode):
            yield node
        elif isinstance(node, MappingNode):
            pending.extend(child for pair in reversed(node.value) for child in reversed(pair))
        elif isinstance(node, SequenceNode):
            pending.extend(reversed(node.value))


def _fields(node):
    if not isinstance(node, MappingNode):
        return {}
    return {key.value: value for key, value in node.value if isinstance(key, ScalarNode)}


def _descriptor_contracts(root):
    contracts = {}

    def mark(node, rendering):
        for scalar in _scalars(node):
            identity = (scalar.start_mark.line, scalar.value)
            contracts.setdefault(identity, set()).add(rendering)

    top = _fields(root)
    for name in ('tenant', 'composite_structure', 'bg_domain', 'external_credential_template'):
        if isinstance(top.get(name), ScalarNode):
            mark(top[name], 'jinja')

    def entity(node, namespace=False):
        fields = _fields(node)
        if isinstance(fields.get('template_path'), ScalarNode):
            mark(fields['template_path'], 'jinja')
        if isinstance(fields.get('template_override'), MappingNode):
            mark(fields['template_override'], 'envgene')
            if namespace:
                # Namespace-name discovery renders the whole override before
                # the later object renderer applies compatibility replacements.
                mark(fields['template_override'], 'custom_jinja')

    cloud = top.get('cloud')
    if isinstance(cloud, ScalarNode):
        mark(cloud, 'jinja')
    else:
        entity(cloud)
    namespaces = top.get('namespaces')
    if isinstance(namespaces, SequenceNode):
        for namespace in namespaces.value:
            entity(namespace, namespace=True)
    return contracts


def _file_contract(index, path):
    relative = path.relative_to(index.root)
    if relative.parts[:2] in (('templates', 'regdefs'), ('templates', 'appdefs')):
        return 'envgene'
    if relative.parts[0] == 'templates' and path.suffix == '.j2':
        if path.name.endswith(('.yml.j2', '.yaml.j2')):
            return 'envgene'
        return 'jinja' if relative.parts[:2] == ('templates', 'parameters') else 'unknown'
    return None


def compatibility_sources(index: RepoIndex, sources: list[TemplateSource]) -> list[CompatibilitySource]:
    result, seen, full_files, documents = [], set(), set(), {}

    def read(path):
        if path in documents:
            return documents[path]
        try:
            text = path.read_text(encoding='utf-8')
        except (OSError, UnicodeError):
            skip_check(index, 'TPL-6', path, 'cannot read compatibility source')
            text = None
        documents[path] = text
        return text

    def add(path, text, rendering, offset=0, descriptor=False):
        identity = (path.resolve(), offset, text, rendering, descriptor)
        if identity not in seen:
            seen.add(identity)
            result.append(CompatibilitySource(path, text, rendering, offset, descriptor))

    for source in sources:
        if not safe_parameter_path(index, source.path):
            continue
        if source.descriptor:
            text = read(source.path)
            root = _compose(index, source.path, text) if text is not None else None
            if root is None:
                continue
            contracts = _descriptor_contracts(root)
            renderings = contracts.get((source.offset, source.text), {'unknown'})
        else:
            rendering = _file_contract(index, source.path) or 'unknown'
            renderings = {rendering}
            full_files.add((source.path.resolve(), rendering))
        for rendering in sorted(renderings):
            add(source.path, source.text, rendering, source.offset, source.descriptor)

    paths = list(configuration_paths(index, 'TPL-6'))
    skipped = {check.path.resolve() for check in index.skipped_checks if check.rule == 'TPL-6'}
    for path in paths:
        rendering = _file_contract(index, path)
        if (path.resolve(), rendering or 'unknown') in full_files or path.resolve() in skipped:
            continue
        text = read(path)
        if text is None:
            continue
        relative = path.relative_to(index.root)
        if rendering is not None:
            add(path, text, rendering)
            full_files.add((path.resolve(), rendering))
            continue
        if not _LEGACY.search(text):
            continue
        root = _compose(index, path, text) if path.suffix != '.j2' else None
        if root is None:
            # A source-level Jinja check can still complete with an unknown YAML contract.
            add(path, text, 'unknown')
            continue
        selected = descriptor_scalars(relative, text, selectors=False)
        contracts = _descriptor_contracts(root) if selected else {}
        for scalar in _scalars(root):
            if _LEGACY.search(scalar.value):
                renderings = contracts.get((scalar.start_mark.line, scalar.value), {'unknown'})
                for rendering in sorted(renderings):
                    add(path, scalar.value, rendering, scalar.start_mark.line, True)
    return result
