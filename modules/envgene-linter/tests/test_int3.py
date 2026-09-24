from pathlib import Path

import pytest
from click.testing import CliRunner
from ruamel.yaml import YAML

from envgene_linter import rule_config
from envgene_linter.cli import main
from envgene_linter.connections import compute_connections
from envgene_linter.discovery import build_index
from envgene_linter.engine import run_check
from envgene_linter.model import Action, IssueType, Severity
from envgene_linter.rules.int3 import check

KINDS = ("ParameterSet", "Shared credentials", "Resource Profile Override", "Shared Template Variables")
FOLDERS = ("parameters", "credentials", "resource_profiles", "configuration")
FIELDS = ("envSpecificParamsets", "sharedMasterCredentialFiles", "envSpecificResourceProfiles", "sharedTemplateVariables")
BASES = ("environments/c01/e01/Inventory", "environments/c01", "environments")


def _write(repo, relative, text="{}\n"):
    path = repo.root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _bind(repo, kind, references=("shared",), cluster="c01", env="e01"):
    repo.env(cluster, env)
    path = repo.root / f"environments/{cluster}/{env}/Inventory/env_definition.yml"
    yaml = YAML()
    doc = yaml.load(path)
    value = list(references)
    if kind == "ParameterSet":
        value = {"cloud": value}
    elif kind == "Resource Profile Override":
        value = {"cloud": references[0]}
    doc["envTemplate"][FIELDS[KINDS.index(kind)]] = value
    yaml.dump(doc, path)


def _file(repo, kind, scope, reference="shared", suffix=".yml", text="{}\n"):
    return _write(repo, f"{BASES[scope]}/{FOLDERS[KINDS.index(kind)]}/{reference}{suffix}", text)


def _check(repo):
    return check(build_index(repo.root))


def test_environment_and_cluster_reference_conflict(repo):
    repo.env("c01", "e01", deploy={"cloud": ["service-deploy"]})
    repo.cluster_paramset("c01", "service-deploy", {"CLUSTER_VALUE": 1})
    repo.env_paramset("c01", "e01", "service-deploy", {"ENV_VALUE": 2})
    findings = [item for item in run_check(repo.root).findings if item.rule == "INT-3"]
    assert len(findings) == 1
    assert {item.path for item in findings[0].file_locations()} == {
        repo.root / "environments/c01/parameters/service-deploy.yml",
        repo.root / "environments/c01/e01/Inventory/parameters/service-deploy.yml",
    }
    assert "ignored" not in findings[0].message


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("scopes", [(0, 1), (1, 2), (0, 2), (0, 1, 2)])
def test_used_cross_scope_definitions(repo, kind, scopes):
    _bind(repo, kind)
    paths = [_file(repo, kind, scope) for scope in scopes]
    findings = _check(repo)
    assert len(findings) == 1
    finding = findings[0]
    assert [location.path for location in finding.file_locations()] == paths
    assert all((location.line, location.column) == (1, 1) for location in finding.file_locations())
    assert finding.scope == "c01/e01"
    assert finding.key == kind
    assert (finding.severity, finding.issue_type, finding.action) == (
        Severity.WARNING, IssueType.WARNING, Action.FIX,
    )


@pytest.mark.parametrize("kind", KINDS)
def test_extensions_share_a_stem_across_scopes(repo, kind):
    _bind(repo, kind)
    paths = [_file(repo, kind, 0, suffix=".yaml"), _file(repo, kind, 2)]
    assert [item.path for item in _check(repo)[0].file_locations()] == paths


@pytest.mark.parametrize("kind", KINDS)
def test_one_scope_is_not_a_cross_scope_conflict(repo, kind):
    _bind(repo, kind)
    _file(repo, kind, 1)
    _file(repo, kind, 1, suffix=".yaml")
    assert _check(repo) == []


@pytest.mark.parametrize("kind", KINDS)
def test_unused_duplicates_and_equal_internal_names_are_silent(repo, kind):
    _bind(repo, kind, ("used",))
    _file(repo, kind, 0, reference="used", text="name: shared\n")
    _file(repo, kind, 1, reference="other", text="name: shared\n")
    _file(repo, kind, 0)
    _file(repo, kind, 2)
    assert _check(repo) == []


@pytest.mark.parametrize("kind", KINDS)
def test_other_environments_do_not_supply_candidates(repo, kind):
    _bind(repo, kind)
    _file(repo, kind, 0)
    folder = FOLDERS[KINDS.index(kind)]
    _write(repo, f"environments/c01/e02/Inventory/{folder}/shared.yml")
    _write(repo, f"environments/c02/{folder}/shared.yml")
    assert _check(repo) == []


