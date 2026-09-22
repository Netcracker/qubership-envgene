from envgene_linter.discovery import build_index
from envgene_linter.model import Action, IssueType, Severity
from envgene_linter.rules.name2 import check


def _name2(repo):
    return check(build_index(repo.root))


def test_matching_paramset_name_is_silent(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    repo.env_paramset("cluster-01", "env-01", "cloud-deploy", {"LOG_LEVEL": "info"})
    assert _name2(repo) == []


def test_mismatch_paramset_is_warning_fix(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    path = (
        repo.root / "environments/cluster-01/env-01/Inventory/parameters/cloud-deploy.yml"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "name: deploy-params\nparameters:\n  LOG_LEVEL: info\n",
        encoding="utf-8",
    )
    findings = _name2(repo)
    assert len(findings) == 1
    item = findings[0]
    assert item.rule == "NAME-2"
    assert item.severity is Severity.WARNING
    assert item.issue_type is IssueType.WARNING
    assert item.action is Action.FIX
    assert item.key == "name"
    assert item.scope == "cloud-deploy"
    assert item.message == (
        "ParameterSet filename stem 'cloud-deploy' does not equal the name field "
        "'deploy-params'."
    )
    assert item.hint == (
        "Set name: cloud-deploy to match the filename, which is the reference key."
    )
    assert len(item.locations) == 1


def test_missing_paramset_name_is_information(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    path = (
        repo.root / "environments/cluster-01/env-01/Inventory/parameters/cloud-deploy.yml"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("parameters:\n  LOG_LEVEL: info\n", encoding="utf-8")
    findings = _name2(repo)
    assert len(findings) == 1
    item = findings[0]
    assert item.severity is Severity.INFORMATION
    assert item.issue_type is IssueType.INFORMATION
    assert item.action is Action.REVIEW
    assert item.message == (
        "ParameterSet cloud-deploy.yml has no name field; EnvGene requires it to "
        "equal the filename stem 'cloud-deploy'."
    )
    assert item.hint == "Set name: cloud-deploy"


def test_empty_paramset_name_is_information(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    path = (
        repo.root / "environments/cluster-01/env-01/Inventory/parameters/cloud-deploy.yml"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("name: \"\"\nparameters:\n  LOG_LEVEL: info\n", encoding="utf-8")
    findings = _name2(repo)
    assert len(findings) == 1
    assert findings[0].severity is Severity.INFORMATION
    assert findings[0].action is Action.REVIEW


def test_orphan_paramset_mismatch_is_ignored(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["bound"]})
    repo.env_paramset("cluster-01", "env-01", "bound", {"KEEP": "ok"})
    path = (
        repo.root / "environments/cluster-01/env-01/Inventory/parameters/orphan.yml"
    )
    path.write_text("name: other\nparameters:\n  KEEP: ok\n", encoding="utf-8")
    assert _name2(repo) == []


def test_jinja_paramset_is_skipped(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    jinja = (
        repo.root
        / "environments/cluster-01/env-01/Inventory/parameters/cloud-deploy.yml.j2"
    )
    jinja.parent.mkdir(parents=True, exist_ok=True)
    jinja.write_text(
        "name: other\nparameters:\n  LOG_LEVEL: info\n",
        encoding="utf-8",
    )
    assert _name2(repo) == []


def test_load_error_paramset_is_skipped(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["ok"]})
    repo.env_paramset("cluster-01", "env-01", "ok", {"A": 1})
    bad = repo.root / "environments/cluster-01/env-01/Inventory/parameters/bad.yml"
    bad.write_bytes(b"\xff\xfe not utf-8")
    assert _name2(repo) == []


def test_selected_artifact_definition_mismatch(repo):
    repo.env(
        "cluster-01",
        "env-01",
        deploy={"cloud": ["cloud-deploy"]},
        artifact="test:1.0",
    )
    repo.env_paramset("cluster-01", "env-01", "cloud-deploy", {"LOG_LEVEL": "info"})
    path = repo.root / "configuration/artifact_definitions/test.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "name: qubership_envgene_templates\ngroupId: org.qubership\n",
        encoding="utf-8",
    )
    findings = _name2(repo)
    assert len(findings) == 1
    assert findings[0].scope == "test"
    assert "Artifact definition" in findings[0].message
    assert "qubership_envgene_templates" in findings[0].message


def test_unselected_artifact_definition_mismatch_is_ignored(repo):
    repo.env("cluster-01", "env-01")
    path = repo.root / "configuration/artifact_definitions/test.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("name: wrong\n", encoding="utf-8")
    assert _name2(repo) == []


def test_matching_application_definition_is_silent(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    repo.env_paramset("cluster-01", "env-01", "cloud-deploy", {"LOG_LEVEL": "info"})
    path = repo.root / "appdefs/billing.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("name: billing\n", encoding="utf-8")
    assert _name2(repo) == []


def test_unproven_application_and_registry_definitions_are_ignored(repo):
    repo.env("cluster-01", "env-01", artifact="template:1")
    artifact = repo.root / "configuration/artifact_definitions/template.yml"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("name: template\n", encoding="utf-8")
    for relative in ("appdefs/application.yml", "regdefs/registry.yml"):
        path = repo.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("name: wrong\n", encoding="utf-8")
    assert _name2(repo) == []


def test_malformed_yml_artifact_wins_without_yaml_fallback(repo):
    repo.env("cluster-01", "env-01", artifact="template:1")
    directory = repo.root / "configuration/artifact_definitions"
    directory.mkdir(parents=True)
    (directory / "template.yml").write_text("not: [valid\n", encoding="utf-8")
    (directory / "template.yaml").write_text("name: wrong\n", encoding="utf-8")
    assert _name2(repo) == []
