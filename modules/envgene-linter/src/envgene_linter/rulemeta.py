from __future__ import annotations

from dataclasses import dataclass

from .model import Action, IssueType


@dataclass(frozen=True)
class RuleMeta:
    id: str
    description: str
    default_issue_type: IssueType
    default_action: Action


RULES: dict[str, RuleMeta] = {
    "PLACE-1": RuleMeta(
        "PLACE-1",
        "Same value belongs on a higher layer",
        IssueType.WARNING,
        Action.FIX,
    ),
    "PLACE-2": RuleMeta(
        "PLACE-2",
        "Higher layer restates a lower-layer value",
        IssueType.WARNING,
        Action.FIX,
    ),
    "PLACE-3": RuleMeta(
        "PLACE-3",
        "Cloud Passport keys and files are misplaced",
        IssueType.WARNING,
        Action.FIX,
    ),
    "PLACE-4": RuleMeta(
        "PLACE-4",
        "Cloud Passport keys do not belong in ParameterSets",
        IssueType.WARNING,
        Action.FIX,
    ),
    "PLACE-6": RuleMeta(
        "PLACE-6",
        "Pipeline ParameterSets bind to the Cloud",
        IssueType.WARNING,
        Action.FIX,
    ),
    "PLACE-7": RuleMeta(
        "PLACE-7",
        "One category per ParameterSet",
        IssueType.WARNING,
        Action.FIX,
    ),
    "PLACE-8": RuleMeta(
        "PLACE-8",
        "Referenced or used entities are empty",
        IssueType.INFORMATION,
        Action.REVIEW,
    ),
    "PLACE-9": RuleMeta(
        "PLACE-9",
        "One Cloud Passport per cluster",
        IssueType.WARNING,
        Action.FIX,
    ),
    "PLACE-10": RuleMeta(
        "PLACE-10",
        "Entities belong in their type directories",
        IssueType.WARNING,
        Action.FIX,
    ),
    "SEC-1": RuleMeta(
        "SEC-1",
        "No literal secrets in parameters",
        IssueType.WARNING,
        Action.FIX,
    ),
    "SEC-3": RuleMeta(
        "SEC-3",
        "No credentials in runtime parameters",
        IssueType.WARNING,
        Action.FIX,
    ),
    "SEC-4": RuleMeta(
        "SEC-4",
        "Credential pairs reference the same ID",
        IssueType.INFORMATION,
        Action.REVIEW,
    ),
    "SEC-5": RuleMeta(
        "SEC-5",
        "Review protection of connected secrets",
        IssueType.INFORMATION,
        Action.REVIEW,
    ),
    "INT-2": RuleMeta("INT-2", "Every reference resolves", IssueType.WARNING, Action.FIX),
    "NAME-1": RuleMeta(
        "NAME-1",
        "Different keys may name the same concept",
        IssueType.INFORMATION,
        Action.REVIEW,
    ),
    "NAME-2": RuleMeta(
        "NAME-2",
        "Filename stem must equal the name field",
        IssueType.WARNING,
        Action.FIX,
    ),
    "NAME-3": RuleMeta(
        "NAME-3",
        "Filenames, directories, and namespaces use kebab-case",
        IssueType.INFORMATION,
        Action.REVIEW,
    ),
    "NAME-4": RuleMeta(
        "NAME-4",
        "Bound ParameterSet stem is <subject>-<category>",
        IssueType.INFORMATION,
        Action.REVIEW,
    ),
}


def defaults_for(rule_id: str) -> tuple[IssueType, Action]:
    item = RULES[rule_id]
    return item.default_issue_type, item.default_action
