import pytest

from pathlib import Path

from click.testing import CliRunner

import envgene_linter.connections as connections_module
from envgene_linter.cli import main
from envgene_linter.connections import compute_connections
from envgene_linter.discovery import build_index
from envgene_linter.engine import run_check
from envgene_linter.html_report import REPORT_FILENAME
from envgene_linter.model import Action, IssueType, Severity
from envgene_linter.rules.place10 import check


def _append_template(repo, cluster: str, env: str, text: str) -> None:
    path = repo.root / "environments" / cluster / env / "Inventory/env_definition.yml"
    with path.open("a", encoding="utf-8") as stream:
        stream.write(text)


def _place10(repo):
    return [finding for finding in run_check(repo.root).findings if finding.rule == "PLACE-10"]


def _write(repo, relative: str, body: str = "{}\n") -> Path:
    path = repo.root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def test_selected_legacy_profile_directory(repo):
    repo.env("c", "e")
    _append_template(repo, "c", "e", "  envSpecificResourceProfiles: {cloud: p}\n")
    directory = repo.root / "environments/c/e/Inventory/rp_override"
    directory.mkdir()
    path = directory / "p.yml"
    path.write_text("{}\n", encoding="utf-8")

    findings = _place10(repo)

    assert len(findings) == 1
    assert findings[0].path == path
    assert findings[0].key == "p"
    assert findings[0].scope == "c/e"
    assert "Resource Profile Override" in findings[0].message
    assert "resource_profiles" in findings[0].message
    assert "resource_profiles" in findings[0].hint


def test_canonical_directories_for_all_five_selected_types(repo):
    repo.env("c", "e", deploy={"cloud": ["params"]}, cloud_passport="passport")
    _append_template(
        repo,
        "c",
        "e",
        "  envSpecificResourceProfiles: {cloud: profile}\n"
        "  sharedMasterCredentialFiles: [creds]\n"
        "  sharedTemplateVariables: [variables]\n",
    )
    repo.env_paramset("c", "e", "params", {"A": 1})
    repo.passport("passport", cluster="c", env="e")
    _write(repo, "environments/c/e/Inventory/resource_profiles/nested/profile.yml")
    _write(repo, "environments/c/e/Inventory/credentials/creds.yml")
    _write(repo, "environments/c/e/Inventory/shared-template-variables/variables.yaml")

    index = build_index(repo.root)
    connections = compute_connections(index)

    assert index.environments[0].shared_template_variable_bindings == ["variables"]
    assert connections.shared_template_variables == frozenset(
        {
            (
                repo.root
                / "environments/c/e/Inventory/shared-template-variables/variables.yaml"
            ).resolve()
        }
    )
    assert connections.shared_template_variables <= connections.selected_paths
    assert check(index, connections) == []


def test_selected_misplaced_files_for_all_five_types(repo):
    repo.env("c", "e", deploy={"cloud": ["params"]}, cloud_passport="passport")
    _append_template(
        repo,
        "c",
        "e",
        "  envSpecificResourceProfiles: {cloud: profile}\n"
        "  sharedMasterCredentialFiles: [creds]\n"
        "  sharedTemplateVariables: [variables]\n",
    )
    _write(repo, "environments/c/e/Inventory/parameters/params.yml", "parameters: {}\n")
    _write(repo, "environments/c/e/Inventory/rp_override/profile.yml")
    _write(repo, "environments/c/e/Inventory/shared-credentials/creds.yml")
    repo.passport("passport", cluster="c", env="e", folder="cloud-passports")
    _write(repo, "environments/c/e/Inventory/configuration/variables.yml")

    findings = _place10(repo)

    assert len(findings) == 4
    assert {finding.key for finding in findings} == {
        "profile",
        "creds",
        "passport",
        "variables",
    }
    assert all(finding.severity is Severity.WARNING for finding in findings)
    assert all(finding.issue_type is IssueType.WARNING for finding in findings)
    assert all(finding.action is Action.FIX for finding in findings)
    assert all(finding.locations[0].line == 1 for finding in findings)
    assert all(finding.locations[0].column == 1 for finding in findings)


def test_selected_parameter_symlink_uses_physical_layout_and_repository_fallback(repo):
    repo.env("c", "e", deploy={"cloud": ["params"]})
    target = _write(repo, "misplaced.yml", "parameters: {}\n")
    alias = repo.root / "environments/parameters/params.yml"
    alias.parent.mkdir(parents=True)
    alias.symlink_to(target.relative_to(alias.parent, walk_up=True))

    findings = _place10(repo)

    assert [(finding.path, finding.key, finding.scope) for finding in findings] == [
        (alias, "params", "repository")
    ]
    assert str(repo.root / "environments/parameters") in findings[0].hint


