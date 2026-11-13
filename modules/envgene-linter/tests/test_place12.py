import json

import pytest

from envgene_linter.connections import compute_connections
from envgene_linter.discovery import build_index
from envgene_linter.effective import compute
from envgene_linter.model import Action, IssueType, Severity
from envgene_linter.passport import build_catalogs
from envgene_linter.rules import place12

ARTIFACT = "example-env-templates:1.0.0"
FIELDS = {
    "deploy": "envSpecificParamsets",
    "e2e": "envSpecificE2EParamsets",
    "technical": "envSpecificTechnicalParamsets",
}


def _env(
    repo,
    cluster,
    name="env-01",
    params=None,
    *,
    template="business",
    artifact=ARTIFACT,
    target="oss",
    category="deploy",
    application=None,
    stem="params",
    layer="environment",
):
    repo.env(cluster, name)
    inventory = repo.root / "environments" / cluster / name / "Inventory"
    definition = {
        "inventory": {"environmentName": name},
        "envTemplate": {
            "name": template,
            "artifact": artifact,
            FIELDS[category]: {target: [stem]},
        },
    }
    (inventory / "env_definition.yml").write_text(json.dumps(definition))
    directory = {
        "environment": inventory / "parameters",
        "cluster": repo.root / "environments" / cluster / "parameters",
        "repository": repo.root / "environments/parameters",
    }[layer]
    directory.mkdir(parents=True, exist_ok=True)
    params = {"SETTING": "shared-default-value"} if params is None else params
    payload = {"name": stem, "parameters": params}
    if application:
        payload = {
            "name": stem,
            "applications": [{"appName": application, "parameters": params}],
        }
    path = directory / f"{stem}.yml"
    path.write_text(json.dumps(payload))
    return path


def _inputs(repo):
    index = build_index(repo.root)
    connections = compute_connections(index)
    return (
        index,
        {env.full_name: compute(index, env) for env in index.environments},
        build_catalogs(index, connections),
    )


def _check(repo):
    index, full, catalogs = _inputs(repo)
    return place12.check(index, full, catalogs)


def _add_reference(repo, cluster, reference, name="env-01"):
    path = repo.root / "environments" / cluster / name / "Inventory/env_definition.yml"
    data = json.loads(path.read_text())
    data["envTemplate"]["envSpecificParamsets"]["oss"].append(reference)
    path.write_text(json.dumps(data))


def test_two_clusters_emit_one_information_review(repo):
    first = _env(repo, "cluster-01")
    second = _env(repo, "cluster-02")
    findings = _check(repo)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule == "PLACE-12" and finding.key == "SETTING"
    assert finding.severity is Severity.INFORMATION
    assert (
        finding.issue_type is IssueType.INFORMATION and finding.action is Action.REVIEW
    )
    assert {location.path for location in finding.file_locations()} == {first, second}
    assert "2 environments using template" in finding.message
    assert "cluster" not in finding.message
    assert "business" in finding.message
    assert "from 'example-env-templates'." in finding.message
    assert ARTIFACT in str(finding.related)
    assert "shared-default-value" not in finding.message + str(finding.related)
    assert "shared-default-value" in finding.hint
    assert "ParameterSet YAML:" in finding.hint
    assert "--template-repo" in finding.hint


def test_same_cluster_emits_one_information_review(repo):
    first = _env(repo, "cluster-01", "env-01")
    second = _env(repo, "cluster-01", "env-02")
    findings = _check(repo)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.issue_type is IssueType.INFORMATION
    assert finding.action is Action.REVIEW
    assert {location.path for location in finding.file_locations()} == {first, second}
    assert "2 environments using template" in finding.message
    assert "cluster" not in finding.message


def test_one_environment_cannot_establish_repetition(repo):
    _env(repo, "cluster-01")
    assert _check(repo) == []


def test_same_cluster_shared_source_does_not_count_as_repeated_authorship(repo):
    _env(repo, "cluster-01", "env-01", layer="cluster")
    _env(repo, "cluster-01", "env-02", layer="cluster")
    assert _check(repo) == []


@pytest.mark.parametrize("third", [{}, {"OTHER": "value"}, {"SETTING": "different"}])
def test_same_cluster_requires_agreement_from_every_bound_consumer(repo, third):
    _env(repo, "cluster-01", "env-01")
    _env(repo, "cluster-01", "env-02")
    _env(repo, "cluster-01", "env-03", params=third)
    assert _check(repo) == []


@pytest.mark.parametrize(
    "change",
    [
        {"template": "platform"},
        {"artifact": "other-env-templates:1.0.0"},
        {"artifact": "Example-env-templates:1.0.0"},
        {"artifact": "example-env-templates :1.0.0"},
        {"artifact": None},
        {"template": "{{ selected }}"},
        {"target": "tools"},
        {"category": "e2e"},
        {"category": "technical"},
    ],
)
def test_different_template_or_scope_does_not_establish_agreement(repo, change):
    _env(repo, "cluster-01")
    _env(repo, "cluster-02", **change)
    assert _check(repo) == []


@pytest.mark.parametrize("second_cluster", ["cluster-01", "cluster-02"])
@pytest.mark.parametrize(
    "artifact",
    [
        "example-env-templates:2.0.0",
        "example-env-templates:release-SNAPSHOT",
        "example-env-templates",
        "example-env-templates:2.0.0:build-17",
    ],
)
def test_artifact_versions_share_a_group_and_retain_original_references(
    repo, second_cluster, artifact
):
    first = _env(repo, "cluster-01", "env-01")
    second = _env(repo, second_cluster, "env-02", artifact=artifact)
    findings = _check(repo)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.action is Action.REVIEW
    assert "2 environments using template" in finding.message
    assert "from 'example-env-templates'." in finding.message
    assert ARTIFACT not in finding.message + finding.scope
    assert {location.path for location in finding.file_locations()} == {first, second}
    for environment, reference in (
        ("cluster-01/env-01", ARTIFACT),
        (second_cluster + "/env-02", artifact),
    ):
        assert any(
            environment in entry and repr(reference) in entry
            for entry in finding.related
        )


