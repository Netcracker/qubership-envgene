import json

import pytest
from ruamel.yaml import YAML
from test_place12 import _env, _relocation_template

from envgene_linter.engine import run_check

REMOVED = (
    "Later ParameterSets override earlier values.",
    "Environment-specific ParameterSets are applied afterwards and keep priority.",
    "Review before removing matching instance entries. Keep their existing ParameterSet references for other overrides.",
    "Local source comparison only: artifact equivalence, Jinja output, and all template consumers remain unverified.",
)


def _findings(repo, template=None):
    return [
        f
        for f in run_check(repo.root, template_repo=template).findings
        if f.rule == "PLACE-12"
    ]


def _existing(template, name="params", parameters=None, suffix=".yml", **extra):
    file = template / "templates/parameters" / (name + suffix)
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(
        json.dumps(
            {
                "name": name,
                "parameters": parameters or {},
                **extra,
            }
        )
    )
    return file


def _yaml(hint):
    if "ParameterSet JSON:\n" in hint:
        return json.loads(hint.split("ParameterSet JSON:\n", 1)[1].split("\n\n", 1)[0])
    return YAML(typ="safe").load(
        hint.split("ParameterSet YAML:\n", 1)[1].split("\n\n", 1)[0]
    )


@pytest.mark.parametrize("with_template", [False, True])
@pytest.mark.parametrize("application", [None, "app-one"])
def test_cleanup_identifies_exact_source_paths(
    repo, tmp_path, with_template, application
):
    sources = [
        _env(
            repo,
            cluster,
            params={
                "NESTED": {"common": "shared"},
                "NESTED.common": "literal",
                "LOCAL": cluster,
            },
            application=application,
        )
        for cluster in ("cluster-01", "cluster-02")
    ]
    template = _relocation_template(tmp_path) if with_template else None
    hint = _findings(repo, template)[0].hint
    assert not any(text in hint for text in REMOVED)
    cleanup = hint.split("Instance repository changes:\n", 1)[1]
    assert "Publish" in cleanup and "verify generation" in cleanup
    prefix = 'applications[0]["parameters"]' if application else "parameters"
    for source in sources:
        assert str(source) + ":" in cleanup
    assert prefix + '["NESTED"]["common"]' in cleanup
    assert prefix + '["NESTED.common"]' in cleanup
    assert '["LOCAL"]' not in cleanup


@pytest.mark.parametrize("suffix", [".yml", ".yaml", ".json"])
def test_merge_existing_preserves_unrelated_data_and_original_bindings(
    repo, tmp_path, suffix
):
    sources = [
        _env(repo, c, params={"NEW": "shared", "LOCAL": c})
        for c in ("cluster-01", "cluster-02")
    ]
    template = _relocation_template(tmp_path)
    existing = _existing(
        template, parameters={"KEEP": "unrelated-private-value"}, suffix=suffix
    )
    before = {p: p.read_bytes() for p in [*sources, existing]}
    hint = _findings(repo, template)[0].hint
    assert f"Merge into file: {existing}" in hint
    assert _yaml(hint) == {"name": "params", "parameters": {"NEW": "shared"}}
    assert "unrelated-private-value" not in hint
    assert "Keep the existing Environment Inventory bindings" in hint
    assert "Descriptor YAML:" not in hint and "Create file:" not in hint
    assert all(p.read_bytes() == value for p, value in before.items())


@pytest.mark.parametrize(
    "old,new",
    [
        (30, 60),
        (True, 1),
        (1, 1.0),
        (1, "1"),
        (["a"], ["b"]),
        (["a", "b"], ["b", "a"]),
        ({"child": 1}, "scalar"),
        ("scalar", {"child": 1}),
    ],
)
def test_conflicts_keep_instance_entries_without_fallback_file(
    repo, tmp_path, old, new
):
    for c in ("cluster-01", "cluster-02"):
        _env(repo, c, params={"CONFLICT": new, "ADD": "shared", "LOCAL": c})
    template = _relocation_template(tmp_path)
    _existing(template, parameters={"CONFLICT": old})
    hint = _findings(repo, template)[0].hint
    assert "Conflict:" in hint and "Create file:" not in hint
    assert _yaml(hint)["parameters"] == {"ADD": "shared"}
    cleanup = hint.split("Instance repository changes:\n", 1)[1]
    assert '["ADD"]' in cleanup and '["CONFLICT"]' not in cleanup