def test_nested_canonical_folder_under_wrong_first_component_is_misplaced(repo):
    repo.env("c", "e")
    _append_template(repo, "c", "e", "  envSpecificResourceProfiles: {cloud: profile}\n")
    path = _write(
        repo,
        "environments/c/e/Inventory/parameters/resource_profiles/profile.yml",
    )

    assert [(finding.path, finding.key) for finding in _place10(repo)] == [
        (path, "profile")
    ]


def test_selected_malformed_content_is_still_checked(repo):
    repo.env("c", "e")
    _append_template(repo, "c", "e", "  envSpecificResourceProfiles: {cloud: broken}\n")
    path = _write(
        repo,
        "environments/c/e/Inventory/rp_override/broken.yml",
        "not: [valid\n",
    )

    assert [(finding.path, finding.key) for finding in _place10(repo)] == [
        (path, "broken")
    ]


def test_unused_missing_dynamic_external_and_git_files_are_not_reported(repo):
    repo.env("c", "e", deploy={"cloud": ["missing"]})
    _append_template(
        repo,
        "c",
        "e",
        "  envSpecificResourceProfiles: {cloud: missing}\n"
        "  sharedMasterCredentialFiles: [missing]\n"
        "  sharedTemplateVariables: ['{{ dynamic }}', missing]\n",
    )
    _write(repo, "environments/rp_override/unused.yml")
    _write(repo, "environments/shared-credentials/unused.yml")
    _write(repo, "environments/configuration/unused.yml")
    git_target = _write(repo, ".git/params.yml", "parameters: {}\n")
    git_alias = repo.root / "environments/parameters/missing.yml"
    git_alias.parent.mkdir(parents=True, exist_ok=True)
    git_alias.symlink_to(git_target.relative_to(git_alias.parent, walk_up=True))

    assert _place10(repo) == []


def test_shared_template_lookup_uses_legacy_precedence_and_exact_stem(repo):
    repo.env("c", "e")
    _append_template(repo, "c", "e", "  sharedTemplateVariables: [variables]\n")
    winner = _write(repo, "environments/c/e/Inventory/configuration/variables.yaml")
    _write(repo, "environments/c/e/Inventory/configurations/variables.yml")
    _write(repo, "environments/c/configuration/variables.yml")
    _write(repo, "environments/configuration/variables.yml")
    _write(repo, "environments/c/e/Inventory/shared-template-variables/variables.yml")
    _write(repo, "environments/c/e/Inventory/configuration/variables-extra.yml")

    connections = compute_connections(build_index(repo.root))

    assert connections.shared_template_variables == frozenset({winner.resolve()})
    assert connections.environment_paths["c/e"] >= frozenset({winner.resolve()})
    assert [(finding.path, finding.key) for finding in _place10(repo)] == [
        (winner, "variables")
    ]


def test_shared_template_lookup_preserves_os_walk_file_order(repo, monkeypatch):
    repo.env("c", "e")
    _append_template(repo, "c", "e", "  sharedTemplateVariables: [variables]\n")
    directory = repo.root / "environments/c/e/Inventory/configuration"
    yml = _write(repo, "environments/c/e/Inventory/configuration/variables.yml")
    yaml = _write(repo, "environments/c/e/Inventory/configuration/variables.yaml")
    real_walk = connections_module.os.walk

    def ordered_walk(path, *args, **kwargs):
        for root, directories, files in real_walk(path, *args, **kwargs):
            if Path(root) == directory:
                files = ["variables.yaml", "variables.yml"]
            yield root, directories, files

    monkeypatch.setattr(connections_module.os, "walk", ordered_walk)

    connections = compute_connections(build_index(repo.root))

    assert connections.shared_template_variables == frozenset({yaml.resolve()})
    assert yml.resolve() not in connections.shared_template_variables


def test_shared_template_binding_reads_only_string_list_elements(repo):
    repo.env("c", "e")
    _append_template(
        repo,
        "c",
        "e",
        "  sharedTemplateVariables:\n"
        "    - variables\n"
        "    - 42\n"
        "    - {unexpected: mapping}\n",
    )
    selected = _write(repo, "environments/c/e/Inventory/configuration/variables.yml")
    _write(repo, "environments/c/e/Inventory/configuration/42.yml")

    index = build_index(repo.root)
    connections = compute_connections(index)

    assert index.environments[0].shared_template_variable_bindings == ["variables"]
    assert connections.shared_template_variables == frozenset({selected.resolve()})


def test_malformed_shared_template_binding_is_not_selected(repo):
    repo.env("c", "e")
    _append_template(
        repo,
        "c",
        "e",
        "  sharedTemplateVariables: {unexpected: mapping}\n",
    )
    _write(repo, "environments/c/e/Inventory/configuration/unexpected.yml")

    index = build_index(repo.root)

    assert index.environments[0].shared_template_variable_bindings == []
    assert compute_connections(index).shared_template_variables == frozenset()


