from __future__ import annotations

from pathlib import Path

import pytest

from envgene_linter.connections import compute_connections
from envgene_linter.discovery import build_index
from envgene_linter.html_report import render_html
from envgene_linter.model import Action
from envgene_linter.report import render
from envgene_linter.rules.int2 import check as check_int2
from envgene_linter.rules.int4 import check
from envgene_linter.rules.sec5 import check as check_sec5
from envgene_linter.security_sources import SecurityBag, collect_security_sources
from envgene_linter.usage_candidates import collect_candidates
from envgene_linter.usage_references import analyze_usage
from test_security_sources import write
from test_usage_references import bind, shared


def registry(repo, value: dict) -> Path:
    repo.env("c", "e", artifact="template:1")
    return write(
        repo.root / "configuration/artifact_definitions/template.yml",
        {"name": "template", "registry": value},
    )


def catalog(repo, *identifiers: str) -> Path:
    return write(
        repo.root / "configuration/credentials/credentials.yml",
        {
            identifier: {"type": "secret", "data": {"secret": "private-payload"}}
            for identifier in identifiers
        },
    )


def analyze(repo):
    index = build_index(repo.root)
    connections = compute_connections(index)
    return analyze_usage(index, connections, collect_candidates(index, connections))


def collect(repo):
    index = build_index(repo.root)
    return collect_security_sources(index, compute_connections(index))


@pytest.mark.parametrize("version", [None, "1.0", "3.0"])
def test_v1_registry_protects_root_entry_and_reviews_same_named_environment_entry(repo, version):
    config = {"credentialsId": "private-used-id"}
    if version is not None:
        config["version"] = version
    registry(repo, config)
    root = catalog(repo, "private-used-id", "private-unused-id")
    bind(repo, sharedMasterCredentialFiles=["shared"])
    environment = shared(repo, ids=("private-used-id",))
    write(
        repo.root / "environments/c/e/Credentials/credentials.yml",
        {"private-used-id": {"type": "secret"}},
    )

    usages = analyze(repo)
    findings = check(build_index(repo.root))

    assert [(item.candidate.path, item.candidate.name) for item in usages if item.references] == [
        (root, "private-used-id")
    ]
    assert [(item.path, item.line) for item in findings] == [(root, 5), (environment, 1)]
    assert all(item.action is Action.REVIEW for item in findings)
    for output in (repr(findings), render(findings), render_html(findings, repo.root)):
        assert "private-used-id" not in output
        assert "private-unused-id" not in output
        assert "private-payload" not in output


@pytest.mark.parametrize("identifier", [None, ""])
def test_empty_v1_credential_id_does_not_create_a_secret_protection_issue(repo, identifier):
    registry(repo, {"credentialsId": identifier})

    inputs = collect(repo)
    index = build_index(repo.root)

    assert inputs.issues == []
    assert check_int2(index) == []
    assert check_sec5(index) == []


@pytest.mark.parametrize("version", [None, "2.0"])
def test_v2_registry_protects_only_the_selected_maven_auth_credential(repo, version):
    config = {
        "credentialsId": "private-inactive-id",
        "mavenConfig": {"authConfig": "chosen"},
        "dockerConfig": {"authConfig": "inactive"},
        "authConfig": {
            "chosen": {"provider": "nexus", "authMethod": "user_pass", "credentialsId": "private-used-id"},
            "inactive": {"provider": "nexus", "authMethod": "user_pass", "credentialsId": "private-inactive-id"},
        },
    }
    if version is not None:
        config["version"] = version
    artifact = registry(repo, config)
    root = catalog(repo, "private-used-id", "private-inactive-id")

    inputs = collect(repo)
    usages = analyze(repo)

    assert SecurityBag(
        artifact, ("registry", "authConfig", "chosen"), "c/e", root, ("credentialsId",)
    ) in inputs.bags
    assert [(item.candidate.path, item.candidate.name) for item in usages if item.references] == [
        (root, "private-used-id")
    ]
    assert [(item.path, item.line) for item in check(build_index(repo.root))] == [(root, 5)]


def test_v2_anonymous_auth_does_not_consume_its_credential_or_inactive_configs(repo):
    artifact = registry(
        repo,
        {
            "mavenConfig": {"authConfig": "chosen"},
            "authConfig": {
                "chosen": {"provider": "nexus", "authMethod": "anonymous", "credentialsId": "private-used-id"},
                "inactive": {"provider": "nexus", "authMethod": "user_pass", "credentialsId": "private-unused-id"},
            },
        },
    )
    root = catalog(repo, "private-used-id", "private-unused-id")

    inputs = collect(repo)

    assert not any(bag.path == artifact for bag in inputs.bags)
    assert not any(issue.path == artifact for issue in inputs.issues)
    assert not any(item.references for item in analyze(repo))
    assert {item.path for item in check(build_index(repo.root))} == {root}


