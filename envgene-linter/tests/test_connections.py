from envgene_linter.connections import Connections, compute_connections
from envgene_linter.discovery import build_index
from envgene_linter.engine import run_check
from envgene_linter.model import Category
from envgene_linter.rules.name1 import check as check_name1
from envgene_linter.rules.name2 import check as check_name2
from envgene_linter.rules.name4 import check as check_name4
from envgene_linter.rules.place4 import check as check_place4
from envgene_linter.rules.place8 import check as check_place8


def _append_template(repo, cluster: str, env: str, text: str) -> None:
    path = repo.root / "environments" / cluster / env / "Inventory/env_definition.yml"
    with path.open("a", encoding="utf-8") as stream:
        stream.write(text)


def _write_symlinked_inventory(repo, target, reference: str = "variables") -> None:
    target.mkdir(parents=True)
    (target / "env_definition.yml").write_text(
        "inventory:\n"
        "  environmentName: e\n"
        "envTemplate:\n"
        "  name: composite\n"
        f"  sharedTemplateVariables: [{reference}]\n",
        encoding="utf-8",
    )
    env = repo.root / "environments/c/e"
    env.mkdir(parents=True)
    (env / "Inventory").symlink_to(target, target_is_directory=True)


def test_connections_positional_artifact_definitions_remain_compatible(tmp_path):
    artifacts = frozenset({tmp_path / "artifact.yml"})

    connections = Connections(
        frozenset(),
        {},
        {},
        {},
        {},
        frozenset(),
        {},
        frozenset(),
        frozenset(),
        artifacts,
    )

    assert connections.artifact_definitions == artifacts
    assert connections.shared_template_variables == frozenset()


def test_shared_template_lookup_does_not_walk_external_symlink_ancestor(repo):
    outside = repo.root.parent / f"{repo.root.name}-outside-inventory"
    _write_symlinked_inventory(repo, outside)
    external = outside / "configuration/variables.yml"
    external.parent.mkdir()
    external.write_text("{}\n", encoding="utf-8")
    safe = repo.root / "environments/configuration/variables.yml"
    safe.parent.mkdir(parents=True)
    safe.write_text("{}\n", encoding="utf-8")

    connections = compute_connections(build_index(repo.root))

    assert connections.shared_template_variables == frozenset({safe.resolve()})


def test_shared_template_lookup_does_not_walk_git_symlink_ancestor(repo):
    git_inventory = repo.root / ".git/inventory"
    _write_symlinked_inventory(repo, git_inventory)
    hidden = git_inventory / "configuration/variables.yml"
    hidden.parent.mkdir()
    hidden.write_text("{}\n", encoding="utf-8")
    safe = repo.root / "environments/configuration/variables.yml"
    safe.parent.mkdir(parents=True)
    safe.write_text("{}\n", encoding="utf-8")

    connections = compute_connections(build_index(repo.root))

    assert connections.shared_template_variables == frozenset({safe.resolve()})


def test_parameter_connections_keep_physical_resolution_and_uses(repo):
    repo.env(
        "c",
        "e",
        deploy={"cloud": ["shared"]},
        technical={"bss": ["shared"]},
    )
    repo.site_paramset("shared", {"SITE": 1})
    repo.cluster_paramset("c", "shared", {"CLUSTER": 1})
    repo.env_paramset("c", "e", "shared", {"ENV": 1})

    index = build_index(repo.root)
    connections = compute_connections(index)
    site = (repo.root / "environments/parameters/shared.yml").resolve()
    cluster = (repo.root / "environments/c/parameters/shared.yml").resolve()
    environment = (
        repo.root / "environments/c/e/Inventory/parameters/shared.yml"
    ).resolve()

    assert connections.parameter_sets == frozenset({cluster, environment})
    assert connections.environment_parameter_sets["c/e"] == frozenset(
        {cluster, environment}
    )
    assert site not in connections.parameter_uses
    assert {
        (use.environment, use.category, use.target, use.reference)
        for use in connections.parameter_uses[cluster]
    } == {
        ("c/e", Category.DEPLOY, "cloud", "shared"),
        ("c/e", Category.TECHNICAL, "bss", "shared"),
    }