@pytest.mark.parametrize("artifact", [":1.0.0", " :1.0.0"])
def test_empty_artifact_names_cannot_establish_a_group(repo, artifact):
    _env(repo, "cluster-01", artifact=artifact)
    _env(repo, "cluster-02", artifact=artifact)
    assert _check(repo) == []


@pytest.mark.parametrize("third", [{}, {"SETTING": "different-value"}])
def test_another_artifact_version_participates_in_agreement(repo, third):
    _env(repo, "cluster-01")
    _env(repo, "cluster-02")
    _env(repo, "cluster-03", params=third, artifact="example-env-templates:2.0.0")
    assert _check(repo) == []


def test_incomplete_consumer_on_another_version_blocks_the_group(repo):
    _env(repo, "cluster-01")
    _env(repo, "cluster-02")
    third = _env(repo, "cluster-03", artifact="example-env-templates:2.0.0")
    third.unlink()
    index, full, catalogs = _inputs(repo)
    assert place12.check(index, full, catalogs) == []
    assert any(check.rule == "PLACE-12" for check in index.skipped_checks)


def test_application_scopes_must_match(repo):
    _env(repo, "cluster-01", application="app-a")
    _env(repo, "cluster-02", application="app-b")
    assert _check(repo) == []


def test_matching_application_scopes_are_compared(repo):
    _env(repo, "cluster-01", application="app-a")
    _env(repo, "cluster-02", application="app-a")
    findings = _check(repo)
    assert len(findings) == 1 and "app-a" in findings[0].scope


@pytest.mark.parametrize(
    "third", [{}, {"OTHER": "value"}, {"SETTING": "different-value"}]
)
def test_every_bound_consumer_must_supply_the_same_key_value(repo, third):
    _env(repo, "cluster-01")
    _env(repo, "cluster-02")
    _env(repo, "cluster-03", params=third)
    assert _check(repo) == []


def test_conflict_inside_one_cluster_blocks_majority_agreement(repo):
    _env(repo, "cluster-01")
    _env(repo, "cluster-02")
    _env(repo, "cluster-01", "env-02", {"SETTING": "different-value"})
    assert _check(repo) == []


def test_missing_application_bag_blocks_agreement(repo):
    _env(repo, "cluster-01", application="app-a")
    _env(repo, "cluster-02", application="app-a")
    _env(repo, "cluster-03", params={})
    assert _check(repo) == []


def test_unrelated_target_is_not_a_consumer(repo):
    _env(repo, "cluster-01")
    _env(repo, "cluster-02")
    _env(repo, "cluster-03", params={}, target="tools")
    assert [finding.key for finding in _check(repo)] == ["SETTING"]


@pytest.mark.parametrize(
    ("left", "right"), [(True, 1), (1, 1.0), ("true", True), ([1, 2], [2, 1])]
)
def test_typed_or_ordered_value_difference_blocks_agreement(repo, left, right):
    _env(repo, "cluster-01", params={"SETTING": left})
    _env(repo, "cluster-02", params={"SETTING": right})
    assert _check(repo) == []


def test_nested_agreement_is_independent_of_other_conflicts(repo):
    _env(repo, "cluster-01", params={"OPTIONS": {"common": "same", "different": 1}})
    _env(repo, "cluster-02", params={"OPTIONS": {"common": "same", "different": 2}})
    assert [finding.key for finding in _check(repo)] == ["OPTIONS.common"]


def test_mapping_order_inside_lists_does_not_change_equality(repo):
    _env(repo, "cluster-01", params={"SETTING": [{"first": 1, "second": 2}]})
    _env(repo, "cluster-02", params={"SETTING": [{"second": 2, "first": 1}]})
    assert [finding.key for finding in _check(repo)] == ["SETTING"]


@pytest.mark.parametrize(
    "value",
    [
        None,
        "${values.setting}",
        "{{ setting }}",
        ["${values.setting}"],
        [{"apiToken": "synthetic-not-a-real-secret"}],
    ],
)
def test_unknown_or_secret_containing_values_are_not_defaults(repo, value):
    _env(repo, "cluster-01", params={"SETTING": value})
    _env(repo, "cluster-02", params={"SETTING": value})
    assert _check(repo) == []


@pytest.mark.parametrize("key", ["CLOUD_API_HOST", "DB_PASSWORD", "apiToken"])
def test_passport_and_secret_keys_are_excluded(repo, key):
    _env(repo, "cluster-01", params={key: "synthetic-not-a-real-secret"})
    _env(repo, "cluster-02", params={key: "synthetic-not-a-real-secret"})
    assert _check(repo) == []


def test_custom_passport_contract_keys_are_excluded(repo):
    _env(repo, "cluster-01", params={"CUSTOM_INFRA_KEY": "same"})
    _env(repo, "cluster-02", params={"CUSTOM_INFRA_KEY": "same"})
    repo.passport(
        "passport", {"infra": {"CUSTOM_INFRA_KEY": "same"}}, cluster="cluster-01"
    )
    assert _check(repo) == []


def test_exact_local_identifier_is_not_a_template_default(repo):
    _env(repo, "cluster-01", params={"SETTING": "cluster-01"})
    _env(repo, "cluster-02", params={"SETTING": "cluster-01"})
    assert _check(repo) == []


