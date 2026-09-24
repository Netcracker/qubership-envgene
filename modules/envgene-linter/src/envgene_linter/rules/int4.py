"""INT-4: review authored entities without observed references."""
from ..connections import Connections, compute_connections
from ..model import Action, Finding, IssueType, RepoIndex, Severity
from ..usage_candidates import collect_candidates
from ..usage_references import analyze_usage

_REASONS = {
    'dynamic': 'A dynamic reference could not be resolved in this scope.',
    'unreadable': 'A relevant local consumer could not be read.',
    'no-environment': 'No consuming environment was discovered for this scope.',
    'provenance': "The generated catalog does not establish the authored entry's origin.",
    'lookup': 'This location is outside the supported reference lookup paths.',
}
_LIMITATION = ('External template consumers and rendered references are not fully analyzed. '
               'Review usage before changing this entity.')


def check(index: RepoIndex, connections: Connections | None = None) -> list[Finding]:
    connections = connections if connections is not None else compute_connections(index)
    candidates = collect_candidates(index, connections)
    findings = []
    for usage in analyze_usage(index, connections, candidates):
        if usage.references:
            continue
        candidate = usage.candidate
        reasons = sorted({gap.reason for gap in usage.gaps})
        findings.append(Finding(
            rule='INT-4', severity=Severity.INFORMATION, issue_type=IssueType.INFORMATION, action=Action.REVIEW,
            path=candidate.path, line=candidate.line, column=candidate.column, key=candidate.kind,
            scope=', '.join(candidate.environments) or 'repository',
            message=f'No references to this {candidate.kind} were found in the available sources.',
            hint=' '.join([_LIMITATION, *(_REASONS[reason] for reason in reasons)]),
        ))
    return sorted(findings, key=lambda item: (str(item.path), item.key, item.line, item.column))