def test_connections_select_only_resolved_passport_profile_and_credentials(repo):
    repo.env("c", "e", cloud_passport="selected")
    repo.passport("selected", {"cloud": {"SELECTED": 1}}, cluster="c", env="e")
    repo.passport("unused", {"cloud": {"UNUSED": 1}})
    _append_template(
        repo,
        "c",
        "e",
        "  envSpecificResourceProfiles:\n"
        "    cloud: selected-profile\n"
        "  sharedMasterCredentialFiles:\n"
        "    - selected-creds\n",
    )
    profile = repo.root / "environments/resource_profiles/selected-profile.yml"
    profile.parent.mkdir(parents=True)
    profile.write_text("{}\n", encoding="utf-8")
    credentials = repo.root / "environments/credentials/selected-creds.yml"
    credentials.parent.mkdir(parents=True)
    credentials.write_text("{}\n", encoding="utf-8")

    index = build_index(repo.root)
    connections = compute_connections(index)

    assert connections.passports == frozenset(
        {repo.root / "environments/c/e/Inventory/cloud-passport/selected.yml"}
    )
    assert connections.resource_profiles == frozenset({profile.resolve()})
    assert connections.credentials == frozenset({credentials.resolve()})
    assert connections.environment_passports["c/e"].path.name == "selected.yml"
    assert connections.environment_paths["c/e"] == frozenset(
        {
            repo.root / "environments/c/e/Inventory/cloud-passport/selected.yml",
            profile.resolve(),
            credentials.resolve(),
        }
    )


def test_artifact_selector_uses_first_two_parts_and_yml_priority(repo):
    repo.env("c", "e")
    _append_template(
        repo,
        "c",
        "e",
        "  artifact: common:1.2:ignored\n"
        "  bgNsArtifacts:\n"
        "    origin: origin:2\n"
        "    peer: peer:3\n",
    )
    directory = repo.root / "configuration/artifact_definitions"
    directory.mkdir(parents=True)
    common_yml = directory / "common.yml"
    common_yml.write_text("not: [valid\n", encoding="utf-8")
    (directory / "common.yaml").write_text("name: common\n", encoding="utf-8")
    (directory / "origin.yaml").write_text("name: origin\n", encoding="utf-8")
    (directory / "peer.yml").write_text("name: peer\n", encoding="utf-8")

    index = build_index(repo.root)
    connections = compute_connections(index)

    assert index.environments[0].artifact_selectors == (
        "common:1.2:ignored",
        "origin:2",
        "peer:3",
    )
    assert connections.artifact_definitions == frozenset(
        {
            common_yml.resolve(),
            (directory / "origin.yaml").resolve(),
            (directory / "peer.yml").resolve(),
        }
    )


def test_malformed_and_jinja_artifact_selectors_are_not_connections(repo):
    repo.env("c", "e")
    _append_template(
        repo,
        "c",
        "e",
        "  artifact: missing-version\n"
        "  bgNsArtifacts:\n"
        "    origin: ':2'\n"
        "    peer: '{{ artifact }}:3'\n",
    )
    directory = repo.root / "configuration/artifact_definitions"
    directory.mkdir(parents=True)
    for name in ("missing-version", "artifact"):
        (directory / f"{name}.yml").write_text(f"name: {name}\n", encoding="utf-8")

    connections = compute_connections(build_index(repo.root))

    assert connections.artifact_definitions == frozenset()


