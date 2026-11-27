from envgene_linter.discovery import build_index
from envgene_linter.model import Action, IssueType, Location, Severity
from envgene_linter.rules.place6 import check

_MESSAGE = (
    "{target} is not the Cloud; pipeline ParameterSets must bind under "
    "envSpecificE2EParamsets.cloud."
)
_HINT = "Move the envSpecificE2EParamsets.{target} list to cloud."


def _place6(repo):
    return check(build_index(repo.root))


def test_e2e_bound_to_namespace_is_a_finding(repo):
    repo.env("cluster-01", "env-01", e2e={"bss": ["env-1-pipeline"]})
    repo.env_paramset("cluster-01", "env-01", "env-1-pipeline", {"E2E": 1})
    findings = _place6(repo)
    assert len(findings) == 1
    item = findings[0]
    assert item.rule == "PLACE-6"
    assert item.severity is Severity.WARNING
    assert item.issue_type is IssueType.WARNING
    assert item.action is Action.FIX
    assert item.key == "bss"
    assert item.scope == "cluster-01/env-01"
    assert item.message == _MESSAGE.format(target="bss")
    assert item.hint == _HINT.format(target="bss")
    assert item.related == ()
    assert item.path.name == "env_definition.yml"
    assert item.line == 6
    assert item.column == 5
    assert item.locations == (Location(item.path, item.line, item.column),)


def test_e2e_bound_to_cloud_is_silent(repo):
    repo.env("cluster-01", "env-01", e2e={"cloud": ["env-1-pipeline"]})
    assert _place6(repo) == []


def test_e2e_bound_to_cloud_any_case_is_silent(repo):
    repo.env("cluster-01", "env-01", e2e={"Cloud": ["env-1-pipeline"]})
    assert _place6(repo) == []


def test_no_e2e_block_is_silent(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    assert _place6(repo) == []


def test_two_stems_under_one_namespace_are_one_finding(repo):
    repo.env("cluster-01", "env-01", e2e={"bss": ["a-pipeline", "b-pipeline"]})
    repo.env_paramset("cluster-01", "env-01", "b-pipeline", {"E2E": 1})
    findings = _place6(repo)
    assert len(findings) == 1
    assert findings[0].key == "bss"


def test_two_namespace_targets_are_two_findings(repo):
    repo.env("cluster-01", "env-01", e2e={"bss": ["a-pipeline"], "oss": ["b-pipeline"]})
    repo.env_paramset("cluster-01", "env-01", "a-pipeline", {"E2E": 1})
    repo.env_paramset("cluster-01", "env-01", "b-pipeline", {"E2E": 1})
    findings = _place6(repo)
    assert {item.key for item in findings} == {"bss", "oss"}
    assert len(findings) == 2


def test_cloud_plus_namespace_reports_only_namespace(repo):
    repo.env(
        "cluster-01",
        "env-01",
        e2e={"cloud": ["env-1-pipeline"], "bss": ["bss-pipeline"]},
    )
    repo.env_paramset("cluster-01", "env-01", "bss-pipeline", {"E2E": 1})
    findings = _place6(repo)
    assert len(findings) == 1
    assert findings[0].key == "bss"


def test_two_envs_are_two_findings(repo):
    repo.env("cluster-01", "env-01", e2e={"bss": ["env-1-pipeline"]})
    repo.env("cluster-01", "env-02", e2e={"bss": ["env-2-pipeline"]})
    repo.env_paramset("cluster-01", "env-01", "env-1-pipeline", {"E2E": 1})
    repo.env_paramset("cluster-01", "env-02", "env-2-pipeline", {"E2E": 1})
    findings = _place6(repo)
    assert len(findings) == 2
    assert {item.scope for item in findings} == {"cluster-01/env-01", "cluster-01/env-02"}


def test_non_cloud_target_with_only_unresolved_references_is_silent(repo):
    repo.env("cluster-01", "env-01", e2e={"bss": ["missing"]})
    assert _place6(repo) == []