@pytest.mark.parametrize(
    ("layer", "count"), [("environment", 1), ("cluster", 1), ("repository", 0)]
)
def test_origin_requires_distinct_cluster_owned_sources(repo, layer, count):
    _env(repo, "cluster-01", layer=layer)
    _env(repo, "cluster-02", layer=layer)
    assert len(_check(repo)) == count


def test_shared_physical_source_does_not_count_as_two_sources(repo):
    first = _env(repo, "cluster-01")
    second = _env(repo, "cluster-02")
    second.unlink()
    second.symlink_to(first)
    assert _check(repo) == []


def test_repository_source_aliases_do_not_establish_cluster_evidence(repo):
    for cluster, stem in (("cluster-01", "first"), ("cluster-02", "second")):
        source = _env(repo, cluster, stem=stem, layer="repository")
        alias = (
            repo.root
            / "environments"
            / cluster
            / "env-01/Inventory/parameters"
            / source.name
        )
        alias.parent.mkdir(parents=True)
        alias.symlink_to(source)
    assert _check(repo) == []


def test_repository_owned_consumer_is_not_dropped_from_agreement(repo):
    _env(repo, "cluster-01")
    _env(repo, "cluster-02")
    _env(repo, "cluster-03", layer="repository")
    assert _check(repo) == []


def test_alias_of_one_cluster_does_not_manufacture_repetition(repo):
    _env(repo, "cluster-01")
    (repo.root / "environments/cluster-02").symlink_to(
        repo.root / "environments/cluster-01", target_is_directory=True
    )
    assert _check(repo) == []


def test_different_parameter_set_names_can_supply_the_same_default(repo):
    _env(repo, "cluster-01", stem="first")
    _env(repo, "cluster-02", stem="second")
    assert len(_check(repo)) == 1


def test_repeated_references_do_not_duplicate_source_locations(repo):
    _env(repo, "cluster-01")
    _env(repo, "cluster-02")
    _add_reference(repo, "cluster-01", "params")
    findings = _check(repo)
    assert len(findings) == 1 and len(findings[0].file_locations()) == 2


@pytest.mark.parametrize("kind", ["missing", "jinja", "malformed"])
def test_incomplete_selected_input_blocks_other_readable_values(repo, kind):
    _env(repo, "cluster-01")
    _env(repo, "cluster-02")
    _add_reference(repo, "cluster-02", "extra")
    directory = repo.root / "environments/cluster-02/env-01/Inventory/parameters"
    if kind == "jinja":
        (directory / "extra.yml.j2").write_text("name: extra\nparameters: {}\n")
    elif kind == "malformed":
        (directory / "extra.yml").write_text("parameters: [\n")
    index, full, catalogs = _inputs(repo)
    assert place12.check(index, full, catalogs) == []
    assert any(check.rule == "PLACE-12" for check in index.skipped_checks)


@pytest.mark.parametrize("kind", ["missing", "ambiguous", "jinja", "malformed"])
def test_unknown_selected_passport_does_not_reduce_to_standard_key_table(repo, kind):
    _env(repo, "cluster-01")
    _env(repo, "cluster-02")
    definition = (
        repo.root / "environments/cluster-01/env-01/Inventory/env_definition.yml"
    )
    data = json.loads(definition.read_text())
    data["inventory"]["cloudPassport"] = "passport"
    definition.write_text(json.dumps(data))
    directory = repo.root / "environments/cluster-01/cloud-passport"
    directory.mkdir()
    if kind == "ambiguous":
        for folder in ("first", "second"):
            (directory / folder).mkdir()
            (directory / folder / "passport.yml").write_text("version: 1.5\n")
    elif kind == "jinja":
        (directory / "passport.yml.j2").write_text("version: 1.5\n")
    elif kind == "malformed":
        (directory / "passport.yml").write_text("infra: [\n")
    index, full, catalogs = _inputs(repo)
    assert place12.check(index, full, catalogs) == []
    assert any(check.rule == "PLACE-12" for check in index.skipped_checks)


@pytest.mark.parametrize(
    "body",
    [
        "parameters:\n  SETTING: !custom [1, 2]\n",
        "parameters:\n  OPTIONS: !custom {common: same}\n",
        "parameters: !custom {SETTING: same}\n",
    ],
)
def test_raw_tagged_containers_cannot_gain_certainty_after_normalization(repo, body):
    for cluster in ("cluster-01", "cluster-02"):
        path = _env(repo, cluster)
        path.write_text("name: params\n" + body)
    assert _check(repo) == []


def test_recursive_analysis_value_does_not_establish_agreement(repo):
    _env(repo, "cluster-01", params={"SETTING": []})
    _env(repo, "cluster-02", params={"SETTING": []})
    index, full, catalogs = _inputs(repo)
    for environment in full.values():
        for mapping in environment.scopes.values():
            mapping[("SETTING",)].value.append(mapping[("SETTING",)].value)
    assert place12.check(index, full, catalogs) == []


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("apiToken", True),
        ("DB_PASSWORD", True),
        ("service.privateKey", True),
        ("TOKENIZER", False),
        ("PASSWORD_POLICY", False),
    ],
)
def test_shared_secret_name_policy_preserves_existing_semantics(name, expected):
    from envgene_linter.security_values import is_secret_parameter_name

    assert is_secret_parameter_name(name) is expected


@pytest.mark.parametrize(
    "payload",
    [
        {"parameters": []},
        {"applications": {}},
        {"applications": [{"appName": "app-a", "parameters": []}]},
        {"applications": [None]},
    ],
)
def test_invalid_selected_shape_cannot_be_ignored_as_empty(repo, payload):
    _env(repo, "cluster-01")
    _env(repo, "cluster-02")
    _add_reference(repo, "cluster-02", "extra")
    path = repo.root / "environments/cluster-02/env-01/Inventory/parameters/extra.yml"
    path.write_text(json.dumps({"name": "extra", **payload}))
    index, full, catalogs = _inputs(repo)
    assert place12.check(index, full, catalogs) == []
    assert any(check.rule == "PLACE-12" for check in index.skipped_checks)


