from envgene_linter.discovery import build_index
from envgene_linter.model import Action, IssueType, Severity
from envgene_linter.rules.name4 import check

_HINT = (
    "Review whether this stem can be <subject>-<category>. "
    "Do not rename it if env_definition or other logic still depends on the current spelling."
)


def _name4(repo):
    return check(build_index(repo.root))


def test_bound_bss_needs_deploy_suffix(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["bss"]})
    repo.env_paramset("cluster-01", "env-01", "bss", {"LOG_LEVEL": "info"})
    findings = _name4(repo)
    assert len(findings) == 1
    item = findings[0]
    assert item.rule == "NAME-4"
    assert item.severity is Severity.INFORMATION
    assert item.issue_type is IssueType.INFORMATION
    assert item.action is Action.REVIEW
    assert item.key == "bss"
    assert item.scope == "deploy"
    assert item.message == (
        "ParameterSet 'bss' must end with -deploy to match its env_definition binding (deploy)."
    )
    assert item.hint == _HINT


def test_bound_bss_deploy_is_silent(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["bss-deploy"]})
    repo.env_paramset("cluster-01", "env-01", "bss-deploy", {"LOG_LEVEL": "info"})
    assert _name4(repo) == []


def test_e2e_pipeline_suffix_is_silent(repo):
    repo.env("cluster-01", "env-01", e2e={"cloud": ["postgresql-pipeline"]})
    repo.env_paramset("cluster-01", "env-01", "postgresql-pipeline", {"E2E_URL": "https://e2e"})
    assert _name4(repo) == []


def test_e2e_deploy_suffix_is_reported(repo):
    repo.env("cluster-01", "env-01", e2e={"cloud": ["postgresql-deploy"]})
    repo.env_paramset("cluster-01", "env-01", "postgresql-deploy", {"E2E_URL": "https://e2e"})
    findings = _name4(repo)
    assert len(findings) == 1
    assert findings[0].scope == "pipeline"
    assert findings[0].message == (
        "ParameterSet 'postgresql-deploy' must end with -pipeline "
        "to match its env_definition binding (pipeline)."
    )


def test_technical_suffix_is_silent(repo):
    repo.env("cluster-01", "env-01", technical={"cloud": ["postgresql-technical"]})
    repo.env_paramset("cluster-01", "env-01", "postgresql-technical", {"T": 1})
    assert _name4(repo) == []


def test_topology_after_category_is_reported(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["postgresql-deploy-ha"]})
    repo.env_paramset("cluster-01", "env-01", "postgresql-deploy-ha", {"LOG_LEVEL": "info"})
    assert len(_name4(repo)) == 1


def test_bare_category_needs_subject(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["deploy"]})
    repo.env_paramset("cluster-01", "env-01", "deploy", {"LOG_LEVEL": "info"})
    assert len(_name4(repo)) == 1


def test_leading_hyphen_needs_subject(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["-deploy"]})
    repo.env_paramset("cluster-01", "env-01", "-deploy", {"LOG_LEVEL": "info"})
    findings = _name4(repo)
    assert len(findings) == 1
    assert findings[0].key == "-deploy"
    assert findings[0].scope == "deploy"
    assert findings[0].message == (
        "ParameterSet '-deploy' must end with -deploy to match its env_definition binding (deploy)."
    )


def test_env_name_in_stem_is_reported(repo):
    repo.env("cluster-01", "qa01", deploy={"cloud": ["qa01-bss-deploy"]})
    repo.env_paramset("cluster-01", "qa01", "qa01-bss-deploy", {"LOG_LEVEL": "info"})
    findings = _name4(repo)
    assert len(findings) == 1
    assert findings[0].message == (
        "ParameterSet 'qa01-bss-deploy' bakes a cluster, environment, ticket or release into the name."
    )


def test_ticket_in_stem_is_reported(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["bss-ticket-12-deploy"]})
    repo.env_paramset("cluster-01", "env-01", "bss-ticket-12-deploy", {"LOG_LEVEL": "info"})
    assert _name4(repo)[0].message.startswith("ParameterSet 'bss-ticket-12-deploy' bakes")


def test_unbound_file_is_silent(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["bss-deploy"]})
    repo.env_paramset("cluster-01", "env-01", "bss-deploy", {"LOG_LEVEL": "info"})
    repo.site_paramset("extra", {"X": 1})
    assert all(item.key != "extra" for item in _name4(repo))


def test_same_stem_two_selected_physical_files_each_get_one_finding(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["bss"]})
    repo.site_paramset("bss", {"S": 1})
    repo.env_paramset("cluster-01", "env-01", "bss", {"E": 1})
    findings = _name4(repo)
    assert len(findings) == 2
    assert {item.path for item in findings} == {
        repo.root / "environments/parameters/bss.yml",
        repo.root / "environments/cluster-01/env-01/Inventory/parameters/bss.yml",
    }


def test_jinja_bound_stem_is_ignored(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["foo"]})
    path = (
        repo.root
        / "environments/cluster-01/env-01/Inventory/parameters/foo.yml.j2"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("name: foo\nparameters:\n  K: v\n", encoding="utf-8")
    assert _name4(repo) == []


def test_same_stem_physical_files_keep_separate_categories_and_owners(repo):
    repo.env("cluster-a", "env-a", deploy={"cloud": ["shared"]})
    repo.env("cluster-b", "env-b", technical={"cloud": ["shared"]})
    repo.env_paramset("cluster-a", "env-a", "shared", {"A": 1})
    repo.env_paramset("cluster-b", "env-b", "shared", {"B": 1})

    findings = _name4(repo)

    assert [(item.path.parts[-5:-3], item.scope) for item in findings] == [
        (("cluster-a", "env-a"), "deploy"),
        (("cluster-b", "env-b"), "technical"),
    ]
