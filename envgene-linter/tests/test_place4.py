from envgene_linter.discovery import build_index
from envgene_linter.model import Action, IssueType, Severity
from envgene_linter.rules.place4 import check

_MESSAGE = "{key} is a Cloud Passport contract key; do not store it in a ParameterSet."
_HINT = (
    "Move {key} to the cluster cloud-passport, or to this environment's "
    "cloud-passport if the value is an override."
)


def _place4(repo):
    return check(build_index(repo.root))


def test_bound_cloud_deploy_with_table_key_is_a_finding(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    repo.env_paramset("cluster-01", "env-01", "cloud-deploy", {"CLOUD_API_HOST": "api.example"})
    findings = _place4(repo)
    assert len(findings) == 1
    item = findings[0]
    assert item.rule == "PLACE-4"
    assert item.severity is Severity.WARNING
    assert item.issue_type is IssueType.WARNING
    assert item.action is Action.FIX
    assert item.key == "CLOUD_API_HOST"
    assert item.scope == "cluster-01/env-01"
    assert item.message == _MESSAGE.format(key="CLOUD_API_HOST")
    assert item.hint == _HINT.format(key="CLOUD_API_HOST")
    assert item.related == ()
    assert item.path.name == "cloud-deploy.yml"
    assert item.locations == () or item.file_locations()[0].path == item.path


def test_table_key_only_in_cluster_passport_is_silent(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    repo.passport("passport", {"cloud": {"CLOUD_API_HOST": "api.example"}}, cluster="cluster-01")
    repo.env_paramset("cluster-01", "env-01", "cloud-deploy", {"TENANT": "acme"})
    assert _place4(repo) == []


def test_custom_passport_key_in_bound_file_is_silent(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    repo.passport(
        "passport",
        {"storage": {"MY_CUSTOM_HOST": "https://minio.example"}},
        cluster="cluster-01",
    )
    repo.env_paramset("cluster-01", "env-01", "cloud-deploy", {"MY_CUSTOM_HOST": "https://minio.example"})
    assert _place4(repo) == []


def test_unbound_file_with_table_key_is_silent(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    repo.env_paramset("cluster-01", "env-01", "cloud-deploy", {"TENANT": "acme"})
    repo.site_paramset("extra", {"CLOUD_API_HOST": "api.example"})
    assert _place4(repo) == []


def test_cluster_layer_table_key_is_a_finding(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["shared"]})
    repo.cluster_paramset("cluster-01", "shared", {"DBAAS_AGGREGATOR_ADDRESS": "https://dbaas.example"})
    findings = _place4(repo)
    assert len(findings) == 1
    assert findings[0].rule == "PLACE-4"
    assert findings[0].key == "DBAAS_AGGREGATOR_ADDRESS"
    assert findings[0].scope == "cluster-01"


def test_site_layer_table_key_is_a_finding(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["shared"]})
    repo.site_paramset("shared", {"DBAAS_AGGREGATOR_ADDRESS": "https://dbaas.example"})
    findings = _place4(repo)
    assert len(findings) == 1
    assert findings[0].rule == "PLACE-4"
    assert findings[0].key == "DBAAS_AGGREGATOR_ADDRESS"
    assert findings[0].scope == "repository"


def test_two_table_keys_in_one_file_are_two_findings(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    repo.env_paramset(
        "cluster-01",
        "env-01",
        "cloud-deploy",
        {"CLOUD_API_HOST": "api.example", "VAULT_ADDR": "https://vault.example"},
    )
    findings = _place4(repo)
    assert {item.key for item in findings} == {"CLOUD_API_HOST", "VAULT_ADDR"}
    assert all(item.rule == "PLACE-4" for item in findings)


def test_nested_children_of_one_top_key_are_one_finding(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    path = (
        repo.root / "environments/cluster-01/env-01/Inventory/parameters/cloud-deploy.yml"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "name: cloud-deploy\n"
        "parameters:\n"
        "  CLOUD_API_HOST:\n"
        "    primary: api.example\n"
        "    backup: api2.example\n",
        encoding="utf-8",
    )
    findings = _place4(repo)
    assert len(findings) == 1
    assert findings[0].key == "CLOUD_API_HOST"


def test_jinja_valid_yaml_with_table_key_is_ignored(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    path = (
        repo.root
        / "environments/cluster-01/env-01/Inventory/parameters/cloud-deploy.yml.j2"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "name: cloud-deploy\nparameters:\n  CLOUD_API_HOST: api.example\n",
        encoding="utf-8",
    )
    assert _place4(repo) == []


def test_jinja_that_does_not_parse_is_silent(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    path = (
        repo.root
        / "environments/cluster-01/env-01/Inventory/parameters/cloud-deploy.yml.j2"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("[:\n", encoding="utf-8")
    assert _place4(repo) == []


def test_same_stem_in_unrelated_cluster_does_not_establish_connection(repo):
    repo.env("cluster-a", "env-a", deploy={"cloud": ["shared"]})
    repo.env("cluster-b", "env-b")
    repo.env_paramset("cluster-a", "env-a", "shared", {"TENANT": "a"})
    repo.env_paramset("cluster-b", "env-b", "shared", {"CLOUD_API_HOST": "bad"})
    assert _place4(repo) == []
