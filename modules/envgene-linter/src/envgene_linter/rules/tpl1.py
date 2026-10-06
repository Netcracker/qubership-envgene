"""TPL-1: check Jinja in active EnvGene repository YAML."""

from __future__ import annotations

import re
from bisect import bisect_right
from collections.abc import Iterator
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError
from ruamel.yaml.tokens import CommentToken, ScalarToken

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
_BLOCK_HEADER = re.compile(r'[|>](?:[1-9][+-]?|[+-][1-9]?)?(?=[ \t]*(?:#|$))')
_PROPERTY = re.compile(r'(?:!<[^>\n]*>|[!&][^\s,\[\]{}]+)(?:[ \t]+|$)')
_DOCUMENT_MARKER = re.compile(r'(?:---|\.\.\.)(?=[ \t]|$)')
_YAML_QUOTED = re.compile(r'''"(?:\\[\s\S]|[^"\\])*"|'(?:''|[^'])*' ''', re.VERBOSE)


def _without_yaml_comments(text: str) -> str:
    """Use YAML comment tokens when scanning succeeds, without constructing YAML objects."""
    comments: dict[int, int] = {}
    comment_starts: set[int] = set()
    try:
        YAML(typ='safe', pure=True).compose(text)
        for token in YAML(typ='rt', pure=True).scan(text):
            if isinstance(token, ScalarToken) and token.style in ('|', '>'):
                start = token.start_mark.index
                end = text.find('\n', start)
                end = end if end >= 0 else len(text)
                comment = text.find('#', start, end)
                if comment >= 0:
                    # The scanner stores block-header comments as strings without source marks.
                    comments[comment] = end
            pending = [token.comment]
            while pending:
                item = pending.pop()
                if isinstance(item, CommentToken):
                    comment_starts.add(item.start_mark.index)
                elif isinstance(item, (list, tuple)):
                    pending.extend(item)
    except (YAMLError, ValueError, RecursionError):
        # Standalone Jinja and malformed YAML still need a source-level check.
        return _lexical_without_yaml_comments(text)
    covered_end = -1
    for start in sorted(comment_starts):
        if start < covered_end or start in comments:
            continue
        end = text.find('\n', start)
        end = end + 1 if end >= 0 else len(text)
        # CommentToken values can synthesize whitespace. Use actual source lines for bounds.
        while end < len(text):
            next_end = text.find('\n', end)
            next_end = next_end + 1 if next_end >= 0 else len(text)
            following = text[end:next_end]
            if following.strip() and not following.lstrip(' \t').startswith('#'):
                break
            end = next_end
        comments[start] = covered_end = end
    masked = list(text)
    for start, end in comments.items():
        masked[start:end] = re.sub(r'[^\r\n]', ' ', text[start:end])
    return ''.join(masked)


def _lexical_without_yaml_comments(text: str) -> str:
    """Mask YAML comments without changing offsets or treating scalar content as comments."""
    masked = list(text)
    quote = None
    quote_end = None
    block = None
    continuation = None
    flow = 0
    offset = 0
    jinja_end = 0
    exhausted: set[str] = set()
    for line in text.splitlines(keepends=True):
        content = line.rstrip('\r\n')
        indent = len(content) - len(content.lstrip(' '))
        if block is not None:
            base, body_indent = block
            if not content.strip() or (indent > base and (body_indent is None or indent >= body_indent)):
                if content.strip() and body_indent is None:
                    block = (base, indent)
                offset += len(line)
                continue
            block = None
        plain = continuation is not None and indent > continuation and not flow
        key_column = parent_indent = indent
        column = 0
        if quote is None and not flow and (marker := _DOCUMENT_MARKER.match(content)):
            column = marker.end()
            plain = False
        while column < len(content):
            position = offset + column
            char = content[column]
            if position < jinja_end:
                column = min(len(content), jinja_end - offset)
                continue
            opening = text[position:position + 2]
            if opening in _CLOSING and opening not in exhausted:
                end = text.find(_CLOSING[opening], position + 2)
                if end >= 0 and (quote_end is None or end + 2 <= quote_end):
                    jinja_end = end + 2
                    plain = plain or opening == '{{'
                    column = min(len(content), jinja_end - offset)
                    continue
                if end < 0:
                    exhausted.add(opening)
            if quote is not None:
                if quote == '"' and char == '\\':
                    column += 2
                    continue
                if char == quote:
                    if quote == "'" and content[column:column + 2] == "''":
                        column += 2
                        continue
                    quote = None
                    quote_end = None
                    plain = True
                column += 1
                continue
            if char == '#' and (column == 0 or content[column - 1].isspace()):
                masked[position:offset + len(content)] = ' ' * (len(content) - column)
                break
            if char.isspace():
                column += 1
                continue
            if not plain:
                key_column = column
                if char in ('"', "'"):
                    quote = char
                    quoted = _YAML_QUOTED.match(text, position)
                    quote_end = quoted.end() if quoted else None
                    column += 1
                    continue
                if char in ('!', '&') and (prop := _PROPERTY.match(content, column)):
                    column = prop.end()
                    continue
                if not flow and char in ('|', '>') and (header := _BLOCK_HEADER.match(content, column)):
                    explicit = next((int(value) for value in header.group() if value.isdigit()), None)
                    block = (parent_indent, parent_indent + explicit if explicit else None)
                    column = header.end()
                    continue
            following = content[column + 1:column + 2]
            if char == ':' and (not following or following.isspace() or (flow and following in '[]{}"\'')):
                parent_indent = key_column
                plain = False
            elif char == '-' and not plain and (not following or following.isspace()):
                parent_indent = column
            elif char == '?' and not plain and (not following or following.isspace()):
                parent_indent = column
            elif char in '[{' and (not plain or flow):
                flow += 1
                plain = False
            elif char in ']}' and flow:
                flow -= 1
                plain = False
            elif char == ',' and flow:
                plain = False
            else:
                plain = True
            column += 1
        if content.strip():
            continuation = parent_indent if plain and quote is None and block is None else None
        offset += len(line)
    return ''.join(masked)


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
        active_text = _without_yaml_comments(text)
        newlines = [-1, *(match.start() for match in re.finditer('\n', text))]
        for start, end in _spans(active_text):
            if any(lower <= start and end <= upper for lower, upper in exemptions):
                continue
            definite = _definite(active_text[start:end])
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
                      'that the generator processes. Renaming alone does not configure rendering.'
                      if definite else 'Review whether this is EnvGene Jinja or syntax consumed by Helm or the application. '
                      'Keep downstream template syntax when the consumer requires it.'),
            )
    return sorted(findings.values(), key=lambda item: (item.path.as_posix(), item.line, item.column))
