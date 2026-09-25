"""NAME-8: name the default Cloud Passport passport and its credentials passport-creds."""
from pathlib import Path

from ..connections import Connections, compute_connections
from ..model import Finding, RepoIndex, Severity
from ..rulemeta import RULES


def _physical(index: RepoIndex, path: Path) -> Path | None:
    try:
        logical = path.absolute().relative_to(index.root)
        physical = path.resolve(strict=True)
        relative = physical.relative_to(index.root)
        if '.git' in logical.parts or '.git' in relative.parts or not physical.is_file():
            return None
        return physical
    except (OSError, RuntimeError, ValueError):
        return None


def check(index: RepoIndex, connections: Connections | None = None) -> list[Finding]:
    connections = connections if connections is not None else compute_connections(index)
    issues: dict[Path, tuple[Path, set[str], set[str]]] = {}

    def consider(path: Path, expected: str, environment: str) -> None:
        physical = _physical(index, path)
        if physical is None or path.stem == expected:
            return
        _, environments, requirements = issues.setdefault(physical, (path, set(), set()))
        environments.add(environment)
        requirements.add(expected)

    for environment, passport in sorted(connections.environment_passports.items()):
        if passport.path.suffix not in ('.yml', '.yaml') or passport.stem == 'passport-infra':
            continue
        if _physical(index, passport.path) is None:
            continue
        consider(passport.path, 'passport', environment)
        # Preserve the generator's legacy-first companion lookup, including its .yml-only contract.
        for candidate in (passport.path.parent / 'credentials' / f'{passport.stem}.yml',
                          passport.path.parent / f'{passport.stem}-creds.yml'):
            try:
                present = candidate.exists() or candidate.is_symlink()
            except (OSError, RuntimeError):
                present = False
            if present:
                consider(candidate, 'passport-creds', environment)
                break

    meta = RULES['NAME-8']
    findings = []
    for path, environments, requirements in issues.values():
        messages = []
        for expected in sorted(requirements):
            kind = 'Cloud Passport' if expected == 'passport' else 'Cloud Passport credentials'
            messages.append(f'{kind} filename stem must be {expected!r}.')
        if len(requirements) > 1:
            hint = ('Use separate passport and companion files with the required names, '
                    'and update dependent references.')
        else:
            expected = next(iter(requirements))
            hint = (f'Rename the file to {expected}{path.suffix} and update dependent references. '
                    'Keep the passport and its companion credentials names consistent.')
        findings.append(Finding(
            rule='NAME-8', severity=Severity.WARNING,
            issue_type=meta.default_issue_type, action=meta.default_action,
            path=path, line=1, column=1, key='filename', scope=', '.join(sorted(environments)),
            message=' '.join(messages), hint=hint,
        ))
    return sorted(findings, key=lambda item: (str(item.path), item.message))