@pytest.mark.parametrize("second_cluster", ["cluster-01", "cluster-02"])
def test_engine_runs_place12_with_the_default_configuration(repo, second_cluster):
    from envgene_linter.engine import run_check

    _env(repo, "cluster-01")
    _env(repo, second_cluster, "env-02")
    findings = [
        finding
        for finding in run_check(repo.root).findings
        if finding.rule == "PLACE-12"
    ]
    assert len(findings) == 1 and findings[0].action is Action.REVIEW


def test_disabled_place12_has_no_findings_or_own_read_diagnostics(repo, monkeypatch):
    from envgene_linter import rule_config
    from envgene_linter.engine import run_check

    path = _env(repo, "cluster-01")
    _env(repo, "cluster-02")
    path.write_text("parameters: [\n")
    monkeypatch.setitem(rule_config.RULE_ENABLED, "PLACE-12", False)
    result = run_check(repo.root)
    assert not any(finding.rule == "PLACE-12" for finding in result.findings)
    assert not any(check.rule == "PLACE-12" for check in result.skipped_checks)


def test_template_only_root_marks_place12_not_applicable(tmp_path):
    from envgene_linter.engine import run_check

    (tmp_path / "templates").mkdir()
    result = run_check(tmp_path)
    assert "PLACE-12" in result.not_applicable_rules
    assert not any(finding.rule == "PLACE-12" for finding in result.findings)


def test_selected_parameter_read_failure_is_visible_for_place12(repo):
    from envgene_linter.engine import run_check

    path = _env(repo, "cluster-01")
    _env(repo, "cluster-02")
    path.write_text("parameters: [\n")
    result = run_check(repo.root)
    assert not any(finding.rule == "PLACE-12" for finding in result.findings)
    assert any(
        check.rule == "PLACE-12" and check.path == path
        for check in result.skipped_checks
    )


@pytest.mark.parametrize("second_cluster", ["cluster-01", "cluster-02"])
def test_place12_findings_reach_html_and_six_field_json_reports(repo, second_cluster):
    from html import escape

    from click.testing import CliRunner

    from envgene_linter.cli import main

    _env(repo, "cluster-01")
    _env(repo, second_cluster, "env-02", artifact="example-env-templates:2.0.0")
    result = CliRunner().invoke(main, ["check", str(repo.root), "--console"])
    assert result.exit_code == 0, result.output
    records = json.loads((repo.root / "envgene-linter-report.json").read_text())
    records = [record for record in records if record["rule_id"] == "PLACE-12"]
    assert len(records) == 1
    assert set(records[0]) == {
        "rule_id",
        "rule_title",
        "files",
        "issue",
        "action",
        "fix_suggestion",
    }
    assert records[0]["action"] == "Review"
    assert "from 'example-env-templates'." in records[0]["issue"]
    assert ARTIFACT not in records[0]["issue"]
    assert ":2.0.0" not in records[0]["issue"]
    hint = records[0]["fix_suggestion"]
    assert "shared-default-value" in hint and "ParameterSet YAML:" in hint
    assert 'Namespace association for "oss"' in hint
    assert "as the last item in template_override.deployParameterSets" in hint
    assert "Reference item to append:" in hint
    assert "Create file:" not in hint and "Edit file:" not in hint
    assert len(records[0]["files"]) == 2
    assert hint in result.output
    body = (repo.root / "envgene-linter-report.html").read_text()
    assert "PLACE-12" in body and escape(records[0]["issue"]) in body
    assert escape(hint) in body


@pytest.mark.parametrize(
    "parameters",
    [
        {"SETTING": [{"${env.name}": "same"}]},
        {"${env.name}": "same"},
        {"OPTIONS": {"{{ current_env.name }}": "same"}},
    ],
)
def test_expression_mapping_keys_never_establish_literal_agreement(repo, parameters):
    from envgene_linter.engine import run_check

    _env(repo, "cluster-01", params=parameters)
    _env(repo, "cluster-02", params=parameters)
    result = run_check(repo.root)
    assert not any(finding.rule == "PLACE-12" for finding in result.findings)


@pytest.mark.parametrize(
    "bindings",
    [
        {"{{ target }}": ["params"]},
        {"oss": "${selected.paramsets}"},
        {"oss": {"name": "params"}},
        "${selected.bindings}",
        ["params"],
        None,
        {"oss": [True]},
    ],
)
def test_unknown_binding_membership_blocks_the_whole_template_group(repo, bindings):
    from envgene_linter.engine import run_check

    _env(repo, "cluster-01")
    _env(repo, "cluster-02")
    third = _env(repo, "cluster-03", params={"SETTING": "conflicting-value"})
    definition = third.parent.parent / "env_definition.yml"
    data = json.loads(definition.read_text())
    data["envTemplate"]["envSpecificParamsets"] = bindings
    definition.write_text(json.dumps(data))
    result = run_check(repo.root)
    assert not any(finding.rule == "PLACE-12" for finding in result.findings)
    assert any(
        check.rule == "PLACE-12" and check.path == definition
        for check in result.skipped_checks
    )


@pytest.mark.parametrize(
    "bindings",
    [
        "!custom {oss: [params]}",
        "{oss: !custom [params]}",
        "{1: [params]}",
    ],
)
def test_tagged_or_nonstring_binding_membership_is_unknown(repo, bindings):
    from envgene_linter.engine import run_check

    _env(repo, "cluster-01")
    _env(repo, "cluster-02")
    third = _env(repo, "cluster-03", params={"SETTING": "conflicting-value"})
    definition = third.parent.parent / "env_definition.yml"
    definition.write_text(
        "envTemplate:\n  name: business\n  artifact: "
        + ARTIFACT
        + "\n  envSpecificParamsets: "
        + bindings
        + "\n"
    )
    result = run_check(repo.root)
    assert not any(finding.rule == "PLACE-12" for finding in result.findings)
    assert any(
        check.rule == "PLACE-12" and check.path == definition
        for check in result.skipped_checks
    )


