from envgene_linter.discovery import build_index
from envgene_linter.effective import ALL_LAYERS, LOWER_LAYERS, SITE_LAYERS, compute
from envgene_linter.passport import build_catalogs
from envgene_linter.rules.place3 import check


def _place3(repo):
    index = build_index(repo.root)
    catalogs = build_catalogs(index)
    full = {env.full_name: compute(index, env, ALL_LAYERS) for env in index.environments}
    lower = {env.full_name: compute(index, env, LOWER_LAYERS) for env in index.environments}
    site = {env.full_name: compute(index, env, SITE_LAYERS) for env in index.environments}
    return check(index, full, lower, site, catalogs)


def test_passport_file_at_environments_root_is_a_finding(repo):
    repo.env(
        "cluster-01", "env-01", deploy={"cloud": ["env-params"]}, cloud_passport="passport"
    )
    repo.passport("passport", {"cloud": {"CLOUD_API_HOST": "api.example"}}, cluster=None)
    repo.env_paramset("cluster-01", "env-01", "env-params", {"TENANT": "acme"})
    findings = [item for item in _place3(repo) if "passport" in item.message.lower() or item.path.name == "passport.yml"]
    assert len(findings) == 1
    assert findings[0].rule == "PLACE-3"
    assert findings[0].message == "Passport passport is not at the cluster layer."
    assert findings[0].column == 1
    assert "cluster" in findings[0].hint.lower()
    assert "<cluster>" not in findings[0].hint


def test_passport_file_under_env_inventory_is_a_finding(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["env-params"]}, cloud_passport="passport")
    repo.passport("passport", {"cloud": {"CLOUD_API_HOST": "api.example"}}, cluster="cluster-01", env="env-01")
    repo.env_paramset("cluster-01", "env-01", "env-params", {"TENANT": "acme"})
    findings = _place3(repo)
    assert len(findings) == 1
    assert findings[0].rule == "PLACE-3"
    assert findings[0].path.name == "passport.yml"


def test_passport_file_on_cluster_is_silent(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["env-params"]})
    repo.passport("passport", {"cloud": {"CLOUD_API_HOST": "api.example"}}, cluster="cluster-01")
    repo.env_paramset("cluster-01", "env-01", "env-params", {"TENANT": "acme"})
    assert [item for item in _place3(repo) if item.path.name == "passport.yml"] == []


def test_jinja_passport_under_environments_is_a_file_finding(repo):
    repo.env(
        "cluster-01", "env-01", deploy={"cloud": ["env-params"]}, cloud_passport="passport"
    )
    repo.env_paramset("cluster-01", "env-01", "env-params", {"TENANT": "acme"})
    directory = repo.root / "environments" / "cloud-passport"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "passport.yml.j2").write_text("cloud:\n  CLOUD_API_HOST: {{ host }}\n", encoding="utf-8")
    findings = [item for item in _place3(repo) if item.path.name == "passport.yml.j2"]
    assert len(findings) == 1
    assert findings[0].rule == "PLACE-3"
    assert "<cluster>" not in findings[0].hint


def test_unreadable_passport_under_environments_is_a_file_finding(repo):
    repo.env(
        "cluster-01", "env-01", deploy={"cloud": ["env-params"]}, cloud_passport="passport"
    )
    repo.env_paramset("cluster-01", "env-01", "env-params", {"TENANT": "acme"})
    directory = repo.root / "environments" / "cloud-passport"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "passport.yml").write_text("[:\n", encoding="utf-8")
    findings = [item for item in _place3(repo) if item.path.name == "passport.yml"]
    assert len(findings) == 1
    assert findings[0].rule == "PLACE-3"
    assert "<cluster>" not in findings[0].hint


def test_unselected_misplaced_passport_is_ignored(repo):
    repo.env("cluster-01", "env-01")
    repo.passport("unused", {"cloud": {"CLOUD_API_HOST": "api.example"}})
    assert _place3(repo) == []
