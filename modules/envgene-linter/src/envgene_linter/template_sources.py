"""Shared configuration paths and descriptor source spans."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError
from ruamel.yaml.nodes import MappingNode, ScalarNode, SequenceNode

from .model import RepoIndex
from .parameter_objects import safe_parameter_path

_ROOTS = ('environments', 'configuration', 'templates')


def configuration_paths(index: RepoIndex, rule: str) -> Iterator[Path]:
    def onerror(error: OSError) -> None:
        note = f'{rule}: cannot enumerate a repository configuration directory'
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


def descriptor_scalars(relative: Path, text: str, *, selectors: bool = True) -> list[ScalarNode]:
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
        for name in ('template_path', 'name') if namespace and selectors else ('template_path',):
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
                spans.append(node)
            elif isinstance(node, MappingNode):
                pending.extend(child for pair in node.value for child in pair)
            elif isinstance(node, SequenceNode):
                pending.extend(node.value)
    return spans


def descriptor_spans(relative: Path, text: str) -> list[tuple[int, int]]:
    return [(node.start_mark.index, node.end_mark.index) for node in descriptor_scalars(relative, text)]
