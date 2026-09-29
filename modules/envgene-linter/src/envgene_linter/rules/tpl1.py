"""TPL-1: check template placement and Jinja in EnvGene repository YAML."""

from __future__ import annotations

import re
from bisect import bisect_right
from collections.abc import Iterator
from pathlib import Path

from ..connections import Connections
from ..model import Action, Finding, IssueType, RepoIndex, Severity
from ..template_sources import configuration_paths, descriptor_spans
from ..rulemeta import RULES

_OPENING = re.compile(r'{{|{%|{#')
_CLOSING = {'{{': '}}', '{%': '%}', '{#': '#}'}
_ENVGENE_NAME = re.compile(
    r'(?<![\w.])(?:current_env|current_env_template|peer_env_template|origin_env_template|'
    r'templates_dir|templates_dirs|env_definition|cloud_passport|env_vars|namespace_by_deploy_postfix)(?!\w)'
)
_QUOTED = re.compile(r'''"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*' ''', re.VERBOSE)


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
    for path in configuration_paths(index, 'TPL-1'):
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
        exemptions = descriptor_spans(relative, text)
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
