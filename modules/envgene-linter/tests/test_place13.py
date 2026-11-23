from pathlib import Path

from envgene_linter.connections import compute_connections
from envgene_linter.discovery import build_index
from envgene_linter.effective import compute
from envgene_linter.engine import run_check
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
        ("demo-cluster/demo-env", "role", Action.REVIEW, "shared-deploy.yml"),
        ("demo-cluster/demo-env", "role", Action.REVIEW, "gamma-deploy.yml"),
        ("demo-cluster/other-env", "role", Action.REVIEW, "shared-deploy.yml"),
    }
    assert not any(item.key in {"replicaCount", "traceToken", "CLOUD_API_HOST"} for item in findings)


def test_move_hint_names_the_accepting_application():
    findings = _findings(ROOT / "instance")
    hint = next(item.hint for item in findings if item.key == "config.message")
    assert "*-sample-alpha-deploy" in hint
    assert "records" in hint


def test_missing_catalog_marks_place13_not_applicable(tmp_path):
    (tmp_path / "environments" / "demo-cluster" / "demo-env" / "Inventory").mkdir(parents=True)
    (tmp_path / "environments" / "demo-cluster" / "demo-env" / "Inventory" / "env_definition.yml").write_text(
        "inventory:\n  environmentName: demo-env\nenvTemplate:\n  name: composite\n",
        encoding="utf-8",
    )
    result = run_check(tmp_path)
    assert result.not_applicable_rules == ("PLACE-13",)
    assert not any(item.rule == "PLACE-13" for item in result.findings)
