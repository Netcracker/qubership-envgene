"""Read and parse template sources without compiling or rendering them."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from jinja2 import ChainableUndefined, Environment, TemplateSyntaxError, nodes

from .model import RepoIndex
from .template_sources import configuration_paths, descriptor_scalars

ENVIRONMENT = Environment(undefined=ChainableUndefined)


@dataclass
class TemplateSource:
    path: Path
    offset: int
    tree: nodes.Template
    raw_blocks: list[tuple[int, str]]
    descriptor: bool = False

    def source_line(self, line: int) -> int:
        # YAML quoting and folding can change line counts. Identify the scalar itself.
        return self.offset + (1 if self.descriptor else line)


def analyze(index: RepoIndex, rules: tuple[str, ...]) -> list[TemplateSource]:
    if not rules:
        return []
    sources = []
    seen: set[tuple[Path, int, int]] = set()

    def skipped(path: Path, reason: str) -> None:
        for rule in rules:
            note = f'{rule}: {reason}: {path.relative_to(index.root)}'
            if note not in index.skipped:
                index.skipped.append(note)

    for path in configuration_paths(index, '/'.join(rules)):
        relative = path.relative_to(index.root)
        if relative.parts[0] != 'templates':
            continue
        if path.suffix != '.j2' and relative.parts[:2] != ('templates', 'env_templates'):
            continue
        try:
            text = path.read_text(encoding='utf-8')
        except (OSError, UnicodeError):
            skipped(path, 'cannot read template source')
            continue
        fragments = ([(0, len(text), text)] if path.suffix == '.j2' else
                     [(node.start_mark.index, node.end_mark.index, node.value)
                      for node in descriptor_scalars(relative, text, selectors=False)])
        for start, end, fragment in fragments:
            identity = (path.resolve(), start, end)
            if identity in seen:
                continue
            seen.add(identity)
            offset = text.count('\n', 0, start)
            try:
                tree = ENVIRONMENT.parse(fragment)
                raw_blocks = []
                raw_line = None
                raw_parts = []
                for line, kind, value in ENVIRONMENT.lex(fragment):
                    if kind == 'raw_begin':
                        raw_line, raw_parts = line, []
                    elif kind == 'raw_end' and raw_line is not None:
                        raw_blocks.append((raw_line, ''.join(raw_parts)))
                        raw_line = None
                    elif raw_line is not None:
                        raw_parts.append(value)
            except (TemplateSyntaxError, RecursionError):
                skipped(path, 'cannot parse Jinja source')
                continue
            sources.append(TemplateSource(path, offset, tree, raw_blocks, path.suffix != '.j2'))
    return sources