@pytest.mark.parametrize("bindings", [{}, {"oss": []}])
def test_known_absent_bindings_do_not_make_unrelated_environments_uncertain(
    repo, bindings
):
    from envgene_linter.engine import run_check

    _env(repo, "cluster-01")
    _env(repo, "cluster-02")
    third = _env(repo, "cluster-03", params={"SETTING": "conflicting-value"})
    definition = third.parent.parent / "env_definition.yml"
    data = json.loads(definition.read_text())
    data["envTemplate"]["envSpecificParamsets"] = bindings
    definition.write_text(json.dumps(data))
    result = run_check(repo.root)
    assert (
        len([finding for finding in result.findings if finding.rule == "PLACE-12"]) == 1
    )
    assert not any(check.rule == "PLACE-12" for check in result.skipped_checks)


def test_common_values_from_one_source_set_form_one_group(repo):
    first = _env(
        repo, "cluster-01", params={"FIRST": "shared", "NESTED": {"SECOND": True}}
    )
    second = _env(
        repo, "cluster-02", params={"FIRST": "shared", "NESTED": {"SECOND": True}}
    )
    findings = _check(repo)
    assert len(findings) == 1
    assert "2 shared parameters" in findings[0].message
    assert "params" in findings[0].message
    assert len(findings[0].file_locations()) == 4
    assert {loc.path for loc in findings[0].file_locations()} == {first, second}
    assert findings[0].hint.count("ParameterSet YAML:") == 1
    assert "FIRST" in findings[0].hint and "SECOND" in findings[0].hint
    assert "FIRST" in findings[0].key and "SECOND" in findings[0].key


def test_source_reference_combinations_are_separate_groups(repo):
    for cluster in ("cluster-01", "cluster-02"):
        _env(repo, cluster, params={"FIRST": "shared"}, stem="first")
        _add_reference(repo, cluster, "second")
        definition = repo.root / "environments" / cluster / "env-01/Inventory"
        (definition / "parameters/second.yml").write_text(
            json.dumps({"name": "second", "parameters": {"SECOND": "shared"}})
        )
    findings = _check(repo)
    assert len(findings) == 2
    assert {f.key for f in findings} == {"FIRST", "SECOND"}
    assert all("1 shared parameter" in f.message for f in findings)


def test_candidate_guards_apply_before_grouping(repo):
    values = {
        "SHARED": "public",
        "API_PASSWORD": "hidden",
        "EXPRESSION": "{{ value }}",
        "DIFFERS": "one",
    }
    _env(repo, "cluster-01", params=values)
    _env(repo, "cluster-02", params=dict(values, DIFFERS="two"))
    findings = _check(repo)
    assert len(findings) == 1 and findings[0].key == "SHARED"
    assert "hidden" not in findings[0].hint
    assert "API_PASSWORD" not in findings[0].hint


def test_cli_with_explicit_template_context_emits_one_copyable_recipe(repo, tmp_path):
    from html import escape

    from click.testing import CliRunner

    from envgene_linter.cli import main
    from envgene_linter.engine import run_check

    values = {"FIRST": "shared", "OPTIONS": {"enabled": "true"}}
    first = _env(repo, "cluster-01", params=dict(values, LOCAL="first"))
    second = _env(
        repo,
        "cluster-02",
        params=dict(values, LOCAL="second"),
        artifact="example-env-templates:2.0.0",
    )
    original = {p: p.read_bytes() for p in (first, second)}
    source = tmp_path / "template-source"
    descriptors = source / "templates/env_templates"
    descriptors.mkdir(parents=True)
    (descriptors / "business.yml").write_text(
        json.dumps(
            {
                "namespaces": [
                    {
                        "template_path": "{{ templates_dir }}/env_templates/oss.yml",
                        "deploy_postfix": "oss",
                    }
                ]
            }
        )
    )
    (descriptors / "oss.yml").write_text(json.dumps({"deployParameterSets": []}))
    result = CliRunner().invoke(
        main, ["check", str(repo.root), "--template-repo", str(source)]
    )
    assert result.exit_code == 0, result.output
    records = [
        r
        for r in json.loads((repo.root / "envgene-linter-report.json").read_text())
        if r["rule_id"] == "PLACE-12"
    ]
    assert len(records) == 1 and len(records[0]["files"]) == 4
    assert "templates/parameters/oss-common-deploy.yml" in records[0]["fix_suggestion"]
    assert "templates/env_templates/business.yml" in records[0]["fix_suggestion"]
    assert "Descriptor YAML:" in records[0]["fix_suggestion"]
    placement = (
        'Append "oss-common-deploy" as the last item in '
        "template_override.deployParameterSets."
    )
    assert placement in records[0]["fix_suggestion"]
    assert 'existing namespaces entry for "oss"' in records[0]["fix_suggestion"]
    body = (repo.root / "envgene-linter-report.html").read_text()
    assert escape(records[0]["fix_suggestion"]) in body
    assert "type" not in records[0]
    direct = [
        f
        for f in run_check(repo.root, template_repo=source).findings
        if f.rule == "PLACE-12"
    ]
    assert direct[0].hint == records[0]["fix_suggestion"]
    assert all(path.read_bytes() == contents for path, contents in original.items())