@pytest.mark.parametrize("kind", KINDS)
def test_each_consuming_environment_retains_its_context(repo, kind):
    _bind(repo, kind)
    _bind(repo, kind, env="e02")
    _file(repo, kind, 1)
    _file(repo, kind, 2)
    assert [f.scope for f in _check(repo)] == ["c01/e01", "c01/e02"]


def test_repeated_categories_and_targets_share_one_finding(repo):
    repo.env("c01", "e01", deploy={"cloud": ["shared", "shared"], "ns": ["shared"]},
             e2e={"cloud": ["shared"]}, technical={"cloud": ["shared"]})
    _file(repo, "ParameterSet", 0)
    _file(repo, "ParameterSet", 1)
    assert len(_check(repo)) == 1


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("content", ["", "[broken YAML"])
def test_content_does_not_erase_a_filename_conflict(repo, kind, content):
    _bind(repo, kind)
    _file(repo, kind, 0, text=content)
    _file(repo, kind, 1)
    assert len(_check(repo)) == 1


@pytest.mark.parametrize("kind", KINDS)
def test_jinja_is_not_a_candidate(repo, kind):
    _bind(repo, kind)
    _file(repo, kind, 0, suffix=".yml.j2")
    _file(repo, kind, 1)
    assert _check(repo) == []


@pytest.mark.parametrize("reference", ["${NAME}", "{{ name }}", "name}}", "{#name#}", "nested/shared"])
def test_dynamic_and_path_references_are_not_inferred(repo, reference):
    _bind(repo, "ParameterSet", (reference,))
    _file(repo, "ParameterSet", 0, reference=reference)
    _file(repo, "ParameterSet", 1, reference=reference)
    assert _check(repo) == []


def test_credential_ids_are_not_filename_references(repo):
    _bind(repo, "Shared credentials", ("one", "two"))
    content = "same-id:\n  type: secret\n  data:\n    secret: placeholder\n"
    _file(repo, "Shared credentials", 0, reference="one", text=content)
    _file(repo, "Shared credentials", 1, reference="two", text=content)
    assert _check(repo) == []


@pytest.mark.parametrize(("kind", "first", "second"), [
    ("Resource Profile Override", "resource_profiles", "rp_override"),
    ("Shared credentials", "credentials", "shared-credentials"),
])
def test_first_matching_directory_per_scope(repo, kind, first, second):
    _bind(repo, kind)
    selected = _write(repo, f"{BASES[0]}/{first}/nested/shared.yml")
    _write(repo, f"{BASES[0]}/{second}/shared.yml")
    lower = _write(repo, f"{BASES[1]}/{second}/shared.yaml")
    assert [item.path for item in _check(repo)[0].file_locations()] == [selected, lower]


def test_variable_inventory_fallback_keeps_logical_scope(repo):
    _bind(repo, "Shared Template Variables")
    fallback = _write(repo, f"{BASES[0]}/shared-template-variables/shared.yml")
    selected = _file(repo, "Shared Template Variables", 1)
    findings = _check(repo)
    assert len(findings) == 1
    assert [item.path for item in findings[0].file_locations()] == [fallback, selected]


def test_variable_inventory_fallback_deduplicates_configuration(repo):
    _bind(repo, "Shared Template Variables")
    selected = _file(repo, "Shared Template Variables", 0)
    lower = _file(repo, "Shared Template Variables", 2)
    assert [item.path for item in _check(repo)[0].file_locations()] == [selected, lower]


def test_unsearched_variable_directories_do_not_contribute(repo):
    _bind(repo, "Shared Template Variables")
    _file(repo, "Shared Template Variables", 0)
    _write(repo, "environments/shared-template-variables/shared.yml")
    assert _check(repo) == []


@pytest.mark.parametrize("kind", KINDS)
def test_file_alias_is_one_physical_definition(repo, kind):
    _bind(repo, kind)
    lower = _file(repo, kind, 1)
    alias = repo.root / f"{BASES[0]}/{FOLDERS[KINDS.index(kind)]}/shared.yml"
    alias.parent.mkdir(parents=True, exist_ok=True)
    alias.symlink_to(lower)
    assert _check(repo) == []