def test_unsafe_shared_template_winner_does_not_promote_lower_candidate(repo):
    repo.env("c", "e")
    _append_template(repo, "c", "e", "  sharedTemplateVariables: [variables]\n")
    external = repo.root.parent / "external-variables.yml"
    external.write_text("{}\n", encoding="utf-8")
    winner = repo.root / "environments/c/e/Inventory/configuration/variables.yml"
    winner.parent.mkdir(parents=True)
    winner.symlink_to(external)
    _write(repo, "environments/c/e/Inventory/shared-template-variables/variables.yml")

    connections = compute_connections(build_index(repo.root))

    assert connections.shared_template_variables == frozenset()
    assert _place10(repo) == []


def test_git_shared_template_winner_does_not_promote_lower_candidate(repo):
    repo.env("c", "e")
    _append_template(repo, "c", "e", "  sharedTemplateVariables: [variables]\n")
    git_target = _write(repo, ".git/variables.yml")
    winner = repo.root / "environments/c/e/Inventory/configuration/variables.yml"
    winner.parent.mkdir(parents=True)
    winner.symlink_to(git_target.relative_to(winner.parent, walk_up=True))
    _write(repo, "environments/c/e/Inventory/shared-template-variables/variables.yml")

    connections = compute_connections(build_index(repo.root))

    assert connections.shared_template_variables == frozenset()
    assert _place10(repo) == []


def test_selected_alias_is_diagnostic_path_and_physical_type_is_deduplicated(repo):
    repo.env("c", "one")
    repo.env("c", "two")
    for name in ("one", "two"):
        _append_template(
            repo,
            "c",
            name,
            "  envSpecificResourceProfiles: {cloud: selected}\n",
        )
    target = _write(repo, "misplaced-profile.yml")
    directory = repo.root / "environments/resource_profiles"
    directory.mkdir(parents=True)
    (directory / "aaa.yml").symlink_to(target.relative_to(directory, walk_up=True))
    selected = directory / "selected.yml"
    selected.symlink_to(target.relative_to(directory, walk_up=True))

    findings = _place10(repo)

    assert [(finding.path, finding.key) for finding in findings] == [
        (selected, "selected")
    ]


def test_one_physical_file_used_as_two_types_is_checked_once_per_type(repo):
    repo.env("c", "e", deploy={"cloud": ["params"]})
    _append_template(repo, "c", "e", "  envSpecificResourceProfiles: {cloud: profile}\n")
    target = _write(repo, "shared.yml", "parameters: {}\n")
    parameter = repo.root / "environments/parameters/params.yml"
    parameter.parent.mkdir(parents=True)
    parameter.symlink_to(target.relative_to(parameter.parent, walk_up=True))
    profile = repo.root / "environments/resource_profiles/profile.yml"
    profile.parent.mkdir(parents=True)
    profile.symlink_to(target.relative_to(profile.parent, walk_up=True))

    findings = _place10(repo)

    assert [(finding.path, finding.key) for finding in findings] == [
        (parameter, "params"),
        (profile, "profile"),
    ]
    assert {finding.message.split(" ", 1)[0] for finding in findings} == {
        "ParameterSet",
        "Resource",
    }


def test_place9_overlap_is_retained(repo):
    repo.env("c", "one", cloud_passport="one")
    repo.env("c", "two", cloud_passport="two")
    repo.passport("one", cluster="c", folder="cloud-passports")
    repo.passport("two", cluster="c", folder="cloud-passports")

    result = run_check(repo.root).findings

    assert [finding for finding in result if finding.rule == "PLACE-9"]
    assert len([finding for finding in result if finding.rule == "PLACE-10"]) == 2


def test_console_and_html_place10_catalog_order_and_warning_fix(repo):
    repo.env("c", "e")
    _append_template(repo, "c", "e", "  envSpecificResourceProfiles: {cloud: profile}\n")
    _write(repo, "environments/rp_override/profile.yml")

    result = CliRunner().invoke(main, ["check", str(repo.root), "--html"])

    assert result.exit_code == 0
    assert (
        result.output.index("PLACE-9")
        < result.output.index("PLACE-10")
        < result.output.index("NAME-1")
    )
    block = result.output[result.output.index("PLACE-10") : result.output.index("NAME-1")]
    assert "warning" in block
    assert "resource_profiles" in block
    body = (repo.root / REPORT_FILENAME).read_text(encoding="utf-8")
    assert "PLACE-10: Entities belong in their type directories" in body
    assert "PLACE-9:" not in body
    assert "NAME-1:" not in body
    assert "chip-warning" in body
    assert "chip-fix" in body


pytestmark = pytest.mark.usefixtures("all_rules_enabled")