def test_equal_values_are_reused_without_empty_merge_or_duplicate_reference(
    repo, tmp_path
):
    for c in ("cluster-01", "cluster-02"):
        _env(repo, c)
    template = _relocation_template(tmp_path)
    file = _existing(template, parameters={"SETTING": "shared-default-value"})
    hint = _findings(repo, template)[0].hint
    assert f"Reuse file: {file}" in hint
    assert "Merge into file:" not in hint and "Descriptor YAML:" not in hint
    assert 'parameters["SETTING"]' in hint.split("Instance repository changes:\n")[1]


def test_generated_name_is_reused_and_appended_once(repo, tmp_path):
    for c in ("cluster-01", "cluster-02"):
        _env(repo, c, params={"NEW": "shared", "LOCAL": c})
    template = _relocation_template(tmp_path)
    file = _existing(template, name="oss-common-deploy")
    hint = _findings(repo, template)[0].hint
    assert f"Merge into file: {file}" in hint
    fragment = YAML(typ="safe").load(
        hint.split("Descriptor YAML:\n")[1].split("\n\n")[0]
    )
    assert fragment["namespaces"][0]["template_override"]["deployParameterSets"] == [
        "oss-common-deploy"
    ]


@pytest.mark.parametrize("kind", ["duplicate", "wrong-name", "jinja", "invalid"])
def test_uncertain_existing_target_blocks_edits_and_cleanup(repo, tmp_path, kind):
    for c in ("cluster-01", "cluster-02"):
        _env(repo, c)
    template = _relocation_template(tmp_path)
    file = _existing(template)
    if kind == "duplicate":
        _existing(template, suffix=".json")
    elif kind == "wrong-name":
        file.write_text("name: other\nparameters: {}\n")
    elif kind == "jinja":
        file.rename(file.with_suffix(".yml.j2"))
    else:
        file.write_text("parameters: [invalid\n")
    hint = _findings(repo, template)[0].hint
    assert "Review:" in hint
    assert "Create file:" not in hint and "Merge into file:" not in hint
    assert "Instance repository changes:" not in hint


def test_cross_finding_conflict_invalidates_both_cleanups(repo, tmp_path):
    for template_name, value in (("business", "one"), ("other", "two")):
        for c in (template_name + "-a", template_name + "-b"):
            _env(repo, c, template=template_name, params={"SETTING": value})
    template = _relocation_template(tmp_path)
    descriptor = template / "templates/env_templates/business.yml"
    descriptor.with_name("other.yml").write_bytes(descriptor.read_bytes())
    _existing(template)
    results = _findings(repo, template)
    assert len(results) == 2
    for finding in results:
        assert "Conflict:" in finding.hint
        assert "Merge into file:" not in finding.hint
        assert "Instance repository changes:" not in finding.hint


@pytest.mark.parametrize("application", ["app-one", "app-two"])
def test_application_merge_matches_identity_and_preserves_other_applications(
    repo, tmp_path, application
):
    for c in ("cluster-01", "cluster-02"):
        _env(repo, c, params={"NEW": "shared"}, application=application)
    template = _relocation_template(tmp_path)
    _existing(
        template,
        applications=[
            {"appName": "app-one", "parameters": {"KEEP": "private-existing"}},
        ],
    )
    hint = _findings(repo, template)[0].hint
    assert _yaml(hint)["applications"] == [
        {"appName": application, "parameters": {"NEW": "shared"}}
    ]
    assert "private-existing" not in hint
    assert 'applications[0]["parameters"]["NEW"]' in hint
    assert "Keep other applications" in hint


@pytest.mark.parametrize("where", ["base", "override"])
def test_existing_generated_reference_is_not_appended_again(repo, tmp_path, where):
    for c in ("cluster-01", "cluster-02"):
        _env(repo, c, params={"NEW": "shared", "LOCAL": c})
    template = _relocation_template(tmp_path)
    _existing(template, name="oss-common-deploy")
    if where == "base":
        file = template / "templates/env_templates/oss.yml.j2"
        doc = json.loads(file.read_text())
        doc["deployParameterSets"] = ["first", "oss-common-deploy", "last"]
    else:
        file = template / "templates/env_templates/business.yml"
        doc = json.loads(file.read_text())
        doc["namespaces"][0]["template_override"] = {
            "deployParameterSets": ["first", "oss-common-deploy", "last"]
        }
    file.write_text(json.dumps(doc))
    hint = _findings(repo, template)[0].hint
    assert "current position" in hint and "Descriptor YAML:" not in hint


