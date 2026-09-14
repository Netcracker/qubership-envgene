from envgene_linter.discovery import build_index
from envgene_linter.effective import ALL_LAYERS, LOWER_LAYERS, SITE_LAYERS, compute
from envgene_linter.engine import run_check
from envgene_linter.rules.place2 import check


def _place2(repo):
    index = build_index(repo.root)
    full = {env.full_name: compute(index, env, ALL_LAYERS) for env in index.environments}
    lower = {env.full_name: compute(index, env, LOWER_LAYERS) for env in index.environments}
    site = {env.full_name: compute(index, env, SITE_LAYERS) for env in index.environments}
    return check(index, full, lower, site)


def test_env_copying_cluster_is_a_finding(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["shared", "env-params"]})
    repo.cluster_paramset("cluster-01", "shared", {"LOG_LEVEL": "info", "REPLICA_COUNT": 2})
    repo.env_paramset(
        "cluster-01", "env-01", "env-params", {"LOG_LEVEL": "info", "REPLICA_COUNT": 3}
    )
    findings = _place2(repo)
    assert len(findings) == 1
    assert findings[0].rule == "PLACE-2"
    assert findings[0].key == "LOG_LEVEL"
    assert "environment" in findings[0].message
    assert "Remove LOG_LEVEL" in findings[0].hint
    assert findings[0].message == (
        "Key LOG_LEVEL at the environment layer repeats the lower-layer value."
    )
    assert findings[0].hint == (
        "Remove LOG_LEVEL from this file, or change the value if the override is intentional."
    )
    assert findings[0].locations == ()


def test_different_value_is_silent(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["shared", "env-params"]})
    repo.cluster_paramset("cluster-01", "shared", {"REPLICA_COUNT": 2})
    repo.env_paramset("cluster-01", "env-01", "env-params", {"REPLICA_COUNT": 3})
    assert _place2(repo) == []


def test_key_absent_below_is_silent(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["env-params"]})
    repo.env_paramset("cluster-01", "env-01", "env-params", {"ONLY_HERE": 1})
    assert _place2(repo) == []


def test_cluster_copying_repository_is_a_finding(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["shared"]})
    site = repo.root / "environments/parameters/shared.yaml"
    site.parent.mkdir(parents=True, exist_ok=True)
    site.write_text("name: shared\nparameters:\n  LOG_LEVEL: info\n", encoding="utf-8")
    repo.cluster_paramset("cluster-01", "shared", {"LOG_LEVEL": "info"})
    findings = _place2(repo)
    assert len(findings) == 1
    assert findings[0].key == "LOG_LEVEL"
    assert "cluster" in findings[0].message


def test_two_envs_share_one_cluster_restatement(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["shared"]})
    repo.env("cluster-01", "env-02", deploy={"cloud": ["shared"]})
    site = repo.root / "environments/parameters/shared.yaml"
    site.parent.mkdir(parents=True, exist_ok=True)
    site.write_text("name: shared\nparameters:\n  LOG_LEVEL: info\n", encoding="utf-8")
    repo.cluster_paramset("cluster-01", "shared", {"LOG_LEVEL": "info"})
    findings = _place2(repo)
    assert len(findings) == 1


def test_same_file_bound_under_two_targets_is_one_finding(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["shared"], "bss": ["shared"]})
    site = repo.root / "environments/parameters/shared.yaml"
    site.parent.mkdir(parents=True, exist_ok=True)
    site.write_text("name: shared\nparameters:\n  LOG_LEVEL: info\n", encoding="utf-8")
    repo.cluster_paramset("cluster-01", "shared", {"LOG_LEVEL": "info"})
    findings = _place2(repo)
    assert len(findings) == 1
    assert findings[0].rule == "PLACE-2"
    assert findings[0].key == "LOG_LEVEL"


def test_restated_env_key_is_place2_not_place1(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["shared", "env-params"]})
    repo.env("cluster-01", "env-02", deploy={"cloud": ["shared", "env-params"]})
    repo.cluster_paramset("cluster-01", "shared", {"LOG_LEVEL": "info"})
    repo.env_paramset("cluster-01", "env-01", "env-params", {"LOG_LEVEL": "info"})
    repo.env_paramset("cluster-01", "env-02", "env-params", {"LOG_LEVEL": "info"})
    result = run_check(repo.root)
    place2 = [item for item in result.findings if item.rule == "PLACE-2" and item.key == "LOG_LEVEL"]
    place1 = [item for item in result.findings if item.rule == "PLACE-1" and item.key == "LOG_LEVEL"]
    assert len(place2) == 2
    assert place1 == []
