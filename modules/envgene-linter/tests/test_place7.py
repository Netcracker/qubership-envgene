import pytest

from envgene_linter.discovery import build_index
from envgene_linter.engine import run_check
from envgene_linter.model import Action, IssueType, Location, Severity
from envgene_linter.rules import place7
from envgene_linter.rules.place7 import check

_HINT = "Use a separate ParameterSet for each category, even when the parameter values are identical."


def _place7(repo):
    return check(build_index(repo.root))


@pytest.mark.parametrize(
    "categories",
    [
        ("deploy", "e2e"),
        ("deploy", "technical"),
        ("e2e", "technical"),
        ("deploy", "e2e", "technical"),
    ],
)
def test_conflicting_categories(repo, categories):
    repo.env(
        "cluster-01",
        "env-01",
        **{category: {"cloud": ["shared"]} for category in categories},
    )
    repo.env_paramset("cluster-01", "env-01", "shared", {"VALUE": 1})
    findings = [finding for finding in run_check(repo.root).findings if finding.rule == "PLACE-7"]
    assert len(findings) == 1
    assert findings[0].key == "shared"
    assert findings[0].scope == "cluster-01/env-01"
    assert findings[0].message == (
        "ParameterSet 'shared' is bound to multiple categories: "
        + ", ".join(categories)
        + "."
    )


def test_conflict_across_different_targets_has_warning_fix_metadata(repo):
    repo.env(
        "cluster-01",
        "env-01",
        deploy={"cloud": ["shared"]},
        technical={"bss": ["shared"]},
    )
    repo.env_paramset("cluster-01", "env-01", "shared", {"VALUE": 1})

    findings = _place7(repo)

    assert len(findings) == 1
    item = findings[0]
    assert item.rule == "PLACE-7"
    assert item.severity is Severity.WARNING
    assert item.issue_type is IssueType.WARNING
    assert item.action is Action.FIX
    assert item.key == "shared"
    assert item.scope == "cluster-01/env-01"
    assert item.related == ()
    assert item.message == "ParameterSet 'shared' is bound to multiple categories: deploy, technical."
    assert item.hint == _HINT
    assert item.path.name == "env_definition.yml"
    assert item.locations == (
        Location(item.path, 7, 9),
        Location(item.path, 10, 9),
    )
    assert (item.line, item.column) == (7, 9)


def test_reuse_and_duplicates_within_one_category_are_allowed(repo):
    repo.env(
        "cluster-01",
        "env-01",
        deploy={"cloud": ["shared", "shared"], "bss": ["shared"]},
    )
    assert _place7(repo) == []


def test_separate_names_and_missing_bindings_are_allowed(repo):
    repo.env(
        "cluster-01",
        "env-01",
        deploy={"cloud": ["deploy-only"]},
        technical={"cloud": ["technical-only"]},
    )
    repo.env("cluster-01", "env-02")
    assert _place7(repo) == []


def test_literal_empty_binding_list_is_allowed(repo):
    repo.env("cluster-01", "env-01")
    path = repo.root / "environments/cluster-01/env-01/Inventory/env_definition.yml"
    path.write_text(
        "inventory:\n"
        "  environmentName: env-01\n"
        "envTemplate:\n"
        "  envSpecificParamsets:\n"
        "    cloud: []\n"
        "  envSpecificE2EParamsets:\n"
        "    cloud: [pipeline-only]\n",
        encoding="utf-8",
    )
    assert _place7(repo) == []


def test_environment_without_conflicts_is_not_reloaded(repo, monkeypatch):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["deploy-only"]})
    index = build_index(repo.root)

    def unexpected_load(path):
        raise AssertionError(f"unexpected reload of {path}")

    monkeypatch.setattr(place7, "load", unexpected_load)
    assert check(index) == []


def test_categories_are_not_aggregated_across_environments(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["shared"]})
    repo.env("cluster-01", "env-02", e2e={"cloud": ["shared"]})
    assert _place7(repo) == []


def test_multiple_conflicts_are_sorted_by_path_then_exact_name(repo):
    repo.env(
        "cluster-02",
        "env-02",
        deploy={"cloud": ["zeta", "Alpha"]},
        e2e={"cloud": ["Alpha", "zeta"]},
    )
    repo.env_paramset("cluster-02", "env-02", "zeta", {"VALUE": 1})
    repo.env_paramset("cluster-02", "env-02", "Alpha", {"VALUE": 1})
    repo.env_paramset("cluster-01", "env-01", "beta", {"VALUE": 1})
    repo.env(
        "cluster-01",
        "env-01",
        deploy={"cloud": ["beta"]},
        technical={"cloud": ["beta"]},
    )

    findings = _place7(repo)

    assert [(item.scope, item.key) for item in findings] == [
        ("cluster-01/env-01", "beta"),
        ("cluster-02/env-02", "Alpha"),
        ("cluster-02/env-02", "zeta"),
    ]