def test_cli_rejects_a_missing_explicit_template_root(repo, tmp_path):
    from click.testing import CliRunner

    from envgene_linter.cli import main

    _env(repo, "cluster-01")
    result = CliRunner().invoke(
        main, ["check", str(repo.root), "--template-repo", str(tmp_path / "missing")]
    )
    assert result.exit_code == 2
    assert "does not exist" in result.output


def test_proposed_name_reserves_other_selected_instance_references(repo, tmp_path):
    from envgene_linter.engine import run_check

    for cluster in ("cluster-01", "cluster-02"):
        _env(
            repo, cluster, params={"SETTING": "shared-default-value", "LOCAL": cluster}
        )
        _add_reference(repo, cluster, "oss-common-deploy")
        inventory = repo.root / "environments" / cluster / "env-01/Inventory"
        (inventory / "parameters/oss-common-deploy.yml").write_text(
            json.dumps({"name": "oss-common-deploy", "parameters": {"VARIES": cluster}})
        )
    source = tmp_path / "template-source/templates/env_templates"
    source.mkdir(parents=True)
    (source / "business.yml").write_text(
        json.dumps(
            {
                "namespaces": [
                    {"template_path": "{{ templates_dir }}/env_templates/oss.yml.j2"}
                ]
            }
        )
    )
    (source / "oss.yml.j2").write_text(json.dumps({"deployParameterSets": []}))
    findings = [
        f
        for f in run_check(repo.root, template_repo=source.parent.parent).findings
        if f.rule == "PLACE-12"
    ]
    assert len(findings) == 1
    assert 'name: "oss-common-deploy-2"' in findings[0].hint
    assert (
        str(source.parent / "parameters/oss-common-deploy.yml") not in findings[0].hint
    )


def _relocation_template(tmp_path):
    source = tmp_path / "relocation-template"
    descriptors = source / "templates/env_templates"
    descriptors.mkdir(parents=True)
    (descriptors / "business.yml").write_text(
        json.dumps(
            {
                "cloud": "{{ templates_dir }}/env_templates/cloud.yml.j2",
                "namespaces": [
                    {
                        "template_path": "{{ templates_dir }}/env_templates/oss.yml.j2",
                        "deploy_postfix": "oss",
                    }
                ],
            }
        )
    )
    for target in ("cloud", "oss"):
        (descriptors / f"{target}.yml.j2").write_text(
            json.dumps(
                {
                    "deployParameterSets": [],
                    "e2eParameterSets": [],
                    "technicalConfigurationParameterSets": [],
                }
            )
        )
    return source


@pytest.mark.parametrize("variant", ["whole", "partial", "unresolved"])
@pytest.mark.parametrize("templates_directory", [False, True])
def test_explicit_repository_paths_identify_both_roots_in_every_recommendation(
    repo, tmp_path, variant, templates_directory
):
    from html import escape

    from click.testing import CliRunner

    from envgene_linter.cli import main
    from envgene_linter.engine import run_check

    source = _relocation_template(tmp_path / "template sources")
    template = "unknown" if variant == "unresolved" else "business"
    for cluster in ("cluster-01", "cluster-02"):
        params = {"SETTING": "shared-default-value"}
        if variant == "partial":
            params["LOCAL"] = cluster
        _env(repo, cluster, params=params, template=template)
    originals = {
        path: path.read_bytes() for path in repo.root.rglob("*") if path.is_file()
    }
    selected = source / "templates" if templates_directory else source

    result = CliRunner().invoke(
        main, ["check", "-i", str(repo.root), "-t", str(selected), "--console"]
    )

    assert result.exit_code == 0, result.output
    records = [
        record
        for record in json.loads((repo.root / "envgene-linter-report.json").read_text())
        if record["rule_id"] == "PLACE-12"
    ]
    assert len(records) == 1
    record = records[0]
    assert set(record) == {
        "rule_id",
        "rule_title",
        "files",
        "issue",
        "action",
        "fix_suggestion",
    }
    hint = record["fix_suggestion"]
    assert f"Instance repository: {repo.root.resolve()}\n" in hint
    assert f"Template repository: {source.absolute()}\n" in hint
    assert ("Whole ParameterSet transfer candidate." in hint) == (variant == "whole")
    assert ("Descriptor YAML:" in hint) == (variant == "partial")
    if variant in {"whole", "partial"}:
        stem = "params" if variant == "whole" else "oss-common-deploy"
        assert (
            f"Create file: {source / 'templates/parameters' / (stem + '.yml')}\n"
            in hint
        )
        assert "Template repository changes:\n" in hint
    if variant == "partial":
        assert f"Edit file: {source / 'templates/env_templates/business.yml'}:" in hint
        assert (
            "YAML path: namespaces[0].template_override.deployParameterSets\n" in hint
        )
    if variant == "unresolved":
        assert "Create file:" not in hint and "Edit file:" not in hint
    html = (repo.root / "envgene-linter-report.html").read_text()
    assert escape(hint) in html
    assert hint in result.output
    direct = [
        finding
        for finding in run_check(repo.root, template_repo=selected).findings
        if finding.rule == "PLACE-12"
    ]
    assert direct[0].hint == hint
    assert all(path.read_bytes() == contents for path, contents in originals.items())
    assert not (source / "envgene-linter-report.html").exists()
    assert not (source / "envgene-linter-report.json").exists()
    assert not (source / ".gitignore").exists()


