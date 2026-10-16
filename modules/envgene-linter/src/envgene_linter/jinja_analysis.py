"""Read and parse template sources without compiling or rendering them."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from jinja2 import ChainableUndefined, Environment, TemplateSyntaxError, nodes

from .model import RepoIndex, SkippedCheck
from .template_sources import configuration_paths, descriptor_scalars

ENVIRONMENT = Environment(undefined=ChainableUndefined)


@dataclass
class TemplateSource:
    path: Path
    offset: int
    tree: nodes.Template
    descriptor: bool = False
    text: str = field(default='', repr=False)

    def source_line(self, line: int) -> int:
        # YAML quoting and folding can change line counts. Identify the scalar itself.
        return self.offset + (1 if self.descriptor else line)


def skip_check(index: RepoIndex, rule: str, path: Path, reason: str, line: int = 1) -> None:
    note = f'{rule}: {reason}: {path.relative_to(index.root)}:{line}:1'
    if note not in index.skipped:
        index.skipped.append(note)
    check = SkippedCheck(rule, path, line, 1, reason)
    if check not in index.skipped_checks:
        index.skipped_checks.append(check)


def analyze(index: RepoIndex, rules: tuple[str, ...]) -> list[TemplateSource]:
    if not rules:
        return []
    sources = []
    seen: set[tuple[Path, int, int]] = set()

    def skipped(path: Path, reason: str, line: int = 1) -> None:
        for rule in rules:
            skip_check(index, rule, path, reason, line)

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
            except TemplateSyntaxError as exc:
                line = offset + (1 if path.suffix != '.j2' else max(1, exc.lineno or 1))
                skipped(path, 'cannot parse Jinja source', line)
                continue
            except RecursionError:
                skipped(path, 'Jinja source exceeds the parser recursion limit', offset + 1)
                continue
            sources.append(TemplateSource(path, offset, tree, descriptor=path.suffix != '.j2', text=fragment))
    return sources