def test_same_name_has_priority_and_other_names_are_not_selected(repo, tmp_path):
    for c in ("cluster-01", "cluster-02"):
        _env(repo, c, params={"NEW": "shared", "LOCAL": c})
    template = _relocation_template(tmp_path)
    original = _existing(template)
    other = _existing(template, name="oss-common-deploy")
    hint = _findings(repo, template)[0].hint
    assert f"Merge into file: {original}" in hint
    assert f"Merge into file: {other}" not in hint
    original.unlink()
    other.rename(other.with_name("unrelated.yml"))
    hint = _findings(repo, template)[0].hint
    assert "Create file:" in hint and "Merge into file:" not in hint


def test_conflicts_only_do_not_render_empty_yaml_or_cleanup(repo, tmp_path):
    for c in ("cluster-01", "cluster-02"):
        _env(repo, c)
    template = _relocation_template(tmp_path)
    _existing(template, parameters={"SETTING": "different"})
    hint = _findings(repo, template)[0].hint
    assert "Conflict:" in hint
    assert (
        "ParameterSet YAML:" not in hint and "Instance repository changes:" not in hint
    )


@pytest.mark.parametrize(
    "invalid",
    [
        "name: params\nparameters: {}\n",  # YAML is not valid JSON.
        '{"name":"params","parameters":{},"applications":null}',
        '{"name":"params","parameters":{},"applications":[{"appName":"a","parameters":{}},{"appName":"a","parameters":{}}]}',
    ],
)
def test_invalid_existing_json_is_not_a_merge_target(repo, tmp_path, invalid):
    for c in ("cluster-01", "cluster-02"):
        _env(repo, c)
    template = _relocation_template(tmp_path)
    file = _existing(template, suffix=".json")
    file.write_text(invalid)
    hint = _findings(repo, template)[0].hint
    assert "Review:" in hint and "Merge into file:" not in hint
    assert "Instance repository changes:" not in hint


def test_cross_finding_parent_child_conflict_is_blocked(repo, tmp_path):
    for template_name, value in (("business", "one"), ("other", {"child": "two"})):
        for c in (template_name + "-a", template_name + "-b"):
            _env(repo, c, template=template_name, params={"SETTING": value})
    template = _relocation_template(tmp_path)
    descriptor = template / "templates/env_templates/business.yml"
    descriptor.with_name("other.yml").write_bytes(descriptor.read_bytes())
    _existing(template)
    for finding in _findings(repo, template):
        assert "Conflict:" in finding.hint
        assert "Instance repository changes:" not in finding.hint


def test_cleanup_does_not_remove_a_shared_source_used_by_another_template(
    repo, tmp_path
):
    for c in ("cluster-01", "cluster-02"):
        _env(repo, c, layer="cluster")
        _env(repo, c, name="other-env", template="other", layer="cluster")
    template = _relocation_template(tmp_path)
    hint = _findings(repo, template)[0].hint
    assert "Cleanup Review:" in hint
    assert "Remove YAML path:" not in hint


def test_json_merge_instructions_are_copyable_json(repo, tmp_path):
    for c in ("cluster-01", "cluster-02"):
        _env(repo, c, params={"FLAG": True, "COUNT": 1, "TEXT": "1"})
    template = _relocation_template(tmp_path)
    _existing(template, suffix=".json")
    hint = _findings(repo, template)[0].hint
    assert "ParameterSet JSON:\n" in hint
    assert _yaml(hint)["parameters"] == {"FLAG": True, "COUNT": 1, "TEXT": "1"}


