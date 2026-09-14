from envgene_linter.discovery import build_index
from envgene_linter.effective import ALL_LAYERS, LOWER_LAYERS, SITE_LAYERS, compute
from envgene_linter.model import Category, Layer, Scope
from envgene_linter.passport import build_catalogs
from envgene_linter.rules.place1 import check
from envgene_linter.yamlio import load


def _place1(repo):
    index = build_index(repo.root)
    full = {env.full_name: compute(index, env, ALL_LAYERS) for env in index.environments}
    lower = {env.full_name: compute(index, env, LOWER_LAYERS) for env in index.environments}
    site = {env.full_name: compute(index, env, SITE_LAYERS) for env in index.environments}
    return check(index, full, lower, site)


def test_value_repeated_in_every_environment_should_move_to_the_cluster(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["env-params"]})
    repo.env("cluster-01", "env-02", deploy={"cloud": ["env-params"]})
    repo.env_paramset("cluster-01", "env-01", "env-params", {"MONITORING_URL": "https://m.example.com"})
    repo.env_paramset("cluster-01", "env-02", "env-params", {"MONITORING_URL": "https://m.example.com"})
    findings = _place1(repo)
    assert len(findings) == 1
    assert findings[0].key == "MONITORING_URL"
    assert findings[0].rule == "PLACE-1"
    assert findings[0].path.parts[-4] == "env-01"
    assert "environments/cluster-01/parameters/" in findings[0].hint
    assert len(findings[0].related) == 2
    assert findings[0].message == (
        "Key MONITORING_URL has the same value in 2 environments of cluster cluster-01."
    )
    assert findings[0].hint == (
        "Move MONITORING_URL to environments/cluster-01/parameters/ "
        "and remove the environment copies."
    )
    loaded = load(findings[0].path)
    _, col = loaded.position(("parameters", "MONITORING_URL"))
    assert findings[0].column == col
    assert findings[0].issue_type.value == "Warning"
    assert findings[0].action.value == "Fix"
    assert len(findings[0].locations) == 2
    assert findings[0].locations[0].path == findings[0].path
    paths = {item.path.name for item in findings[0].locations}
    assert paths == {"env-params.yml"}
    env_dirs = {item.path.parts[-4] for item in findings[0].locations}
    assert env_dirs == {"env-01", "env-02"}


def test_differing_values_are_a_genuine_difference(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["env-params"]})
    repo.env("cluster-01", "env-02", deploy={"cloud": ["env-params"]})
    repo.env_paramset("cluster-01", "env-01", "env-params", {"REPLICAS": 2})
    repo.env_paramset("cluster-01", "env-02", "env-params", {"REPLICAS": 3})
    assert _place1(repo) == []


def test_a_single_environment_is_not_enough(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["env-params"]})
    repo.env_paramset("cluster-01", "env-01", "env-params", {"REPLICAS": 2})
    assert _place1(repo) == []


def test_environments_that_do_not_resolve_the_scope_are_not_participants(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["env-params"]})
    repo.env("cluster-01", "env-02", deploy={"cloud": ["env-params"]})
    repo.env("cluster-01", "env-03")
    repo.env_paramset("cluster-01", "env-01", "env-params", {"REPLICAS": 2})
    repo.env_paramset("cluster-01", "env-02", "env-params", {"REPLICAS": 2})
    assert len(_place1(repo)) == 1


def test_plain_restatement_is_not_place1(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["shared", "env-params"]})
    repo.env("cluster-01", "env-02", deploy={"cloud": ["shared", "env-params"]})
    repo.cluster_paramset("cluster-01", "shared", {"KEY": "same"})
    repo.env_paramset("cluster-01", "env-01", "env-params", {"KEY": "same"})
    repo.env_paramset("cluster-01", "env-02", "env-params", {"KEY": "same"})
    assert _place1(repo) == []


