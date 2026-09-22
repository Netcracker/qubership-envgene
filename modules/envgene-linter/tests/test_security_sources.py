from __future__ import annotations

from pathlib import Path

from ruamel.yaml import YAML

from envgene_linter.connections import compute_connections
from envgene_linter.discovery import build_index
from envgene_linter.security_sources import (
    SecurityBag,
    SecurityIssue,
    SecuritySource,
    collect_security_sources,
)


def write(path: Path, doc: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        YAML().dump(doc, stream)
    return path


def collect(repo):
    index = build_index(repo.root)
    connections = compute_connections(index)
    return collect_security_sources(index, connections), connections


def set_inventory_deployer(repo, name: str) -> Path:
    path = repo.root / "environments/c/e/Inventory/env_definition.yml"
    yaml = YAML()
    doc = yaml.load(path.read_text(encoding="utf-8"))
    doc["inventory"]["deployer"] = name
    with path.open("w", encoding="utf-8") as stream:
        yaml.dump(doc, stream)
    return path


def test_collects_fixed_generated_and_connected_parameter_sources_without_mutating_connections(repo):
    repo.env("c", "e", deploy={"cloud": ["params"]})
    parameter_set = repo.root / "environments/c/e/Inventory/parameters/params.yml"
    write(
        parameter_set,
        {
            "parameters": {"PASSWORD": "synthetic"},
            "applications": [{"name": "app", "parameters": {"TOKEN": "synthetic"}}],
        },
    )
    fixed = write(
        repo.root / "environments/c/e/Inventory/credentials/inventory_generation_creds.yml",
        {},
    )
    generated = write(repo.root / "environments/c/e/Credentials/credentials.yml", {})

    inputs, connections = collect(repo)

    assert set(inputs.sources) == {
        SecuritySource(fixed.resolve(), "shared", "c/e"),
        SecuritySource(generated.resolve(), "generated", "c/e"),
    }
    assert {
        (bag.path, bag.prefix, bag.catalog, bag.fields)
        for bag in inputs.bags
        if bag.path == parameter_set.resolve()
    } == {
        (parameter_set.resolve(), ("parameters",), generated.resolve(), None),
        (
            parameter_set.resolve(),
            ("applications", 0, "parameters"),
            generated.resolve(),
            None,
        ),
    }
    assert connections.credentials == frozenset({fixed.resolve()})


def test_passport_companion_uses_first_candidate_and_passport_bag_uses_that_catalog(repo):
    repo.env("c", "e", cloud_passport="selected")
    repo.passport("selected", {"api": {"TOKEN": "synthetic"}}, cluster="c", env="e")
    passport = repo.root / "environments/c/e/Inventory/cloud-passport/selected.yml"
    first = write(passport.parent / "credentials/selected.yml", {})
    write(passport.parent / "selected-creds.yml", {})

    inputs, _ = collect(repo)

    assert SecuritySource(first.resolve(), "passport", "c/e") in inputs.sources
    assert SecurityBag(passport.resolve(), (), "c/e", first.resolve()) in inputs.bags
    assert not any(source.path.name == "selected-creds.yml" for source in inputs.sources)


def test_unsafe_first_passport_companion_does_not_fall_back(repo, tmp_path):
    repo.env("c", "e", cloud_passport="selected")
    repo.passport("selected", {"api": {"TOKEN": "synthetic"}}, cluster="c", env="e")
    passport = repo.root / "environments/c/e/Inventory/cloud-passport/selected.yml"
    outside = write(tmp_path.parent / f"{tmp_path.name}-outside.yml", {})
    first = passport.parent / "credentials/selected.yml"
    first.parent.mkdir(parents=True)
    first.symlink_to(outside)
    fallback = write(passport.parent / "selected-creds.yml", {})

    try:
        inputs, _ = collect(repo)
    finally:
        outside.unlink(missing_ok=True)

    assert not any(source.path == fallback.resolve() for source in inputs.sources)
    assert SecurityBag(passport.resolve(), (), "c/e", None) in inputs.bags
    assert SecurityIssue(passport.resolve()) in inputs.issues


def test_safe_passport_symlink_uses_logical_companion_location(repo):
    repo.env("c", "e", cloud_passport="selected")
    target = write(repo.root / "fixtures/passport.yml", {"api": {"TOKEN": "synthetic"}})
    passport = repo.root / "environments/c/e/Inventory/cloud-passport/selected.yml"
    passport.parent.mkdir(parents=True)
    passport.symlink_to(target)
    companion = write(passport.parent / "credentials/selected.yml", {})

    inputs, _ = collect(repo)

    assert SecuritySource(companion.resolve(), "passport", "c/e") in inputs.sources
    assert SecurityBag(target.resolve(), (), "c/e", companion.resolve()) in inputs.bags


def test_deployer_binding_uses_cluster_priority_selected_entry_and_companion(repo):
    repo.env("c", "e")
    definition = set_inventory_deployer(repo, "chosen")
    cluster_deployer = write(
        repo.root / "environments/c/app-deployer/deployer.yml",
        {"chosen": {"username": "inline", "token": "inline", "deployerUrl": "example"}},
    )
    write(
        repo.root / "environments/c/e/app-deployer/deployer.yml",
        {"chosen": {"username": "shadowed", "token": "shadowed"}},
    )
    companion = write(cluster_deployer.parent / "deployer-creds.yml", {})

    inputs, _ = collect(repo)

    assert SecurityBag(
        cluster_deployer.resolve(),
        ("chosen",),
        "c/e",
        companion.resolve(),
        ("username", "token"),
    ) in inputs.bags
    assert not any(
        bag.path.parent == repo.root / "environments/c/e/app-deployer"
        for bag in inputs.bags
    )
    assert SecurityIssue(definition.resolve(), ("inventory", "deployer")) not in inputs.issues


def test_deployer_missing_selected_entry_falls_back_to_root_definition(repo):
    repo.env("c", "e")
    set_inventory_deployer(repo, "chosen")
    write(
        repo.root / "environments/c/app-deployer/deployer.yml",
        {"other": {"username": "unused", "token": "unused"}},
    )
    root_deployer = write(
        repo.root / "configuration/deployer.yml",
        {"chosen": {"username": "inline", "token": "inline", "deployerUrl": "example"}},
    )
    root_catalog = write(repo.root / "configuration/credentials/credentials.yml", {})

    inputs, _ = collect(repo)

    assert SecurityBag(
        root_deployer.resolve(),
        ("chosen",),
        "c/e",
        root_catalog.resolve(),
        ("username", "token"),
    ) in inputs.bags


def test_deployer_symlink_uses_logical_companion_location(repo):
    repo.env("c", "e")
    set_inventory_deployer(repo, "chosen")
    target = write(
        repo.root / "fixtures/deployer.yml",
        {"chosen": {"username": "inline", "token": "inline", "deployerUrl": "example"}},
    )
    logical = repo.root / "environments/c/app-deployer/deployer.yml"
    logical.parent.mkdir(parents=True)
    logical.symlink_to(target)
    logical_companion = write(logical.parent / "deployer-creds.yml", {})
    write(target.parent / "deployer-creds.yml", {"shadowed": {"type": "secret"}})

    inputs, _ = collect(repo)

    assert SecurityBag(
        target.resolve(),
        ("chosen",),
        "c/e",
        logical_companion.resolve(),
        ("username", "token"),
    ) in inputs.bags


def test_missing_deployer_binding_target_records_only_consumer_location(repo):
    repo.env("c", "e")
    definition = set_inventory_deployer(repo, "absent")

    inputs, _ = collect(repo)

    assert SecurityIssue(definition.resolve(), ("inventory", "deployer")) in inputs.issues
    assert not any(bag.fields == ("username", "token") for bag in inputs.bags)


def test_system_integration_scans_explicit_fields_but_not_inactive_discovery(repo):
    repo.env("c", "e")
    integration = write(
        repo.root / "configuration/integration.yml",
        {
            "self_token": "explicit",
            "cp_discovery": {"gitlab": {"token": "configured-but-inactive"}},
        },
    )
    root_catalog = write(repo.root / "configuration/credentials/credentials.yml", {})

    inputs, _ = collect(repo)

    assert SecurityBag(
        integration.resolve(), (), "system", root_catalog.resolve(), ("self_token",)
    ) in inputs.bags
    assert not any(bag.prefix == ("cp_discovery", "gitlab") for bag in inputs.bags)


def test_system_integration_missing_self_token_uses_ci_fallback_without_issue(repo):
    repo.env("c", "e")
    integration = write(
        repo.root / "configuration/integration.yml",
        {"cp_discovery": {"gitlab": {"project": "synthetic/project", "token": "explicit"}}},
    )

    inputs, _ = collect(repo)

    assert SecurityBag(
        integration.resolve(),
        ("cp_discovery", "gitlab"),
        "system",
        None,
        ("token",),
    ) in inputs.bags
    assert not any(issue.path == integration.resolve() for issue in inputs.issues)


def test_inactive_system_config_does_not_inspect_root_credentials_catalog(repo):
    repo.env("c", "e")
    write(repo.root / "configuration/integration.yml", {"cp_discovery": {}})
    root_catalog = repo.root / "configuration/credentials/credentials.yml"
    root_catalog.parent.mkdir(parents=True)
    root_catalog.write_text("broken: [\n", encoding="utf-8")

    inputs, _ = collect(repo)

    assert inputs.issues == []
    assert not any(source.path == root_catalog.resolve() for source in inputs.sources)


def test_registry_bag_is_selected_only_for_active_legacy_artifact_consumer(repo):
    repo.env("c", "e")
    definition = repo.root / "environments/c/e/Inventory/env_definition.yml"
    definition.write_text(
        "inventory:\n"
        "  environmentName: e\n"
        "envTemplate:\n"
        "  name: composite\n"
        "  templateArtifact:\n"
        "    registry: active\n"
        "    templateRepository: releaseRepository\n"
        "    artifact:\n"
        "      group_id: g\n"
        "      artifact_id: a\n"
        "      version: 1\n",
        encoding="utf-8",
    )
    registry = write(
        repo.root / "configuration/registry.yml",
        {
            "active": {"username": "inline", "password": "inline"},
            "unused": {"username": "unused", "password": "unused"},
        },
    )
    root_catalog = write(repo.root / "configuration/credentials/credentials.yml", {})

    inputs, _ = collect(repo)

    assert SecurityBag(
        registry.resolve(),
        ("active",),
        "c/e",
        root_catalog.resolve(),
        ("username", "password"),
    ) in inputs.bags
    assert not any(bag.prefix == ("unused",) for bag in inputs.bags)


def test_selected_modern_artifact_registry_uses_environment_catalog(repo):
    repo.env("c", "e", artifact="template:1")
    artifact = write(
        repo.root / "configuration/artifact_definitions/template.yml",
        {
            "name": "template",
            "registry": {"credentialsId": "synthetic-reference"},
        },
    )
    generated = write(repo.root / "environments/c/e/Credentials/credentials.yml", {})

    inputs, _ = collect(repo)

    assert SecurityBag(
        artifact.resolve(),
        ("registry",),
        "c/e",
        generated.resolve(),
        ("credentialsId",),
    ) in inputs.bags


def test_cloud_and_namespace_parameter_bags_use_generated_catalog(repo):
    repo.env("c", "e", deploy={"app": ["params"]})
    repo.site_paramset("params", {})
    generated = write(repo.root / "environments/c/e/Credentials/credentials.yml", {})
    cloud = write(
        repo.root / "environments/c/e/cloud.yml",
        {"deployParameters": {"PASSWORD": "synthetic"}},
    )
    namespace = write(
        repo.root / "environments/c/e/Namespaces/app/namespace.yml",
        {"technicalConfigurationParameters": {"TOKEN": "synthetic"}},
    )

    inputs, _ = collect(repo)

    assert SecurityBag(
        cloud.resolve(), ("deployParameters",), "c/e", generated.resolve()
    ) in inputs.bags
    assert SecurityBag(
        namespace.resolve(),
        ("technicalConfigurationParameters",),
        "c/e",
        generated.resolve(),
    ) in inputs.bags


def test_nonempty_unsupported_parameter_sections_record_file_issues(repo):
    repo.env("c", "e", deploy={"cloud": ["params"]})
    parameter_set = write(
        repo.root / "environments/c/e/Inventory/parameters/params.yml",
        {"parameters": ["unsupported"], "applications": {"unsupported": True}},
    )
    cloud = write(
        repo.root / "environments/c/e/cloud.yml",
        {"deployParameters": ["unsupported"]},
    )

    inputs, _ = collect(repo)

    assert SecurityIssue(parameter_set.resolve()) in inputs.issues
    assert SecurityIssue(cloud.resolve()) in inputs.issues


def test_nonempty_unsupported_application_entries_record_file_issue(repo):
    repo.env("c", "e", deploy={"cloud": ["params"]})
    parameter_set = write(
        repo.root / "environments/c/e/Inventory/parameters/params.yml",
        {
            "parameters": {},
            "applications": [
                {"name": "bad-params", "parameters": ["unsupported"]},
                "unsupported-entry",
            ],
        },
    )

    inputs, _ = collect(repo)

    assert SecurityIssue(parameter_set.resolve()) in inputs.issues