@pytest.mark.parametrize(
    "override",
    [
        {"mavenConfig": None},
        {"mavenConfig": {}},
        {"mavenConfig": {"authConfig": "${PRIVATE_SELECTOR}"}},
        {"mavenConfig": {"authConfig": "private-unknown-selector"}},
        {"authConfig": []},
        {"authConfig": {"chosen": None}},
        {"authConfig": {"chosen": {"credentialsId": "private-used-id"}}},
        {"authConfig": {"chosen": {"authMethod": "${PRIVATE_METHOD}", "credentialsId": "private-used-id"}}},
        {"authConfig": {"chosen": {"authMethod": "user_pass"}}},
        {"authConfig": {"chosen": {"authMethod": "user_pass", "credentialsId": None}}},
        {"authConfig": {"chosen": {"authMethod": "user_pass", "credentialsId": ""}}},
    ],
)
def test_unresolved_v2_auth_selection_preserves_review_with_uncertainty(repo, override):
    config = {
        "mavenConfig": {"authConfig": "chosen"},
        "authConfig": {
            "chosen": {"provider": "nexus", "authMethod": "user_pass", "credentialsId": "private-used-id"}
        },
    }
    config.update(override)
    artifact = registry(repo, config)
    catalog(repo, "private-used-id")

    inputs = collect(repo)
    usages = analyze(repo)

    assert not any(bag.path == artifact for bag in inputs.bags)
    assert any(issue.path == artifact for issue in inputs.issues)
    assert not any(item.references for item in usages)
    assert all(item.gaps for item in usages)
    for output in (render(check(build_index(repo.root))), render_html(check(build_index(repo.root)), repo.root)):
        assert "private-used-id" not in output
        assert "private-unknown-selector" not in output
        assert "PRIVATE_SELECTOR" not in output
        assert "PRIVATE_METHOD" not in output


def test_version_2_registry_without_auth_config_does_not_use_v1_credentials_id(repo):
    artifact = registry(repo, {"version": "2.0", "credentialsId": "private-used-id"})
    catalog(repo, "private-used-id")

    inputs = collect(repo)

    assert not any(bag.path == artifact for bag in inputs.bags)
    assert any(issue.path == artifact for issue in inputs.issues)
    assert not any(item.references for item in analyze(repo))


def test_dynamic_selected_v2_credential_id_is_uncertain_without_consuming_other_ids(repo):
    registry(
        repo,
        {
            "mavenConfig": {"authConfig": "chosen"},
            "authConfig": {
                "chosen": {"provider": "nexus", "authMethod": "user_pass", "credentialsId": "${PRIVATE_ID}"}
            },
        },
    )
    catalog(repo, "private-unused-id")

    usages = analyze(repo)

    assert not any(item.references for item in usages)
    assert all(any(gap.reason == "dynamic" for gap in item.gaps) for item in usages)


@pytest.mark.parametrize("state", ["missing", "malformed", "outside", "git"])
def test_unavailable_root_catalog_never_falls_back_to_environment_catalog(repo, tmp_path, state):
    artifact = registry(repo, {"credentialsId": "private-used-id"})
    bind(repo, sharedMasterCredentialFiles=["shared"])
    shared(repo, ids=("private-used-id",))
    write(
        repo.root / "environments/c/e/Credentials/credentials.yml",
        {"private-used-id": {"type": "secret"}},
    )
    root = repo.root / "configuration/credentials/credentials.yml"
    outside = None
    if state == "malformed":
        root.parent.mkdir(parents=True)
        root.write_text("broken: [\n", encoding="utf-8")
    elif state in ("outside", "git"):
        target = (tmp_path.parent / f"{tmp_path.name}-outside.yml" if state == "outside"
                  else repo.root / ".git/credentials.yml")
        write(target, {"private-used-id": {"type": "secret"}})
        root.parent.mkdir(parents=True)
        root.symlink_to(target)
        outside = target if state == "outside" else None

    try:
        inputs = collect(repo)
        usages = analyze(repo)
    finally:
        if outside is not None:
            outside.unlink(missing_ok=True)

    bag = next(bag for bag in inputs.bags if bag.path == artifact)
    assert bag.catalog == root
    assert not any(item.references for item in usages)
    assert all(any(gap.reason == "unreadable" for gap in item.gaps) for item in usages)