def test_variable_selected_alias_scope_precedes_inventory_fallback(repo):
    _bind(repo, "Shared Template Variables")
    selected = _file(repo, "Shared Template Variables", 1)
    fallback = repo.root / f"{BASES[0]}/shared.yml"
    fallback.symlink_to(selected)
    same_scope = _write(repo, f"{BASES[1]}/configuration/nested/shared.yml")
    # The fallback alias must not turn two cluster definitions into two scopes.
    assert same_scope != selected
    assert _check(repo) == []


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("target", ["external", "git", "broken", "cycle", "directory"])
def test_unsafe_candidates_are_excluded(repo, kind, target, tmp_path):
    _bind(repo, kind)
    _file(repo, kind, 0)
    folder = repo.root / f"{BASES[1]}/{FOLDERS[KINDS.index(kind)]}"
    folder.mkdir(parents=True, exist_ok=True)
    candidate = folder / "shared.yml"
    # Test the rule's own path guards against a changed filesystem. Legacy discovery
    # can fail on cyclic links before any check is invoked.
    candidate.write_text("{}\n")
    index = build_index(repo.root)
    connections = compute_connections(index)
    candidate.unlink()
    if target == "directory":
        actual = _write(repo, "elsewhere/shared.yml")
        (folder / "nested").symlink_to(actual.parent, target_is_directory=True)
    elif target == "git":
        candidate.symlink_to(_write(repo, ".git/hidden.yml"))
    elif target == "external":
        outside = tmp_path.parent / f"{tmp_path.name}-outside.yml"
        outside.write_text("{}\n")
        candidate.symlink_to(outside)
    else:
        candidate.symlink_to(candidate if target == "cycle" else folder / "missing.yml")
    assert check(index, connections) == []


def test_directory_enumeration_failure_is_a_generic_skip(repo, monkeypatch):
    _bind(repo, "Shared Template Variables")
    _file(repo, "Shared Template Variables", 0)
    lower = _file(repo, "Shared Template Variables", 1)
    index = build_index(repo.root)
    connections = compute_connections(index)
    import os
    original = os.scandir

    def denied(path):
        if Path(path) == lower.parent:
            raise PermissionError("sensitive-exception-content")
        return original(path)

    monkeypatch.setattr(os, "scandir", denied)
    assert check(index, connections) == []
    assert any("INT-3" in note and "cannot enumerate" in note for note in index.skipped)
    assert all("sensitive-exception-content" not in note for note in index.skipped)


def test_variable_lookup_keeps_the_generators_unsorted_first_match(repo, monkeypatch):
    _bind(repo, "Shared Template Variables")
    selected = _write(repo, f"{BASES[0]}/configuration/z/shared.yml")
    other = _write(repo, f"{BASES[0]}/configuration/a/shared.yml")
    lower = _file(repo, "Shared Template Variables", 1)
    # A real filesystem may return either directory first. Force the generator's
    # permitted reverse order to catch a checker that silently selects a new winner.
    import os
    original = os.walk

    def reverse_walk(*args, **kwargs):
        for base, directories, files in original(*args, **kwargs):
            directories.sort(reverse=True)
            yield base, directories, files

    monkeypatch.setattr(os, "walk", reverse_walk)
    index = build_index(repo.root)
    connections = compute_connections(index)
    assert selected in connections.shared_template_variables
    findings = check(index, connections)
    assert len(findings) == 1
    assert {location.path for location in findings[0].file_locations()} == {selected, other, lower}


def test_cli_reports_conflict_without_credential_content(repo, monkeypatch):
    _bind(repo, "Shared credentials")
    secret = "placeholder-secret-value"
    identifier = "private-credential-id"
    body = f"{identifier}:\n  type: secret\n  data:\n    secret: {secret}\n"
    paths = [_file(repo, "Shared credentials", scope, text=body) for scope in (0, 1)]
    flags = dict.fromkeys(rule_config.RULES, False)
    flags["INT-3"] = True
    monkeypatch.setattr(rule_config, "RULE_ENABLED", flags)
    result = CliRunner().invoke(main, ["check", str(repo.root), "--console"])
    assert result.exit_code == 0, result.output
    html = (repo.root / "envgene-linter-report.html").read_text()
    for output in (result.output, html):
        assert "INT-3" in output
        assert secret not in output
        assert identifier not in output
        assert all(str(path.relative_to(repo.root)) in output for path in paths)
    assert result.output.index("INT-2\n") < result.output.index("INT-3\n") < result.output.index("NAME-1\n")


def test_disabling_int3_preserves_other_findings(repo, monkeypatch):
    repo.env("c01", "e01", deploy={"cloud": ["shared"]})
    repo.site_paramset("shared", {"COUNT": 1})
    repo.cluster_paramset("c01", "shared", {"COUNT": 2})
    repo.env_paramset("c01", "e01", "shared", {"COUNT": 2})
    enabled = run_check(repo.root)
    assert any(f.rule == "INT-3" for f in enabled.findings)
    monkeypatch.setitem(rule_config.RULE_ENABLED, "INT-3", False)
    disabled = run_check(repo.root)
    assert [f for f in enabled.findings if f.rule != "INT-3"] == disabled.findings
    result = CliRunner().invoke(main, ["check", str(repo.root), "--console"])
    assert "INT-3\nDisabled" in result.output
    html = (repo.root / "envgene-linter-report.html").read_text()
    assert "Disabled rules" in html and "INT-3" in html
