import pytest

from pathlib import Path

from envgene_linter.connections import compute_connections
from envgene_linter.discovery import build_index
from envgene_linter.engine import run_check
from envgene_linter.model import Action, IssueType, Severity


def _write(root: Path, relative: str, body: str = "version: 1.5\n") -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _place9(repo) -> list:
    return [finding for finding in run_check(repo.root).findings if finding.rule == "PLACE-9"]


def test_one_automatic_default_passport_is_allowed(repo):
    repo.env("c", "e")
    repo.passport("passport", cluster="c")
    assert _place9(repo) == []


def test_one_default_and_explicit_passport_infra_are_allowed(repo):
    repo.env("c", "default")
    repo.env("c", "infra", cloud_passport="passport-infra")
    repo.passport("passport", cluster="c")
    repo.passport("passport-infra", cluster="c")
    assert _place9(repo) == []


def test_two_used_custom_default_passports_report_one_cluster_role_finding(repo):
    repo.env("c", "a", cloud_passport="one")
    repo.env("c", "b", cloud_passport="two")
    repo.passport("one", cluster="c")
    repo.passport("two", cluster="c")

    findings = _place9(repo)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.key == "default"
    assert finding.scope == "c"
    assert {location.path.name for location in finding.file_locations()} == {
        "one.yml",
        "two.yml",
    }
    assert finding.severity is Severity.WARNING
    assert finding.issue_type is IssueType.WARNING
    assert finding.action is Action.FIX


def test_passport_infra_role_name_is_exact(repo):
    repo.env("c", "a")
    repo.env("c", "b", cloud_passport="Passport-infra")
    repo.passport("passport", cluster="c")
    repo.passport("Passport-infra", cluster="c")
    assert [_finding.key for _finding in _place9(repo)] == ["default"]


def test_selected_physical_passports_are_counted_once_and_per_cluster(repo):
    repo.env("a", "one", cloud_passport="shared")
    repo.env("a", "two", cloud_passport="alias")
    repo.env("b", "one", cloud_passport="first")
    repo.env("b", "two", cloud_passport="second")
    shared = _write(repo.root, "environments/a/cloud-passport/shared.yml")
    alias = repo.root / "environments/a/cloud-passport/alias.yml"
    alias.symlink_to(shared.name)
    repo.passport("first", cluster="b")
    repo.passport("second", cluster="b")

    findings = _place9(repo)

    assert [(finding.scope, finding.key) for finding in findings] == [("b", "default")]


def test_unused_extra_and_missing_explicit_passports_are_silent(repo):
    repo.env("c", "auto")
    repo.env("c", "missing", cloud_passport="does-not-exist")
    repo.passport("passport", cluster="c")
    repo.passport("unused-one", cluster="c")
    repo.passport("unused-two", cluster="c")
    assert _place9(repo) == []


def test_explicit_duplicate_resolution_is_deduplicated_across_environments(repo):
    repo.env("c", "a", cloud_passport="dup")
    repo.env("c", "b", cloud_passport="dup")
    cluster_passport = _write(repo.root, "environments/c/cloud-passport/dup.yml")
    repo_passport = _write(repo.root, "environments/cloud-passport/dup.yaml")

    findings = _place9(repo)

    assert len(findings) == 1
    finding = findings[0]
    locations = finding.file_locations()
    assert {location.path for location in locations if location.path.name.startswith("dup.")} == {
        cluster_passport,
        repo_passport,
    }
    definitions = [location for location in locations if location.path.name == "env_definition.yml"]
    assert [(location.line, location.column) for location in definitions] == [(3, 3), (3, 3)]
    assert finding.key == "dup"
    assert "multiple" in finding.message.lower()


def test_auto_resolution_stops_after_cluster_name_bucket(repo):
    repo.env("c", "e")
    selected = _write(repo.root, "environments/c/cloud-passport/c.yml")
    _write(repo.root, "environments/c/cloud-passport/passport.yml")
    _write(repo.root, "environments/c/cloud-passport/passport.yaml")

    index = build_index(repo.root)
    connections = compute_connections(index)

    assert connections.environment_passports["c/e"].path == selected
    assert _place9(repo) == []


def test_duplicate_first_auto_bucket_reports_definition_origin(repo):
    repo.env("c", "e")
    first = _write(repo.root, "environments/c/cloud-passport/c.yml")
    second = _write(repo.root, "environments/c/cloud-passport/c.yaml")

    findings = _place9(repo)

    assert len(findings) == 1
    assert {location.path for location in findings[0].file_locations()} == {
        first,
        second,
        repo.root / "environments/c/e/Inventory/env_definition.yml",
    }
    definition = next(
        location
        for location in findings[0].file_locations()
        if location.path.name == "env_definition.yml"
    )
    assert (definition.line, definition.column) == (1, 1)


def test_physical_aliases_do_not_create_an_ambiguity_finding(repo):
    repo.env("c", "e", cloud_passport="dup")
    original = _write(repo.root, "environments/c/cloud-passport/dup.yml")
    alias = repo.root / "environments/cloud-passport/dup.yml"
    alias.parent.mkdir(parents=True)
    alias.symlink_to(original)
    assert _place9(repo) == []


