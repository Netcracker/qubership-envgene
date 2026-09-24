"""INT-3: used reference names must not be defined at multiple scopes."""

from __future__ import annotations

import os
from pathlib import Path

from ..connections import (
    CREDENTIAL_DIRS, PROFILE_DIRS, Connections, _resolve_shared_template_variable, compute_connections,
)
from ..discovery import paramset_stem
from ..model import EnvModel, Finding, Location, NamedEntityFile, RepoIndex, Severity
from ..rulemeta import RULES
from ..security_values import literal_name

Candidate = tuple[int, Path]


def _literal(reference: str) -> bool:
    return literal_name(reference) and reference not in (".", "..") and not any(
        marker in reference for marker in ("}}", "%}", "{#", "#}", "/", "\\")
    )


def _safe(index: RepoIndex, path: Path, *, directory: bool = False) -> Path | None:
    try:
        logical = path.absolute().relative_to(index.root)
        if ".git" in logical.parts:
            return None
        parent = index.root
        for part in logical.parts if directory else logical.parts[:-1]:
            parent /= part
            if parent.is_symlink():
                return None
        physical = path.resolve()
        if ".git" in physical.relative_to(index.root).parts:
            return None
        exists = path.is_dir() if directory else path.is_file()
        if exists:
            return physical
    except (OSError, RuntimeError, ValueError):
        pass
    return None


class _Candidates:
    def __init__(self, index: RepoIndex):
        self.index = index
        self.directories: dict[Path, list[Path]] = {}

    def files(self, directory: Path) -> list[Path]:
        if directory not in self.directories:
            paths: list[Path] = []

            def skipped(_error: OSError) -> None:
                note = f"{directory}: cannot enumerate directory; INT-3 skipped"
                if note not in self.index.skipped:
                    self.index.skipped.append(note)

            if _safe(self.index, directory, directory=True) is not None:
                for base, folders, files in os.walk(directory, followlinks=False, onerror=skipped):
                    folders[:] = sorted(
                        name for name in folders
                        if name != ".git" and not (Path(base) / name).is_symlink()
                    )
                    paths.extend(Path(base) / name for name in sorted(files) if name.endswith((".yml", ".yaml")))
            self.directories[directory] = paths
        return self.directories[directory]

    def named(self, bases: tuple[Path, ...], reference: str,
              records: list[NamedEntityFile], folders: tuple[str, ...]) -> tuple[list[Candidate], list[Candidate]]:
        candidates, selected = [], []
        found_scope = False
        for scope, base in enumerate(bases):
            for folder in folders:
                matches = sorted({
                    path for record in records if not record.is_jinja
                    for path in (record.path, *record.aliases)
                    if path.is_relative_to(base / folder) and paramset_stem(path) == reference
                })
                if not matches:
                    continue
                safe = [(scope, path) for path in matches if _safe(self.index, path) is not None]
                candidates.extend(safe)
                if not found_scope:
                    selected = safe
                    found_scope = True
                break
        return candidates, selected

    def variables(self, bases: tuple[Path, ...], reference: str) -> list[Candidate]:
        candidates = []
        directories = [(scope, base / name) for scope, base in enumerate(bases)
                       for name in ("configuration", "configurations")]
        directories.append((0, bases[0]))
        for scope, directory in directories:
            for path in self.files(directory):
                if paramset_stem(path) != reference:
                    continue
                if _safe(self.index, path) is not None:
                    candidates.append((scope, path))
        return candidates


def _finding(environment: str, kind: str, paths: list[Path]) -> Finding:
    hint = "Use distinct reference names and update the bindings, or keep the definition at one scope."
    if kind == "ParameterSet":
        hint += " ParameterSet fragments can merge during generation; this finding checks the naming standard."
    meta = RULES["INT-3"]
    return Finding(
        rule="INT-3", severity=Severity.WARNING, path=paths[0], line=1,
        key=kind, scope=environment,
        message=f"The same {kind} reference name is defined at multiple scopes for environment {environment}.",
        hint=hint, issue_type=meta.default_issue_type, action=meta.default_action,
        locations=tuple(Location(path, 1, 1) for path in paths),
    )


def check(index: RepoIndex, connections: Connections | None = None) -> list[Finding]:
    connections = connections if connections is not None else compute_connections(index)
    collector = _Candidates(index)
    findings: list[Finding] = []

    def report(env: EnvModel, kind: str, candidates: list[Candidate], selected: list[Candidate],
               connected: frozenset[Path]) -> None:
        # Give selected logical aliases priority before deduplicating physical files.
        selected = [candidate for candidate in selected if _safe(index, candidate[1]) in connected]
        if not selected:
            return
        physical: dict[Path, Candidate] = {}
        for candidate in [*selected, *candidates]:
            resolved = _safe(index, candidate[1])
            if resolved is not None:
                physical.setdefault(resolved, candidate)
        if len({scope for scope, _ in physical.values()}) > 1:
            paths = [path for _, path in sorted(physical.values())]
            findings.append(_finding(env.full_name, kind, paths))

    for env in sorted(index.environments, key=lambda env: env.full_name):
        bases = (env.path / "Inventory", index.clusters[env.cluster].path, index.root / "environments")
        references = {
            use.reference for uses in connections.parameter_uses.values()
            for use in uses if use.environment == env.full_name and _literal(use.reference)
        }
        for reference in sorted(references):
            candidates = []
            for scope, files in enumerate((
                env.paramsets, index.clusters[env.cluster].paramsets, index.site_paramsets,
            )):
                for file in files:
                    if file.stem == reference and not file.is_jinja:
                        candidates.append((scope, file.path))
            report(env, "ParameterSet", candidates, candidates,
                   connections.environment_parameter_sets.get(env.full_name, frozenset()))
        used = connections.environment_paths.get(env.full_name, frozenset())
        for kind, bindings, records, folders, connected in (
            ("Resource Profile Override", env.resource_profile_bindings.values(), index.resource_profiles,
             PROFILE_DIRS, connections.resource_profiles),
            ("Shared credentials", env.shared_credential_bindings, index.credential_files,
             CREDENTIAL_DIRS, connections.credentials),
        ):
            for reference in sorted(set(bindings)):
                if _literal(reference):
                    candidates, selected = collector.named(bases, reference, records, folders)
                    report(env, kind, candidates, selected, used & connected)
        for reference in sorted(set(env.shared_template_variable_bindings)):
            if _literal(reference):
                candidates = collector.variables(bases, reference)
                # The generator's walk order chooses the winner; sorted enumeration
                # here is only for complete, deterministic conflict locations.
                resolved = _resolve_shared_template_variable(index, env, reference)
                selected = [item for item in candidates if resolved is not None and item[1] == resolved[1]]
                report(env, "Shared Template Variables", candidates, selected, used & connections.shared_template_variables)
    return sorted(findings, key=lambda finding: (
        finding.scope, finding.key, tuple(str(item.path) for item in finding.file_locations()),
    ))
