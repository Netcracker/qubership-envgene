from envgene_linter.discovery import build_index
from envgene_linter.passport import TABLE, build_catalogs, flattened_keys, resolve_passport


def test_table_contains_mapped_effective_set_keys():
    assert "DBAAS_AGGREGATOR_ADDRESS" in TABLE
    assert "MAAS_SERVICE_ADDRESS" in TABLE
    assert "MAAS_EXTERNAL_ROUTE" in TABLE
    assert "CLOUD_DEPLOY_TOKEN" in TABLE


def test_explicit_cloud_passport_resolves(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["env-params"]}, cloud_passport="passport-infra")
    repo.passport("passport-infra", {"dbaas": {"DBAAS_AGGREGATOR_ADDRESS": "https://dbaas.example"}}, cluster="cluster-01")
    repo.env_paramset("cluster-01", "env-01", "env-params", {"TENANT": "acme"})
    index = build_index(repo.root)
    env = index.environments[0]
    assert env.cloud_passport == "passport-infra"
    resolved = resolve_passport(index, env)
    assert resolved.file is not None
    assert resolved.file.stem == "passport-infra"
    assert resolved.note is None
    catalogs = build_catalogs(index)
    assert "DBAAS_AGGREGATOR_ADDRESS" in catalogs.env[env.full_name]
    assert "TENANT" not in catalogs.env[env.full_name]


def test_auto_passport_yml_resolves(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["env-params"]})
    repo.passport("passport", {"global": {"MONITORING_ENABLED": "true"}}, cluster="cluster-01")
    repo.env_paramset("cluster-01", "env-01", "env-params", {"TENANT": "acme"})
    index = build_index(repo.root)
    resolved = resolve_passport(index, index.environments[0])
    assert resolved.file is not None
    assert resolved.file.stem == "passport"
    catalogs = build_catalogs(index)
    assert "MONITORING_ENABLED" in catalogs.env["cluster-01/env-01"]


def test_missing_passport_is_table_only(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["env-params"]})
    repo.env_paramset("cluster-01", "env-01", "env-params", {"TENANT": "acme"})
    catalogs = build_catalogs(build_index(repo.root))
    assert catalogs.env["cluster-01/env-01"] == TABLE


def test_duplicate_explicit_match_does_not_resolve(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["env-params"]}, cloud_passport="dup")
    repo.passport("dup", {"cloud": {"CLOUD_API_HOST": "a"}}, cluster="cluster-01")
    repo.passport("dup", {"cloud": {"CLOUD_API_HOST": "b"}}, cluster="cluster-01", env="env-01")
    repo.env_paramset("cluster-01", "env-01", "env-params", {"TENANT": "acme"})
    index = build_index(repo.root)
    resolved = resolve_passport(index, index.environments[0])
    assert resolved.file is None
    assert resolved.note is not None
    assert {candidate.path for candidate in resolved.candidates} == {
        repo.root / "environments/cluster-01/cloud-passport/dup.yml",
        repo.root / "environments/cluster-01/env-01/Inventory/cloud-passport/dup.yml",
    }
    catalogs = build_catalogs(index)
    assert catalogs.env["cluster-01/env-01"] == TABLE


def test_catalogs_exclude_unselected_passport_files(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["env-params"]})
    repo.passport("passport", {"cloud": {"SELECTED_KEY": "selected"}}, cluster="cluster-01")
    repo.passport("extra", {"storage": {"STORAGE_SERVER_URL": "https://minio.example"}}, cluster="cluster-01")
    repo.env_paramset("cluster-01", "env-01", "env-params", {"TENANT": "acme"})
    catalogs = build_catalogs(build_index(repo.root))
    assert "SELECTED_KEY" in catalogs.cluster["cluster-01"]
    assert "SELECTED_KEY" in catalogs.repo
    assert "STORAGE_SERVER_URL" not in catalogs.cluster["cluster-01"]
    assert "STORAGE_SERVER_URL" not in catalogs.repo


def test_flattened_keys_skips_nested_dicts(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["env-params"]})
    repo.env_paramset("cluster-01", "env-01", "env-params", {"TENANT": "acme"})
    directory = repo.root / "environments" / "cluster-01" / "cloud-passport"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "passport.yml").write_text(
        "version: 1.5\n"
        "dbaas:\n"
        "  DBAAS_AGGREGATOR_ADDRESS: x\n"
        "  config:\n"
        "    retries: 3\n",
        encoding="utf-8",
    )
    index = build_index(repo.root)
    passport = next(item for item in index.passports if item.stem == "passport")
    keys = flattened_keys(passport)
    assert "DBAAS_AGGREGATOR_ADDRESS" in keys
    assert "config" not in keys
    catalogs = build_catalogs(index)
    assert "config" not in catalogs.cluster["cluster-01"]
    assert "config" not in catalogs.repo