def test_json_merge_does_not_change_unrepresentable_yaml_value_types(repo, tmp_path):
    for c in ("cluster-01", "cluster-02"):
        file = _env(repo, c)
        file.write_text("name: params\nparameters:\n  SETTING: 2026-01-01\n")
    template = _relocation_template(tmp_path)
    _existing(template, suffix=".json")
    hint = _findings(repo, template)[0].hint
    assert "Conflict:" in hint
    assert "Merge into file:" not in hint and "Instance repository changes:" not in hint


@pytest.mark.parametrize(
    "parameters,applications",
    [
        ({"{{ key }}": "value"}, []),
        ({}, [{"appName": "{{ name }}", "parameters": {}}]),
        ({}, [{"appName": "", "parameters": {}}]),
    ],
)
def test_dynamic_membership_in_existing_paramset_blocks_cleanup(
    repo, tmp_path, parameters, applications
):
    for c in ("cluster-01", "cluster-02"):
        _env(repo, c)
    template = _relocation_template(tmp_path)
    _existing(template, parameters=parameters, applications=applications)
    hint = _findings(repo, template)[0].hint
    assert "Review:" in hint
    assert "Merge into file:" not in hint and "Instance repository changes:" not in hint


@pytest.mark.parametrize("with_template", [False, True])
def test_json_instance_cleanup_uses_exact_json_key_coordinates(
    repo, tmp_path, with_template
):
    sources = []
    for c in ("cluster-01", "cluster-02"):
        file = _env(repo, c, params={"SETTING": "shared", "LOCAL": c})
        text = json.dumps(json.loads(file.read_text()), indent=2)
        file.unlink()
        file = file.with_suffix(".json")
        file.write_text(text)
        sources.append(file)
    template = _relocation_template(tmp_path) if with_template else None
    hint = _findings(repo, template)[0].hint
    cleanup = hint.split("Instance repository changes:\n")[1]
    for file in sources:
        # The JSON key is on line 4, indented by four spaces.
        assert f"{file}:4:5" in cleanup
    assert 'parameters["SETTING"]' in cleanup
    assert "Cleanup Review:" not in hint


@pytest.mark.parametrize("existing", [False, True])
@pytest.mark.parametrize("dynamic", ["conditional", "reference"])
def test_unresolved_template_membership_never_authorizes_cleanup(
    repo, tmp_path, existing, dynamic
):
    for c in ("cluster-01", "cluster-02"):
        _env(repo, c, params={"NEW": "shared", "LOCAL": c})
    template = _relocation_template(tmp_path)
    if existing:
        _existing(template, name="oss-common-deploy")
    source = template / "templates/env_templates/oss.yml.j2"
    source.write_text(
        "deployParameters: {}\n{% if enabled %}\ndeployParameterSets:\n"
        '  - "oss-common-deploy"\n{% endif %}\n'
        if dynamic == "conditional"
        else 'deployParameterSets:\n  - "{{ selected_paramset }}"\n'
    )
    hint = _findings(repo, template)[0].hint
    assert "Instance repository changes:" not in hint
    assert "Create file:" not in hint and "Merge into file:" not in hint
    assert "membership" in hint


def test_whole_relocation_preserves_anchored_descriptor_when_no_edit_is_needed(
    repo, tmp_path
):
    for c in ("cluster-01", "cluster-02"):
        _env(repo, c)
    template = _relocation_template(tmp_path)
    descriptor = template / "templates/env_templates/business.yml"
    descriptor.write_text(
        "shared: &entry\n"
        '  template_path: "{{ templates_dir }}/env_templates/oss.yml.j2"\n'
        "  deploy_postfix: oss\nnamespaces:\n  - *entry\n"
    )
    hint = _findings(repo, template)[0].hint
    assert "Whole ParameterSet transfer candidate." in hint
    assert "Edit file:" not in hint
    assert "Instance repository changes:" in hint


def test_whole_relocation_with_dynamic_selected_membership_has_no_file_deletion(
    repo, tmp_path
):
    for c in ("cluster-01", "cluster-02"):
        _env(repo, c)
    template = _relocation_template(tmp_path)
    (template / "templates/env_templates/oss.yml.j2").write_text(
        'deployParameterSets:\n  - "{{ selected_paramset }}"\n'
    )
    hint = _findings(repo, template)[0].hint
    assert "membership" in hint
    assert "Instance repository changes:" not in hint
    assert "Whole ParameterSet transfer candidate." not in hint
