import json
from dataclasses import replace
from pathlib import Path

import pytest
from click.testing import CliRunner

from envgene_linter import report, rule_config
from envgene_linter.cli import main
from envgene_linter.model import Action, Finding, IssueType, Location, Severity


def _finding(**overrides):
    finding = Finding(
        rule="PLACE-1", severity=Severity.WARNING,
        path=Path("environments/cluster-a/env-a/Inventory/parameters/service-deploy.yml"),
        line=3, column=3, key="LOG_LEVEL", scope="cloud/deploy",
        message="The same value occurs in two environments.",
        hint="Move LOG_LEVEL to the cluster layer.",
    )
    return replace(finding, **overrides)


def test_json_contract_keeps_all_locations_in_one_finding(tmp_path):
    finding = _finding(locations=(
        Location(tmp_path / "environments/a.yml", 60, 5),
        Location(tmp_path / "environments/b.yml", 54, 5),
        Location(tmp_path / "environments/c.yml", 58, 5),
    ))

    data = json.loads(report.render_json([finding], tmp_path))

    assert data == [{
        "rule_id": "PLACE-1",
        "rule_title": "Same value belongs on a higher layer",
        "files": ["environments/a.yml:60:5", "environments/b.yml:54:5", "environments/c.yml:58:5"],
        "issue": "The same value occurs in two environments.",
        "action": "Fix",
        "fix_suggestion": "Move LOG_LEVEL to the cluster layer.",
    }]


@pytest.mark.parametrize("issue_type", list(IssueType))
def test_json_omits_type_and_preserves_finding_action(tmp_path, issue_type):
    finding = _finding(issue_type=issue_type, action=Action.REVIEW)
    data = json.loads(report.render_json([finding], tmp_path))
    assert "type" not in data[0]
    assert data[0]["action"] == "Review"
    assert data[0]["files"] == ["environments/cluster-a/env-a/Inventory/parameters/service-deploy.yml:3:3"]


def test_json_preserves_text_without_html_escaping(tmp_path):
    text = 'Review "значение" <tag> & \\path\nnext line'
    output = report.render_json([_finding(message=text, hint=text)], tmp_path)
    data = json.loads(output)
    assert data[0]["issue"] == text
    assert data[0]["fix_suggestion"] == text
    assert "значение" in output


def test_json_filters_disabled_and_inapplicable_rules(tmp_path):
    findings = [_finding(rule=rule) for rule in ("PLACE-1", "TPL-4", "TPL-6")]
    data = json.loads(report.render_json(
        findings, tmp_path, disabled_rules=("TPL-4",), not_applicable_rules=("PLACE-1",),
    ))
    assert [item["rule_id"] for item in data] == ["TPL-6"]
    assert json.loads(report.render_json([], tmp_path)) == []
    assert json.loads(report.render_json(findings, tmp_path, disabled_rules=("PLACE-1", "TPL-4", "TPL-6"))) == []


def test_json_rule_order_preserves_each_finding_and_handles_unknown_rules(tmp_path):
    findings = [_finding(rule=rule, message=str(index)) for index, rule in enumerate(
        ("FUTURE-2", "TPL-4", "PLACE-1", "PLACE-1", "FUTURE-1")
    )]
    data = json.loads(report.render_json(findings, tmp_path))
    assert [item["issue"] for item in data] == ["2", "3", "1", "4", "0"]
    assert data[-1]["rule_title"] == "FUTURE-2"