def test_legacy_template_artifact_and_non_string_selector_are_not_connections(repo):
    repo.env("c", "e")
    path = repo.root / "environments/c/e/Inventory/env_definition.yml"
    path.write_text(
        "inventory:\n"
        "  environmentName: e\n"
        "envTemplate:\n"
        "  artifact: 42\n"
        "  templateArtifact:\n"
        "    artifact:\n"
        "      artifact_id: legacy\n",
        encoding="utf-8",
    )
    directory = repo.root / "configuration/artifact_definitions"
    directory.mkdir(parents=True)
    (directory / "legacy.yml").write_text("name: wrong\n", encoding="utf-8")

    index = build_index(repo.root)

    assert index.environments[0].artifact_selectors == ()
    assert compute_connections(index).artifact_definitions == frozenset()


def test_direct_rule_and_engine_share_selected_parameter_files(repo):
    repo.env("c", "e", deploy={"cloud": ["used"]})
    used = repo.root / "environments/c/e/Inventory/parameters/used.yml"
    used.parent.mkdir(parents=True)
    used.write_text("name: wrong\nparameters: {}\n", encoding="utf-8")
    unused = repo.root / "environments/parameters/unused.yml"
    unused.parent.mkdir(parents=True)
    unused.write_text("name: also-wrong\nparameters: {}\n", encoding="utf-8")

    direct = check_name2(build_index(repo.root))
    engine = [finding for finding in run_check(repo.root).findings if finding.rule == "NAME-2"]

    assert [(item.path, item.key) for item in direct] == [(used, "name")]
    assert [(item.path, item.key) for item in engine] == [(used, "name")]


def test_unbound_regular_alias_cannot_replace_selected_parameter_record(repo):
    repo.env("c", "e", deploy={"cloud": ["service-deploy"]})
    target = repo.root / "environments/c/e/Inventory/parameters/service-deploy.yml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "name: service-deploy\nparameters:\n  CLOUD_API_HOST: api.example\n",
        encoding="utf-8",
    )
    alias = target.with_name("aaa.yml")
    alias.symlink_to(target.name)

    index = build_index(repo.root)
    connections = compute_connections(index)

    assert connections.parameter_files[target.resolve()].path == target
    assert check_name2(index, connections) == []
    assert check_name4(index, connections) == []
    assert [(item.path, item.key) for item in check_place4(index, connections)] == [
        (target, "CLOUD_API_HOST")
    ]

    engine = run_check(repo.root).findings
    assert [item for item in engine if item.rule in {"NAME-2", "NAME-4"}] == []
    assert [
        (item.path, item.key) for item in engine if item.rule == "PLACE-4"
    ] == [(target, "CLOUD_API_HOST")]


def test_unbound_jinja_alias_cannot_suppress_selected_parameter_records(repo):
    repo.env(
        "c",
        "e",
        deploy={"cloud": ["service-deploy", "empty-deploy"]},
    )
    directory = repo.root / "environments/c/e/Inventory/parameters"
    directory.mkdir(parents=True)
    service = directory / "service-deploy.yml"
    service.write_text(
        "name: service-deploy\n"
        "parameters:\n"
        "  KAFKA_URL: kafka.internal:9092\n"
        "  BOOTSTRAP_SERVERS: kafka.internal:9092\n",
        encoding="utf-8",
    )
    empty = directory / "empty-deploy.yml"
    empty.write_text("name: empty-deploy\nparameters: {}\n", encoding="utf-8")
    (directory / "aaa.yml.j2").symlink_to(service.name)
    (directory / "aab.yml.j2").symlink_to(empty.name)

    index = build_index(repo.root)
    connections = compute_connections(index)
    direct_name1 = check_name1(index, connections)
    direct_place8 = check_place8(index, connections)

    assert len(direct_name1) == 1
    assert {location.path for location in direct_name1[0].locations} == {service}
    assert [(item.path, item.key) for item in direct_place8] == [(empty, "empty-deploy")]

    engine = run_check(repo.root).findings
    engine_name1 = [item for item in engine if item.rule == "NAME-1"]
    engine_place8 = [item for item in engine if item.rule == "PLACE-8"]
    assert len(engine_name1) == 1
    assert {location.path for location in engine_name1[0].locations} == {service}
    assert [(item.path, item.key) for item in engine_place8] == [(empty, "empty-deploy")]
