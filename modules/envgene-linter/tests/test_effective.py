from envgene_linter.discovery import build_index
from envgene_linter.effective import (
    ALL_LAYERS,
    LOWER_LAYERS,
    SITE_LAYERS,
    compute,
    dict_merge,
    resolve_reference,
)
from envgene_linter.model import Category, Layer, Scope


def test_dict_merge_nested_and_none():
    assert dict_merge({"a": {"x": 1, "y": 2}}, {"a": {"y": 3, "z": 4}}) == {"a": {"x": 1, "y": 3, "z": 4}}
    assert dict_merge({"a": 1}, None) == {"a": 1}
    assert dict_merge(1, [2]) == [2]


def test_same_filename_cluster_replaces_site(repo):
    repo.env("c", "e", deploy={"cloud": ["shared"]})
    repo.site_paramset("shared", {"KEEP": "site", "WIN": "site"})
    repo.cluster_paramset("c", "shared", {"WIN": "cluster"})
    index = build_index(repo.root)
    env = index.environments[0]
    entries = resolve_reference(index, env, "shared", ALL_LAYERS)
    assert [entry.file.layer for entry in entries] == [Layer.CLUSTER]
    full = compute(index, env, ALL_LAYERS)
    scope = Scope("cloud", Category.DEPLOY)
    assert full.get(scope, ("KEEP",)) is None
    assert full.get(scope, ("WIN",)).value == "cluster"
    assert full.get(scope, ("WIN",)).provenance.layer is Layer.CLUSTER


def test_env_file_survives_same_name(repo):
    repo.env("c", "e", deploy={"cloud": ["shared"]})
    repo.cluster_paramset("c", "shared", {"A": 1, "B": 1})
    repo.env_paramset("c", "e", "shared", {"B": 2})
    index = build_index(repo.root)
    env = index.environments[0]
    entries = resolve_reference(index, env, "shared", ALL_LAYERS)
    assert [entry.file.layer for entry in entries] == [Layer.CLUSTER, Layer.ENVIRONMENT]
    full = compute(index, env, ALL_LAYERS)
    scope = Scope("cloud", Category.DEPLOY)
    assert full.get(scope, ("A",)).value == 1
    assert full.get(scope, ("B",)).value == 2
    assert full.get(scope, ("B",)).provenance.layer is Layer.ENVIRONMENT


def test_yml_and_yaml_both_apply(repo):
    repo.env("c", "e", deploy={"cloud": ["shared"]})
    site = repo.root / "environments" / "parameters"
    site.mkdir(parents=True)
    (site / "shared.yml").write_text("parameters:\n  FROM_YML: 1\n", encoding="utf-8")
    (site / "shared.yaml").write_text("parameters:\n  FROM_YAML: 2\n", encoding="utf-8")
    index = build_index(repo.root)
    full = compute(index, index.environments[0], ALL_LAYERS)
    scope = Scope("cloud", Category.DEPLOY)
    assert full.get(scope, ("FROM_YML",)).value == 1
    assert full.get(scope, ("FROM_YAML",)).value == 2


def test_projections_drop_higher_layers(repo):
    repo.env("c", "e", deploy={"cloud": ["shared", "other", "env-only"]})
    repo.site_paramset("shared", {"S": 1})
    repo.cluster_paramset("c", "other", {"C": 1})
    repo.env_paramset("c", "e", "env-only", {"E": 1})
    index = build_index(repo.root)
    env = index.environments[0]
    scope = Scope("cloud", Category.DEPLOY)
    assert compute(index, env, SITE_LAYERS).get(scope, ("S",)).value == 1
    assert compute(index, env, SITE_LAYERS).get(scope, ("C",)) is None
    assert compute(index, env, LOWER_LAYERS).get(scope, ("C",)).value == 1
    assert compute(index, env, LOWER_LAYERS).get(scope, ("E",)) is None
    assert compute(index, env, ALL_LAYERS).get(scope, ("E",)).value == 1


def test_projections_do_not_resurrect_shadowed_site_file(repo):
    repo.env("c", "e", deploy={"cloud": ["cloud"]})
    repo.site_paramset("cloud", {"COMMON_FROM_SITE": "shared"})
    repo.cluster_paramset("c", "cloud", {"COMMON_FROM_SITE": "shared", "CLUSTER_ONLY": "x"})
    index = build_index(repo.root)
    env = index.environments[0]
    scope = Scope("cloud", Category.DEPLOY)
    assert [entry.file.layer for entry in resolve_reference(index, env, "cloud", SITE_LAYERS)] == [
        Layer.REPOSITORY
    ]
    site = compute(index, env, SITE_LAYERS)
    assert site.get(scope, ("COMMON_FROM_SITE",)) is None
    assert site.get(scope, ("CLUSTER_ONLY",)) is None
    lower = compute(index, env, LOWER_LAYERS)
    assert [entry.file.layer for entry in resolve_reference(index, env, "cloud", LOWER_LAYERS)] == [
        Layer.CLUSTER
    ]
    assert lower.get(scope, ("COMMON_FROM_SITE",)).provenance.layer is Layer.CLUSTER
    assert lower.get(scope, ("CLUSTER_ONLY",)).value == "x"
    assert compute(index, env, ALL_LAYERS).get(scope, ("COMMON_FROM_SITE",)).provenance.layer is Layer.CLUSTER


def test_null_override_keeps_prior_scalar_and_provenance(repo):
    repo.env("c", "e", deploy={"cloud": ["shared"]})
    repo.cluster_paramset("c", "shared", {"FOO": 5})
    env_dir = repo.root / "environments" / "c" / "e" / "Inventory" / "parameters"
    env_dir.mkdir(parents=True, exist_ok=True)
    (env_dir / "shared.yml").write_text("name: shared\nparameters:\n  FOO:\n", encoding="utf-8")
    index = build_index(repo.root)
    full = compute(index, index.environments[0], ALL_LAYERS)
    scope = Scope("cloud", Category.DEPLOY)
    leaf = full.get(scope, ("FOO",))
    assert leaf.value == 5
    assert leaf.provenance.layer is Layer.CLUSTER


def test_unbound_paramset_is_not_in_any_scope(repo):
    repo.env("c", "e", deploy={"cloud": ["used"]})
    repo.env_paramset("c", "e", "used", {"A": 1})
    repo.env_paramset("c", "e", "orphan", {"B": 1})
    full = compute(build_index(repo.root), build_index(repo.root).environments[0], ALL_LAYERS)
    scope = Scope("cloud", Category.DEPLOY)
    assert full.get(scope, ("A",)).value == 1
    assert full.get(scope, ("B",)) is None