def test_external_and_dot_git_candidates_are_ignored_for_ambiguity(repo):
    repo.env("c", "e", cloud_passport="dup")
    _write(repo.root, "environments/cloud-passport/dup.yml")
    outside = _write(repo.root.parent, f"{repo.root.name}-outside-dup.yml")
    external_alias = repo.root / "environments/c/cloud-passport/dup.yml"
    external_alias.parent.mkdir(parents=True)
    external_alias.symlink_to(outside)
    hidden = _write(repo.root, "hidden/dup.yaml")
    dot_git = repo.root / "environments/c/cloud-passport/.git/dup.yaml"
    dot_git.parent.mkdir(parents=True)
    dot_git.symlink_to(hidden)
    assert _place9(repo) == []


def test_malformed_selected_passport_still_counts_for_cardinality(repo):
    repo.env("c", "a", cloud_passport="broken")
    repo.env("c", "b", cloud_passport="valid")
    _write(repo.root, "environments/c/cloud-passport/broken.yml", "[not valid\n")
    repo.passport("valid", cluster="c")
    assert [(finding.scope, finding.key) for finding in _place9(repo)] == [("c", "default")]


def test_selected_repository_passport_remains_place3_only(repo):
    repo.env("c", "e", cloud_passport="shared")
    repo.passport("shared")
    result = run_check(repo.root)
    assert [finding for finding in result.findings if finding.rule == "PLACE-9"] == []
    assert len([finding for finding in result.findings if finding.rule == "PLACE-3"]) == 1


def test_selected_cluster_passport_in_plural_folder_is_reported(repo):
    repo.env("c", "e", cloud_passport="custom")
    path = _write(repo.root, "environments/c/cloud-passports/custom.yml")
    findings = _place9(repo)
    assert len(findings) == 1
    assert findings[0].path == path
    assert findings[0].key == "custom"
    assert "cloud-passport" in findings[0].hint


def test_selected_nested_cluster_passport_under_canonical_folder_is_allowed(repo):
    repo.env("c", "e", cloud_passport="custom")
    _write(repo.root, "environments/c/cloud-passport/team/custom.yml")
    assert _place9(repo) == []


def test_adjacent_selected_credentials_are_allowed(repo):
    repo.env("c", "e", cloud_passport="custom")
    repo.passport("custom", cluster="c")
    _write(repo.root, "environments/c/cloud-passport/custom-creds.yml", "synthetic: {}\n")
    assert _place9(repo) == []


def test_adjacent_credentials_in_noncanonical_folder_are_reported(repo):
    repo.env("c", "e", cloud_passport="custom")
    _write(repo.root, "environments/c/cloud-passports/custom.yml")
    credential = _write(
        repo.root,
        "environments/c/cloud-passports/custom-creds.yml",
        "synthetic: {}\n",
    )
    finding = next(finding for finding in _place9(repo) if finding.path == credential)
    assert "appropriate cluster cloud-passport folder" in finding.message
    assert finding.hint == "Move it beside the passport under the appropriate cluster's cloud-passport folder."


def test_first_existing_subfolder_credentials_are_reported_even_with_adjacent_copy(repo):
    repo.env("c", "e", cloud_passport="custom")
    passport = _write(repo.root, "environments/c/cloud-passport/custom.yml")
    used = _write(
        repo.root,
        "environments/c/cloud-passport/credentials/custom.yml",
        "synthetic: {}\n",
    )
    _write(repo.root, "environments/c/cloud-passport/custom-creds.yml", "synthetic: {}\n")

    findings = _place9(repo)

    assert len(findings) == 1
    assert findings[0].path == used
    assert {location.path for location in findings[0].file_locations()} == {used, passport}
    assert "credentials" in findings[0].message.lower()


def test_missing_unused_and_yaml_credentials_are_silent(repo):
    repo.env("c", "e", cloud_passport="custom")
    repo.passport("custom", cluster="c")
    _write(repo.root, "environments/c/cloud-passport/custom-creds.yaml", "synthetic: {}\n")
    _write(repo.root, "environments/c/cloud-passport/unused-creds.yml", "synthetic: {}\n")
    assert _place9(repo) == []


def test_external_first_credential_slot_does_not_promote_adjacent_fallback(repo):
    repo.env("c", "e", cloud_passport="custom")
    repo.passport("custom", cluster="c")
    outside = _write(repo.root.parent, f"{repo.root.name}-outside-custom-creds.yml", "synthetic: {}\n")
    first = repo.root / "environments/c/cloud-passport/credentials/custom.yml"
    first.parent.mkdir(parents=True)
    first.symlink_to(outside)
    _write(repo.root, "environments/c/cloud-passport/custom-creds.yml", "synthetic: {}\n")
    assert _place9(repo) == []


def test_direct_check_matches_engine_and_findings_are_sorted(repo):
    from envgene_linter.rules.place9 import check

    repo.env("a", "e", cloud_passport="bad")
    repo.env("b", "one", cloud_passport="one")
    repo.env("b", "two", cloud_passport="two")
    _write(repo.root, "environments/a/cloud-passports/bad.yml")
    repo.passport("one", cluster="b")
    repo.passport("two", cluster="b")
    index = build_index(repo.root)
    connections = compute_connections(index)

    direct = check(index, connections)
    engine = [finding for finding in run_check(repo.root).findings if finding.rule == "PLACE-9"]

    assert direct == engine
    assert [(finding.path.as_posix(), finding.key, finding.line) for finding in direct] == sorted(
        (finding.path.as_posix(), finding.key, finding.line) for finding in direct
    )


pytestmark = pytest.mark.usefixtures("all_rules_enabled")
