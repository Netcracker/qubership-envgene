from pathlib import Path

from envgene_linter.model import Action, Finding, IssueType, Severity
from envgene_linter.rulemeta import RULES, defaults_for


def test_catalog_defaults_for_known_rules():
    assert set(RULES) == {
        "PLACE-1", "PLACE-2", "PLACE-3", "PLACE-4", "PLACE-6", "PLACE-7", "PLACE-8", "PLACE-9", "PLACE-10",
        "SEC-1", "SEC-3", "SEC-4", "SEC-5", "INT-2", "INT-3", "NAME-1", "NAME-2", "NAME-3", "NAME-4",
    }
    assert RULES["PLACE-4"].description == "Cloud Passport keys do not belong in ParameterSets"
    assert RULES["PLACE-4"].default_issue_type is IssueType.WARNING
    assert RULES["PLACE-4"].default_action is Action.FIX
    assert RULES["PLACE-6"].description == "Pipeline ParameterSets bind to the Cloud"
    assert RULES["PLACE-6"].default_issue_type is IssueType.WARNING
    assert RULES["PLACE-6"].default_action is Action.FIX
    assert RULES["PLACE-7"].description == "One category per ParameterSet"
    assert RULES["PLACE-7"].default_issue_type is IssueType.WARNING
    assert RULES["PLACE-7"].default_action is Action.FIX
    assert RULES["PLACE-8"].description == "Referenced or used entities are empty"
    assert RULES["PLACE-8"].default_issue_type is IssueType.INFORMATION
    assert RULES["PLACE-8"].default_action is Action.REVIEW
    assert RULES["PLACE-9"].description == "One Cloud Passport per cluster"
    assert RULES["PLACE-9"].default_issue_type is IssueType.WARNING
    assert RULES["PLACE-9"].default_action is Action.FIX
    assert RULES["PLACE-10"].description == "Entities belong in their type directories"
    assert RULES["PLACE-10"].default_issue_type is IssueType.WARNING
    assert RULES["PLACE-10"].default_action is Action.FIX
    assert defaults_for("INT-2") == (IssueType.WARNING, Action.FIX)
    assert defaults_for("SEC-5") == (IssueType.INFORMATION, Action.REVIEW)
    assert defaults_for("SEC-4") == (IssueType.INFORMATION, Action.REVIEW)
    assert defaults_for("SEC-3") == (IssueType.WARNING, Action.FIX)
    assert defaults_for("SEC-1") == (IssueType.WARNING, Action.FIX)
    assert RULES["NAME-1"].description == "Different keys may name the same concept"
    assert RULES["NAME-1"].default_issue_type is IssueType.INFORMATION
    assert RULES["NAME-1"].default_action is Action.REVIEW
    assert RULES["NAME-2"].description == "Filename stem must equal the name field"
    assert RULES["NAME-2"].default_issue_type is IssueType.WARNING
    assert RULES["NAME-2"].default_action is Action.FIX
    assert RULES["NAME-3"].description == "Filenames, directories, and namespaces use kebab-case"
    assert RULES["NAME-3"].default_issue_type is IssueType.INFORMATION
    assert RULES["NAME-3"].default_action is Action.REVIEW
    assert RULES["NAME-4"].description == "Bound ParameterSet stem is <subject>-<category>"
    assert RULES["NAME-4"].default_issue_type is IssueType.INFORMATION
    assert RULES["NAME-4"].default_action is Action.REVIEW
    for rule_id in ("PLACE-1", "PLACE-2", "PLACE-3", "PLACE-4", "PLACE-6", "PLACE-7", "PLACE-9", "PLACE-10"):
        assert RULES[rule_id].default_issue_type is IssueType.WARNING
        assert RULES[rule_id].default_action is Action.FIX


def test_defaults_for_returns_catalog_pair():
    assert defaults_for("PLACE-2") == (IssueType.WARNING, Action.FIX)


def test_finding_new_fields_default():
    finding = Finding(
        rule="PLACE-1",
        severity=Severity.WARNING,
        path=Path("a.yml"),
        line=4,
        key="K",
        scope="s",
        message="m",
        hint="h",
    )
    assert finding.column == 1
    assert finding.issue_type is IssueType.WARNING
    assert finding.action is Action.FIX