@pytest.mark.parametrize("category", ["deploy", "e2e", "technical"])
def test_complete_paramset_relocation_preserves_the_existing_binding(
    repo, tmp_path, category
):
    from envgene_linter.engine import run_check
    from envgene_linter.parsing import parse_yaml

    files = [
        _env(repo, cluster, category=category)
        for cluster in ("cluster-01", "cluster-02")
    ]
    source = _relocation_template(tmp_path)
    originals = {path: path.read_bytes() for path in files}
    findings = [
        f
        for f in run_check(repo.root, template_repo=source).findings
        if f.rule == "PLACE-12"
    ]
    assert len(findings) == 1
    hint = findings[0].hint
    assert "Whole ParameterSet transfer candidate." in hint
    assert f"Create file: {source / 'templates/parameters/params.yml'}\n" in hint
    assert (
        "Keep the existing Environment Inventory bindings and reference order." in hint
    )
    assert FIELDS[category] in hint
    assert "Descriptor YAML:" not in hint
    assert "Edit file:" not in hint
    assert "No descriptor override is needed." in hint
    assert all(f"- {path}\n" in hint for path in files)
    payload = parse_yaml(hint.split("ParameterSet YAML:\n", 1)[1].split("\n\n", 1)[0])
    assert payload == {
        "name": "params",
        "parameters": {"SETTING": "shared-default-value"},
    }
    assert all(path.read_bytes() == contents for path, contents in originals.items())


@pytest.mark.parametrize(
    "scenario",
    [
        "partial",
        "occupied",
        "wrong_name",
        "another_binding",
        "another_consumer",
        "layered",
        "unknown_field",
        "applications_differ",
        "excluded_secret",
        "different_names",
        "null_applications",
        "unknown_application_field",
    ],
)
def test_whole_relocation_rejects_incomplete_or_conflicting_sources(
    repo, tmp_path, scenario
):
    from envgene_linter.engine import run_check

    first = _env(repo, "cluster-01")
    second = _env(
        repo,
        "cluster-02",
        stem="different" if scenario == "different_names" else "params",
    )
    source = _relocation_template(tmp_path)
    for number, path in enumerate((first, second)):
        doc = json.loads(path.read_text())
        if scenario == "partial":
            doc["parameters"]["LOCAL"] = str(number)
        elif scenario == "wrong_name":
            doc["name"] = "wrong"
        elif scenario == "unknown_field":
            doc["custom"] = "metadata"
        elif scenario == "applications_differ":
            doc["applications"] = [
                {"appName": "worker", "parameters": {"LOCAL": str(number)}}
            ]
        elif scenario == "excluded_secret":
            doc["parameters"]["API_PASSWORD"] = "private-value"
        elif scenario == "null_applications":
            doc["applications"] = None
        elif scenario == "unknown_application_field":
            doc["applications"] = [
                {"appName": "worker", "parameters": {}, "private": "private-value"}
            ]
        path.write_text(json.dumps(doc))
    if scenario == "occupied":
        path = source / "templates/parameters/params.yml"
        path.parent.mkdir()
        path.write_text(
            json.dumps({"name": "params", "parameters": {"SETTING": "different"}})
        )
    elif scenario == "another_binding":
        path = first.parent.parent / "env_definition.yml"
        doc = json.loads(path.read_text())
        doc["envTemplate"]["envSpecificE2EParamsets"] = {"cloud": ["params"]}
        path.write_text(json.dumps(doc))
    elif scenario == "another_consumer":
        _env(repo, "cluster-03", template="another", params={"SETTING": "different"})
    elif scenario == "layered":
        path = repo.root / "environments/cluster-01/parameters/params.yml"
        path.parent.mkdir()
        path.write_text(
            json.dumps({"name": "params", "parameters": {"SETTING": "lower"}})
        )
    findings = [
        f
        for f in run_check(repo.root, template_repo=source).findings
        if f.rule == "PLACE-12"
    ]
    assert len(findings) == 1
    assert "Whole ParameterSet transfer candidate." not in findings[0].hint
    if scenario == "occupied":
        assert "Conflict:" in findings[0].hint
        assert "Instance repository changes:" not in findings[0].hint
    else:
        assert "Descriptor YAML:" in findings[0].hint
    assert "private-value" not in findings[0].hint


@pytest.mark.parametrize("versions, retained", [([1, 1], True), ([1, "2"], False)])
def test_complete_relocation_documents_version_normalization(
    repo, tmp_path, versions, retained
):
    from envgene_linter.engine import run_check
    from envgene_linter.parsing import parse_yaml

    for cluster, version in zip(("cluster-01", "cluster-02"), versions):
        path = _env(repo, cluster)
        doc = json.loads(path.read_text())
        doc["version"] = version
        path.write_text(json.dumps(doc))
    finding = next(
        f
        for f in run_check(
            repo.root, template_repo=_relocation_template(tmp_path)
        ).findings
        if f.rule == "PLACE-12"
    )
    assert "Whole ParameterSet transfer candidate." in finding.hint
    payload = parse_yaml(
        finding.hint.split("ParameterSet YAML:\n", 1)[1].split("\n\n", 1)[0]
    )
    assert ("version" in payload) is retained
    if retained:
        assert payload["version"] == 1
    else:
        assert "omits the deprecated version field" in finding.hint


def test_application_only_paramset_can_move_without_broadening_its_scope(
    repo, tmp_path
):
    from envgene_linter.engine import run_check
    from envgene_linter.parsing import parse_yaml

    for cluster in ("cluster-01", "cluster-02"):
        _env(repo, cluster, application="worker")
    finding = next(
        f
        for f in run_check(
            repo.root, template_repo=_relocation_template(tmp_path)
        ).findings
        if f.rule == "PLACE-12"
    )
    assert "Whole ParameterSet transfer candidate." in finding.hint
    payload = parse_yaml(
        finding.hint.split("ParameterSet YAML:\n", 1)[1].split("\n\n", 1)[0]
    )
    assert payload["applications"] == [
        {"appName": "worker", "parameters": {"SETTING": "shared-default-value"}}
    ]
    assert not payload.get("parameters")