def test_names_use_exact_case_and_require_resolved_files(repo):
    repo.env(
        "cluster-01",
        "env-01",
        deploy={"cloud": ["Shared", "shared.yml", "shared"]},
        e2e={"cloud": ["shared"]},
    )
    repo.env_paramset("cluster-01", "env-01", "shared", {"VALUE": 1})
    findings = _place7(repo)
    assert [item.key for item in findings] == ["shared"]


def test_reordered_blocks_and_yaml_aliases_use_sorted_deduplicated_item_positions(repo):
    repo.env("cluster-01", "env-01")
    path = repo.root / "environments/cluster-01/env-01/Inventory/env_definition.yml"
    path.write_text(
        "inventory:\n"
        "  environmentName: env-01\n"
        "envTemplate:\n"
        "  envSpecificTechnicalParamsets:\n"
        "    bss: &shared_refs\n"
        "      - shared\n"
        "      - shared\n"
        "  envSpecificParamsets:\n"
        "    cloud: *shared_refs\n"
        "  envSpecificE2EParamsets:\n"
        "    cloud:\n"
        "      - shared\n",
        encoding="utf-8",
    )
    repo.env_paramset("cluster-01", "env-01", "shared", {"VALUE": 1})

    findings = _place7(repo)

    assert len(findings) == 1
    item = findings[0]
    assert item.message == (
        "ParameterSet 'shared' is bound to multiple categories: deploy, e2e, technical."
    )
    assert item.locations == (
        Location(path, 6, 9),
        Location(path, 7, 9),
        Location(path, 12, 9),
    )
    assert (item.line, item.column) == (6, 9)


def test_reload_failure_skips_only_the_unreadable_environment(repo):
    repo.env(
        "cluster-01",
        "env-01",
        deploy={"cloud": ["first"]},
        e2e={"cloud": ["first"]},
    )
    repo.env_paramset("cluster-01", "env-01", "first", {"VALUE": 1})
    repo.env_paramset("cluster-01", "env-02", "second", {"VALUE": 1})
    repo.env(
        "cluster-01",
        "env-02",
        deploy={"cloud": ["second"]},
        technical={"cloud": ["second"]},
    )
    index = build_index(repo.root)
    bad_path = repo.root / "environments/cluster-01/env-01/Inventory/env_definition.yml"
    bad_path.write_bytes(b"\xff\xfe")

    findings = check(index)

    assert [(item.scope, item.key) for item in findings] == [
        ("cluster-01/env-02", "second")
    ]


def test_missing_position_falls_back_to_file_start_and_deduplicates(repo):
    repo.env(
        "cluster-01",
        "env-01",
        deploy={"cloud": ["shared"]},
        e2e={"cloud": ["shared"]},
    )
    repo.env_paramset("cluster-01", "env-01", "shared", {"VALUE": 1})
    index = build_index(repo.root)
    path = repo.root / "environments/cluster-01/env-01/Inventory/env_definition.yml"
    path.write_text("inventory:\n  environmentName: env-01\n", encoding="utf-8")

    findings = check(index)

    assert len(findings) == 1
    assert findings[0].locations == (Location(path, 1, 1),)
    assert (findings[0].line, findings[0].column) == (1, 1)


def test_unresolved_references_are_filtered_without_renumbering_locations(repo):
    repo.env(
        "cluster-01",
        "env-01",
        deploy={"cloud": ["missing-deploy", "shared"]},
        e2e={"cloud": ["missing-e2e", "shared"]},
    )
    repo.env_paramset("cluster-01", "env-01", "shared", {"VALUE": 1})

    findings = _place7(repo)

    assert len(findings) == 1
    path = repo.root / "environments/cluster-01/env-01/Inventory/env_definition.yml"
    assert findings[0].locations == (
        Location(path, 8, 9),
        Location(path, 12, 9),
    )


def test_unresolved_name_in_multiple_categories_is_silent(repo):
    repo.env(
        "cluster-01",
        "env-01",
        deploy={"cloud": ["missing"]},
        technical={"cloud": ["missing"]},
    )
    assert _place7(repo) == []


pytestmark = pytest.mark.usefixtures("all_rules_enabled")