def test_json_relative_root_and_absolute_location(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    data = json.loads(report.render_json([_finding(path=tmp_path / "environments/a.yml")], Path(".")))
    assert data[0]["files"] == ["environments/a.yml:3:3"]


@pytest.mark.parametrize("console", [False, True])
def test_cli_creates_both_reports_with_grouped_findings(repo, console):
    repo.env("cluster-a", "env-a", deploy={"cloud": ["service-deploy"]})
    repo.env("cluster-a", "env-b", deploy={"cloud": ["service-deploy"]})
    for env in ("env-a", "env-b"):
        repo.env_paramset("cluster-a", env, "service-deploy", {"LOG_LEVEL": "info"})
    args = ["check", str(repo.root)] + (["--console"] if console else [])

    result = CliRunner(mix_stderr=False).invoke(main, args)

    assert result.exit_code == 0, result.output
    path = repo.root / "envgene-linter-report.json"
    assert path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    place1 = [item for item in data if item["rule_id"] == "PLACE-1"]
    assert len(place1) == 1
    assert place1[0]["files"] == [
        "environments/cluster-a/env-a/Inventory/parameters/service-deploy.yml:3:3",
        "environments/cluster-a/env-b/Inventory/parameters/service-deploy.yml:3:3",
    ]
    html = (repo.root / "envgene-linter-report.html").read_text(encoding="utf-8")
    assert html.count('class="finding"') == len(data)
    assert f"HTML report saved here: {repo.root / 'envgene-linter-report.html'}" in result.stderr
    assert f"JSON report saved here: {path}" in result.stderr
    assert all("type" not in item for item in data)
    assert ("PLACE-1" in result.stdout) == console


@pytest.mark.parametrize("existing", ["*.pyc", "/envgene-linter-report.html\n", "/envgene-linter-report.json\n"])
def test_cli_adds_both_ignore_entries_once_and_preserves_existing(repo, existing):
    (repo.root / "templates").mkdir()
    gitignore = repo.root / ".gitignore"
    gitignore.write_text(existing, encoding="utf-8")
    runner = CliRunner()
    for _ in range(2):
        result = runner.invoke(main, ["check", str(repo.root)])
        assert result.exit_code == 0, result.output
    text = gitignore.read_text(encoding="utf-8")
    assert text.startswith(existing)
    names = [line.lstrip("/") for line in text.splitlines()]
    assert names.count("envgene-linter-report.html") == 1
    assert names.count("envgene-linter-report.json") == 1


def test_cli_replaces_json_with_empty_array_when_rules_disabled(repo, monkeypatch):
    (repo.root / "templates").mkdir()
    monkeypatch.setattr(rule_config, "RULE_ENABLED", dict.fromkeys(rule_config.RULE_ENABLED, False))
    path = repo.root / "envgene-linter-report.json"
    path.write_text('[{"old": true}]', encoding="utf-8")
    monkeypatch.chdir(repo.root)
    result = CliRunner().invoke(main, ["check"])
    assert result.exit_code == 0, result.output
    assert json.loads(path.read_text(encoding="utf-8")) == []


@pytest.mark.parametrize("args", [[], ["--console"]])
def test_cli_json_write_failure_exits_two_without_success_notice(repo, args):
    (repo.root / "templates").mkdir()
    (repo.root / "envgene-linter-report.json").mkdir()
    result = CliRunner(mix_stderr=False).invoke(main, ["check", str(repo.root), *args])
    assert result.exit_code == 2
    assert "cannot write JSON report" in result.stderr
    assert "report saved here:" not in result.stderr
    assert "Traceback" not in result.stderr


def test_cli_json_keeps_sec5_redaction(repo):
    repo.env("cluster-a", "env-a")
    path = repo.root / "environments/cluster-a/env-a/Credentials/credentials.yml"
    path.parent.mkdir(parents=True)
    path.write_text("private-identifier:\n  type: secret\n  data:\n    secret: synthetic-private-secret\n")
    result = CliRunner().invoke(main, ["check", str(repo.root)])
    assert result.exit_code == 0, result.output
    output = (repo.root / "envgene-linter-report.json").read_text(encoding="utf-8")
    assert any(item["rule_id"] == "SEC-5" for item in json.loads(output))
    assert "private-identifier" not in output
    assert "synthetic-private-secret" not in output
