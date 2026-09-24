"""Private analysis records. Names and IDs must not be copied into findings."""
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Kind = Literal['ParameterSet', 'Shared Template Variable', 'Resource Profile Override', 'Credential']


@dataclass(frozen=True)
class Candidate:
    path: Path
    physical: Path
    kind: Kind
    name: str
    environments: tuple[str, ...]
    aliases: tuple[Path, ...] = ()
    line: int = 1
    column: int = 1


@dataclass(frozen=True)
class Reference:
    source: Path
    kind: Kind
    name: str
    environment: str | None
    catalog: Path | None = None
    category: str | None = None
    target: str | None = None


@dataclass(frozen=True)
class Gap:
    source: Path
    kind: Kind
    environment: str | None
    reason: str


@dataclass(frozen=True)
class Usage:
    candidate: Candidate
    references: tuple[Reference, ...]
    gaps: tuple[Gap, ...]
