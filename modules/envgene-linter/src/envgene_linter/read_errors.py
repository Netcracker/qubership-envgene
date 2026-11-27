"""Context-local collection of safe source read failures."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ReadProblem:
    path: Path
    reason: str
    line: int = 1
    column: int = 1


_problems: ContextVar[list[ReadProblem] | None] = ContextVar('read_problems', default=None)


def record_read_error(problem: ReadProblem) -> None:
    problems = _problems.get()
    if problems is not None:
        problems.append(problem)


@contextmanager
def collect_read_errors() -> Iterator[list[ReadProblem]]:
    problems: list[ReadProblem] = []
    token = _problems.set(problems)
    try:
        yield problems
    finally:
        _problems.reset(token)
