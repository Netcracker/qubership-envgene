from pathlib import Path

from envgene_linter.connections import compute_connections
from envgene_linter.discovery import build_index
from envgene_linter.effective import compute
from envgene_linter.engine import run_check
from envgene_linter.html_report import render_html
from envgene_linter.model import Action
from envgene_linter.rules.place13 import check

ROOT = Path(__file__).resolve().parent.parent / "testdata" / "rules" / "place13"
CATALOG = ROOT / "helm-parameter-catalog"


def _findings(repo: Path):
    index = build_index(repo)
    full = {env.full_name: compute(index, env) for env in index.environments}
    return check(index, full, compute_connections(index), CATALOG)


def test_fixture_covers_each_place13_outcome():
    findings = _findings(ROOT / "instance")
    seen = {(item.scope, item.key, item.action, item.path.name) for item in findings}
    assert seen == {
        ("demo-cluster/demo-env", "config.message", Action.FIX, "cloud-deploy.yml"),
        ("demo-cluster/demo-env", "extra.note", Action.FIX, "cloud-deploy.yml"),
        ("demo-cluster/demo-env", "config.path", Action.FIX, "records-deploy.yml"),
        ("demo-cluster/demo-env", "config.path", Action.REVIEW, "cloud-deploy.yml"),
        ("demo-cluster/demo-env", "legacyFlag", Action.REVIEW, "cloud-deploy.yml"),
        ("demo-cluster/demo-env, demo-cluster/other-env", "role", Action.REVIEW, "shared-deploy.yml"),
        ("demo-cluster/demo-env", "role", Action.REVIEW, "gamma-deploy.yml"),
    }
    assert not any(item.key in {"replicaCount", "traceToken", "CLOUD_API_HOST"} for item in findings)


def test_shared_review_names_environments_and_the_local_owner():
    findings = _findings(ROOT / "instance")
    shared = [item for item in findings if item.path.name == "shared-deploy.yml"]
    assert len(shared) == 1
    item = shared[0]
    assert item.scope == "demo-cluster/demo-env, demo-cluster/other-env"
    assert "**environments/demo-cluster/parameters/shared-deploy.yml**" in item.message
    assert "**demo-cluster/demo-env**" in item.message
    assert "**demo-cluster/other-env**" in item.message
    assert "This finding is for" not in item.message
    assert "In each of these environments:" in item.message
    assert item.message.count("**sample-alpha** (application) accepts **role**.") == 1
    assert "**sample-beta** (application) does not accept **role**." in item.message
    assert "every application in these environments receives it." in item.hint
    assert item.hint.count("Keep **role** on a ParameterSet for that application, in the namespace **records**.") == 1
    assert "prefix plus **-sample-alpha-deploy**" in item.hint
    assert "The linter does not choose the prefix." in item.hint
    assert "The linter does not create a separate copy of the file for each environment." in item.hint
    assert "PLACE-13" not in item.hint
    page = render_html(shared, ROOT / "instance")
    assert "<em>role</em>" in page
    assert "<em>demo-cluster/demo-env</em>" in page
    assert "<br>" in page
    assert "**" not in page


def test_missing_schema_names_the_service_and_does_not_name_the_rule():
    findings = _findings(ROOT / "instance")
    item = next(item for item in findings if item.path.name == "gamma-deploy.yml")
    assert "set for **sample-gamma** (application)" in item.message
    assert "namespace **notes**" in item.message
    assert "Value: **gamma**" in item.message
    assert "**sample-notes** (service)" in item.message
    assert "values.schema.json" in item.message
    assert "cannot tell which parameters it accepts" in item.message
    assert "PLACE-13" not in item.hint
    assert "Add values.schema.json for **sample-notes** (service)" in item.hint


def test_priority_conflict_names_both_places_and_values():
    findings = _findings(ROOT / "instance")
    item = next(item for item in findings if item.key == "config.path" and item.action is Action.REVIEW)
    assert "cloud-deploy.yml" in item.message
    assert "records-deploy.yml" in item.message
    assert "Value: **wide**" in item.message
    assert "Value: **narrow**" in item.message
    assert "namespace **records**" in item.message
    assert "because that place is more specific than the whole cloud" in item.hint
    assert "prefix plus **-sample-alpha-deploy**" in item.hint


def test_move_hint_names_the_accepting_application():
    findings = _findings(ROOT / "instance")
    item = next(item for item in findings if item.key == "config.message")
    assert "Value: **catalog**" in item.message
    assert "**sample-alpha** (application) accepts **config.message**." in item.message
    assert "**sample-beta** (application) does not accept **config.message**." in item.message
    assert "Put **config.message** on a ParameterSet for **sample-alpha** (application)" in item.hint
    assert "namespace **records**" in item.hint
    assert "prefix plus **-sample-alpha-deploy**" in item.hint
    assert "app@ns" not in item.hint
    assert "app@ns" not in item.message


def test_missing_catalog_marks_place13_not_applicable(tmp_path):
    (tmp_path / "environments" / "demo-cluster" / "demo-env" / "Inventory").mkdir(parents=True)
    (tmp_path / "environments" / "demo-cluster" / "demo-env" / "Inventory" / "env_definition.yml").write_text(
        "inventory:\n  environmentName: demo-env\nenvTemplate:\n  name: composite\n",
        encoding="utf-8",
    )
    result = run_check(tmp_path)
    assert result.not_applicable_rules == ("PLACE-13",)
    assert not any(item.rule == "PLACE-13" for item in result.findings)
