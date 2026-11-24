import json
from pathlib import Path

import pytest

from envgene_linter.discovery import DiscoveryError, build_index, paramset_stem
from envgene_linter.engine import run_check
from envgene_linter.model import Category, EnvModel, Layer, RepoIndex


def test_missing_environments_is_not_an_instance_repo(tmp_path: Path):
    with pytest.raises(DiscoveryError, match="environments"):
        build_index(tmp_path)


def test_indexes_layers_and_bindings(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["env-params"]})
    repo.site_paramset("shared", {"SITE": 1})
    repo.cluster_paramset("cluster-01", "shared", {"CLUSTER": 1})
    repo.env_paramset("cluster-01", "env-01", "env-params", {"ENV": 1})

    index = build_index(repo.root)
    assert [item.stem for item in index.site_paramsets] == ["shared"]
    assert index.site_paramsets[0].layer is Layer.REPOSITORY
    cluster = index.clusters["cluster-01"]
    assert [item.stem for item in cluster.paramsets] == ["shared"]
    env = cluster.environments[0]
    assert env.full_name == "cluster-01/env-01"
    assert env.bound_targets(Category.DEPLOY) == {"cloud": ["env-params"]}
    assert env.paramsets[0].layer is Layer.ENVIRONMENT
    assert env.paramsets[0].parameters["ENV"] == 1


def test_parameters_dir_is_not_a_cluster(repo):
    repo.site_paramset("shared", {"A": 1})
    index = build_index(repo.root)
    assert "parameters" not in index.clusters


def test_paramset_stem_strips_yaml_and_j2():
    assert paramset_stem(Path("foo.yml.j2")) == "foo"
    assert paramset_stem(Path("foo.yaml")) == "foo"


def test_jinja_paramset_is_skipped_not_loaded(repo):
    repo.env("c", "e")
    path = repo.root / "environments" / "c" / "e" / "Inventory" / "parameters"
    path.mkdir(parents=True, exist_ok=True)
    (path / "x.yml.j2").write_text("{{ foo }}\n", encoding="utf-8")
    index = build_index(repo.root)
    env = index.clusters["c"].environments[0]
    assert env.paramsets[0].is_jinja is True
    assert env.paramsets[0].loaded is None
    assert index.skipped


def test_non_utf8_paramset_is_skipped_not_crash(repo):
    repo.env("c", "e", deploy={"cloud": ["ok"]})
    repo.env_paramset("c", "e", "ok", {"A": 1})
    bad = repo.root / "environments" / "parameters" / "bad.yml"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_bytes(b"\xff\xfe not utf-8")
    index = build_index(repo.root)
    assert any("bad.yml" in note for note in index.skipped)
    result = run_check(repo.root)
    assert any("bad.yml" in note for note in result.skipped)


def test_indexes_named_entities(repo):
    repo.env("cluster-01", "env-01")
    path = repo.root / "configuration/artifact_definitions/test.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("name: test\n", encoding="utf-8")
    index = build_index(repo.root)
    assert len(index.named_entities) == 1
    entity = index.named_entities[0]
    assert entity.stem == "test"
    assert entity.kind == "Artifact definition"
    assert entity.loaded is not None


def test_place8_model_fields_are_backward_compatible_defaults(tmp_path):
    env = EnvModel(cluster="c", name="e", path=tmp_path)
    index = RepoIndex(root=tmp_path)
    assert env.resource_profile_bindings == {}
    assert env.shared_credential_bindings == []
    assert env.shared_template_variable_bindings == []
    assert index.resource_profiles == []
    assert index.credential_files == []


def test_env_model_positional_artifact_selectors_remain_compatible(tmp_path):
    selectors = ("application:1.0",)

    env = EnvModel("c", "e", tmp_path, [], {}, None, {}, [], selectors)

    assert env.artifact_selectors == selectors
    assert env.shared_template_variable_bindings == []


def test_place8_entities_are_separate_from_name2_entities(repo):
    repo.env("c", "e")
    profile = repo.root / "environments/resource_profiles/nested/p.yml"
    credential = repo.root / "environments/credentials/nested/c.yml"
    profile.parent.mkdir(parents=True)
    credential.parent.mkdir(parents=True)
    profile.write_text("{}\n", encoding="utf-8")
    credential.write_text("{}\n", encoding="utf-8")
    index = build_index(repo.root)
    assert [item.path for item in index.resource_profiles if item.path == profile] == [profile]
    assert [item.path for item in index.credential_files] == [credential]
    assert not {profile, credential} & {item.path for item in index.named_entities}


def _definition_template(repo, template):
    repo.env("cluster-01", "env-01")
    path = repo.root / "environments/cluster-01/env-01/Inventory/env_definition.yml"
    path.write_text(json.dumps({"envTemplate": template}), encoding="utf-8")
    return build_index(repo.root).environments[0]


def test_template_identity_preserves_name_and_complete_artifact(repo):
    env = _definition_template(repo, {
        "name": "business", "artifact": "example-env-templates:1.0.0"
    })
    assert getattr(env, "template_identity", None) == ("business", "example-env-templates:1.0.0")


@pytest.mark.parametrize("template", [
    {},
    {"name": "business"},
    {"artifact": "example-env-templates:1.0.0"},
    {"name": None, "artifact": "example-env-templates:1.0.0"},
    {"name": "business", "artifact": None},
    {"name": " ", "artifact": "example-env-templates:1.0.0"},
    {"name": "business", "artifact": ""},
    {"name": 1, "artifact": "example-env-templates:1.0.0"},
    {"name": "business", "artifact": ["example-env-templates:1.0.0"]},
    {"name": "{{ selected }}", "artifact": "example-env-templates:1.0.0"},
    {"name": "business", "artifact": "example-env-templates:{{ version }}"},
    {"name": "{% if enabled %}business{% endif %}", "artifact": "example-env-templates:1.0.0"},
    {"name": "business", "artifact": "${templates.artifact}"},
    {"name": "${templates.name}", "artifact": "example-env-templates:1.0.0"},
    {"name": "business", "bgNsArtifacts": {"origin": "other:1", "peer": "other:2"}},
])
def test_template_identity_rejects_incomplete_or_dynamic_values(repo, template):
    assert getattr(_definition_template(repo, template), "template_identity", None) is None



pytestmark = pytest.mark.usefixtures("all_rules_enabled")


@pytest.mark.parametrize("body", [
    "!custom\nenvTemplate:\n  name: business\n  artifact: example-env-templates:1.0.0\n",
    "envTemplate: !custom\n  name: business\n  artifact: example-env-templates:1.0.0\n",
])
def test_tagged_definition_identity_is_unknown(repo, body):
    repo.env("cluster-01", "env-01")
    path = repo.root / "environments/cluster-01/env-01/Inventory/env_definition.yml"
    path.write_text(body)
    assert build_index(repo.root).environments[0].template_identity is None