def test_partial_recommendation_does_not_reserve_the_name_of_a_later_whole_transfer(
    repo, tmp_path
):
    from envgene_linter.engine import run_check

    for cluster in ("cluster-01", "cluster-02"):
        path = _env(repo, cluster)
        definition = path.parent.parent / "env_definition.yml"
        doc = json.loads(definition.read_text())
        doc["envTemplate"]["envSpecificE2EParamsets"] = {"cloud": ["pipeline"]}
        definition.write_text(json.dumps(doc))
        (path.parent / "pipeline.yml").write_text(
            json.dumps(
                {
                    "name": "pipeline",
                    "parameters": {"COMMON": "shared", "LOCAL": cluster},
                }
            )
        )
    source = _relocation_template(tmp_path)
    findings = [
        f
        for f in run_check(repo.root, template_repo=source).findings
        if f.rule == "PLACE-12"
    ]
    assert len(findings) == 2
    assert (
        sum("Whole ParameterSet transfer candidate." in f.hint for f in findings) == 1
    )
    whole = next(
        f for f in findings if "Whole ParameterSet transfer candidate." in f.hint
    )
    assert f"Create file: {source / 'templates/parameters/params.yml'}\n" in whole.hint


def test_whole_transfer_rejects_linked_template_parameter_directories(repo, tmp_path):
    from envgene_linter.engine import run_check

    for cluster in ("cluster-01", "cluster-02"):
        _env(repo, cluster)
    source = _relocation_template(tmp_path)
    directory = source / "templates/parameters"
    directory.mkdir()
    outside = tmp_path / "outside-parameters"
    outside.mkdir()
    (directory / "linked").symlink_to(outside, target_is_directory=True)
    finding = next(
        f
        for f in run_check(repo.root, template_repo=source).findings
        if f.rule == "PLACE-12"
    )
    assert "Whole ParameterSet transfer candidate." not in finding.hint


def test_relocation_preserves_other_consumers_of_a_physical_source(repo, tmp_path):
    from envgene_linter.engine import run_check

    first = _env(repo, "cluster-01")
    _env(repo, "cluster-02")
    alias = _env(
        repo,
        "cluster-03",
        template="another",
        artifact="another-artifact:1",
        stem="alias",
    )
    alias.unlink()
    alias.symlink_to(first)
    finding = next(
        f
        for f in run_check(
            repo.root, template_repo=_relocation_template(tmp_path)
        ).findings
        if f.rule == "PLACE-12"
    )
    assert "Whole ParameterSet transfer candidate." not in finding.hint


@pytest.mark.parametrize("owner", [False, True])
def test_relocation_accounts_for_secondary_artifact_roles(repo, tmp_path, owner):
    from envgene_linter.engine import run_check

    first = _env(repo, "cluster-01")
    _env(repo, "cluster-02")
    if owner:
        path = first
        origin = "another-artifact:1"
    else:
        path = _env(
            repo,
            "cluster-03",
            template="another",
            artifact="another-artifact:1",
            params={"SETTING": "different"},
        )
        origin = ARTIFACT
    definition = path.parent.parent / "env_definition.yml"
    doc = json.loads(definition.read_text())
    doc["envTemplate"]["bgNsArtifacts"] = {"origin": origin}
    definition.write_text(json.dumps(doc))
    finding = next(
        f
        for f in run_check(
            repo.root, template_repo=_relocation_template(tmp_path)
        ).findings
        if f.rule == "PLACE-12"
    )
    assert "Whole ParameterSet transfer candidate." not in finding.hint


@pytest.mark.parametrize(
    "location", ["base", "override", "other_template", "conditional"]
)
def test_existing_template_references_block_original_name_relocation(
    repo, tmp_path, location
):
    from envgene_linter.engine import run_check

    _env(repo, "cluster-01")
    _env(repo, "cluster-02")
    _env(repo, "cluster-03", target="cloud", stem="other", params={"LOCAL": "another"})
    source = _relocation_template(tmp_path)
    directory = source / "templates/env_templates"
    if location == "override":
        path = directory / "business.yml"
        doc = json.loads(path.read_text())
        doc["namespaces"][0]["template_override"] = {"deployParameterSets": ["params"]}
        path.write_text(json.dumps(doc))
    elif location == "conditional":
        (directory / "oss.yml.j2").write_text(
            'deployParameters: {}\n{% if enabled %}\ndeployParameterSets:\n  - "params"\n{% endif %}\n'
        )
    else:
        path = directory / ("oss.yml.j2" if location == "base" else "another.yml.j2")
        path.write_text(json.dumps({"deployParameterSets": ["params"]}))
    finding = next(
        f
        for f in run_check(repo.root, template_repo=source).findings
        if f.rule == "PLACE-12"
    )
    assert "Whole ParameterSet transfer candidate." not in finding.hint


def test_relocation_report_retains_each_complete_reference_list(repo, tmp_path):
    from envgene_linter.engine import run_check

    for cluster, references in (
        ("cluster-01", ["before", "params", "after"]),
        ("cluster-02", ["after", "params", "before"]),
    ):
        path = _env(repo, cluster)
        definition = path.parent.parent / "env_definition.yml"
        doc = json.loads(definition.read_text())
        doc["envTemplate"]["envSpecificParamsets"]["oss"] = references
        definition.write_text(json.dumps(doc))
        for ref in ("before", "after"):
            (path.parent / (ref + ".yml")).write_text(
                json.dumps({"name": ref, "parameters": {"LOCAL": cluster}})
            )
    finding = next(
        f
        for f in run_check(
            repo.root, template_repo=_relocation_template(tmp_path)
        ).findings
        if f.rule == "PLACE-12"
    )
    assert "Whole ParameterSet transfer candidate." in finding.hint
    assert '["before", "params", "after"]' in finding.hint
    assert '["after", "params", "before"]' in finding.hint
    assert "Environment Inventory YAML:" not in finding.hint