def test_stale_cluster_value_overridden_identically_everywhere(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["shared", "env-params"]})
    repo.env("cluster-01", "env-02", deploy={"cloud": ["shared", "env-params"]})
    repo.cluster_paramset("cluster-01", "shared", {"KEY": "stale"})
    repo.env_paramset("cluster-01", "env-01", "env-params", {"KEY": "current"})
    repo.env_paramset("cluster-01", "env-02", "env-params", {"KEY": "current"})
    assert [item.key for item in _place1(repo)] == ["KEY"]


def test_value_repeated_in_every_cluster_should_move_to_the_repository(repo):
    for cluster in ("cluster-01", "cluster-02"):
        repo.env(cluster, "env-01", e2e={"cloud": ["cloud-params"]})
        repo.cluster_paramset(cluster, "cloud-params", {"E2E_BASE_URL": "https://e2e.example.com"})
    findings = _place1(repo)
    assert len(findings) == 1
    assert findings[0].key == "E2E_BASE_URL"
    assert findings[0].scope.startswith("repository ")
    assert findings[0].message == "Key E2E_BASE_URL has the same value in 2 clusters."
    assert findings[0].hint == (
        "Move E2E_BASE_URL to a repository paramset and remove the cluster copies."
    )
    assert len(findings[0].locations) == 2


def test_disagreeing_clusters_do_not_hoist(repo):
    repo.env("cluster-01", "env-01", e2e={"cloud": ["cloud-params"]})
    repo.cluster_paramset("cluster-01", "cloud-params", {"KEY": "same"})
    repo.env("cluster-02", "env-01", e2e={"cloud": ["cloud-params"]})
    repo.cluster_paramset("cluster-02", "cloud-params", {"KEY": "different"})
    assert _place1(repo) == []


def test_cluster_file_shadowing_site_file_makes_both_cluster_keys_hoistable(repo):
    repo.site_paramset("cloud", {"COMMON_FROM_SITE": "shared"})
    for cluster in ("cluster-01", "cluster-02"):
        repo.env(cluster, "env-01", deploy={"cloud": ["cloud"]})
        repo.cluster_paramset(
            cluster, "cloud", {"COMMON_FROM_SITE": "shared", "CLUSTER_ONLY": "same"}
        )
    findings = _place1(repo)
    assert [item.key for item in findings] == ["CLUSTER_ONLY", "COMMON_FROM_SITE"]
    index = build_index(repo.root)
    env = index.environments[0]
    site = compute(index, env, SITE_LAYERS)
    scope = Scope("cloud", Category.DEPLOY)
    assert site.get(scope, ("COMMON_FROM_SITE",)) is None


def test_catalog_key_is_not_hoisted_to_cluster(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["env-params"]})
    repo.env("cluster-01", "env-02", deploy={"cloud": ["env-params"]})
    repo.env_paramset("cluster-01", "env-01", "env-params", {"DBAAS_AGGREGATOR_ADDRESS": "https://dbaas.example"})
    repo.env_paramset("cluster-01", "env-02", "env-params", {"DBAAS_AGGREGATOR_ADDRESS": "https://dbaas.example"})
    index = build_index(repo.root)
    full = {env.full_name: compute(index, env, ALL_LAYERS) for env in index.environments}
    lower = {env.full_name: compute(index, env, LOWER_LAYERS) for env in index.environments}
    site = {env.full_name: compute(index, env, SITE_LAYERS) for env in index.environments}
    findings = check(index, full, lower, site, build_catalogs(index))
    assert findings == []


def test_catalog_key_is_not_hoisted_to_repository(repo):
    for cluster in ("cluster-01", "cluster-02"):
        repo.env(cluster, "env-01", deploy={"cloud": ["cloud-params"]})
        repo.cluster_paramset(cluster, "cloud-params", {"DBAAS_AGGREGATOR_ADDRESS": "https://dbaas.example"})
    index = build_index(repo.root)
    full = {env.full_name: compute(index, env, ALL_LAYERS) for env in index.environments}
    lower = {env.full_name: compute(index, env, LOWER_LAYERS) for env in index.environments}
    site = {env.full_name: compute(index, env, SITE_LAYERS) for env in index.environments}
    findings = check(index, full, lower, site, build_catalogs(index))
    assert findings == []
