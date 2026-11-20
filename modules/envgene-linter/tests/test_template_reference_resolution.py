import json

import pytest
from test_place12_merge import _env, _existing, _findings, _relocation_template

from envgene_linter.engine import run_check
from envgene_linter.parsing import parse_yaml
from envgene_linter.template_references import (
    UnresolvedReference,
    resolve_reference_text,
    unconditional_reference_prefix,
)
from envgene_linter.yamlio import LoadedYaml


def _context(repo, tmp_path, versions=("1", "1"), reference=None, existing=None):
    template = _relocation_template(tmp_path)
    for cluster, version in zip(("cluster-01", "cluster-02"), versions):
        _env(repo, cluster, params={"SETTING": "shared", "LOCAL": cluster})
        if version is not None:
            repo.passport(
                "passport",
                {"custom": {"RELEASE": version, "BASELINE": "dev"}},
                cluster=cluster,
            )
    ref = (
        reference or "release-{{ current_env.cloud_passport.custom.RELEASE }}-defaults"
    )
    source = template / "templates/env_templates/oss.yml.j2"
    source.write_text(
        f'deployParameterSets:\n  - "{ref}"\n'
        'profile:\n{% if current_env.cloud_passport.custom.BASELINE == "dev" %}\n'
        "  name: small\n{% else %}\n  name: large\n{% endif %}\n"
    )
    for version in set(versions) - {None}:
        _existing(
            template, f"release-{version}-defaults", {"SETTING": "template-value"}
        )
    if existing:
        _existing(template, existing)
    return template


@pytest.mark.parametrize("versions", [("1", "1"), ("1", "2")])
def test_available_passport_reference_paths_continue_the_recipe(
    repo, tmp_path, versions
):
    template = _context(repo, tmp_path, versions)
    hint = _findings(repo, template)[0].hint
    assert "Template relocation proposal not generated." not in hint
    assert "Create file:" in hint and "Instance repository changes:" in hint
    for version in set(versions):
        assert f"release-{version}-defaults" in hint
    assert "Resolved ParameterSet references:" in hint


def test_literal_bracket_keys_are_resolved_without_python_attribute_access(
    repo, tmp_path
):
    template = _context(
        repo,
        tmp_path,
        reference="release-{{ current_env['cloud_passport']['custom']['RELEASE'] }}-defaults",
    )
    hint = _findings(repo, template)[0].hint
    assert "Create file:" in hint and "release-1-defaults" in hint


@pytest.mark.parametrize(
    "reference",
    [
        "release-{{ current_env.cloud_passport.custom.RELEASE | lower }}-defaults",
        "release-{{ current_env.cloud_passport.custom.get('RELEASE') }}-defaults",
        "release-{{ lookup('env', 'VALUE') }}-defaults",
        "release-{{ current_env.__class__ }}-defaults",
        "release-{{ current_env.cloud_passport.custom.MISSING }}-defaults",
    ],
)
def test_unsupported_or_missing_expression_keeps_review(repo, tmp_path, reference):
    template = _context(repo, tmp_path, reference=reference)
    hint = _findings(repo, template)[0].hint
    assert "Template relocation proposal not generated." in hint
    assert "Unresolved reference:" in hint
    assert "Instance repository changes:" not in hint


def test_missing_context_for_one_participant_cannot_be_borrowed_from_another(
    repo, tmp_path
):
    template = _context(repo, tmp_path, versions=("1", None))
    hint = _findings(repo, template)[0].hint
    assert "Template relocation proposal not generated." in hint
    assert "cluster-02/env-01" in hint
    assert "Instance repository changes:" not in hint


@pytest.mark.parametrize("kind", ["missing", "duplicate", "unrendered"])
def test_resolved_dynamic_reference_requires_one_readable_local_target(
    repo, tmp_path, kind
):
    template = _context(repo, tmp_path)
    file = template / "templates/parameters/release-1-defaults.yml"
    if kind == "missing":
        file.unlink()
    elif kind == "duplicate":
        file.with_suffix(".json").write_bytes(file.read_bytes())
    else:
        file.write_text("{% if enabled %}\nparameters: {}\n{% endif %}\n")
    hint = _findings(repo, template)[0].hint
    assert "Template relocation proposal not generated." in hint
    assert "release-1-defaults" in hint
    assert "Instance repository changes:" not in hint


@pytest.mark.parametrize("version", ["../outside", "{{ other }}", "", ["1"]])
def test_nonliteral_or_unsafe_selector_values_do_not_make_file_references(
    repo, tmp_path, version
):
    template = _context(repo, tmp_path)
    passport = repo.root / "environments/cluster-01/cloud-passport/passport.yml"
    passport.write_text(json.dumps({"custom": {"RELEASE": version}}))
    hint = _findings(repo, template)[0].hint
    assert "Template relocation proposal not generated." in hint
    assert "Instance repository changes:" not in hint


@pytest.mark.parametrize(
    "body",
    [
        'deployParameterSets:\n  - "fixed"\n{% if enabled %}\n  - "extra"\n{% endif %}\n',
        "deployParameterSets: []\nprofile: {}\n{% if enabled %}\ndeployParameterSets: [extra]\n{% endif %}\n",
        'deployParameterSets: []\nprofile: {}\n{% include "other.yml" %}\n',
        "deployParameterSets: []\nprofile: {}\n{% if enabled %}\n{{ injected_yaml }}\n{% endif %}\n",
    ],
)
def test_control_flow_that_may_change_membership_still_blocks_the_recipe(
    repo, tmp_path, body
):
    template = _context(repo, tmp_path)
    (template / "templates/env_templates/oss.yml.j2").write_text(body)
    hint = _findings(repo, template)[0].hint
    assert "Template relocation proposal not generated." in hint
    assert "Instance repository changes:" not in hint


def test_existing_reference_resolved_for_every_participant_is_not_appended_again(
    repo, tmp_path
):
    template = _context(repo, tmp_path, existing="release-1-defaults")
    # Use the already selected reference as the generated-name merge target.
    for cluster in ("cluster-01", "cluster-02"):
        source = (
            repo.root / f"environments/{cluster}/env-01/Inventory/parameters/params.yml"
        )
        doc = json.loads(source.read_text())
        doc["name"] = "release-1-defaults"
        source.write_text(json.dumps(doc))
        source.rename(source.with_name("release-1-defaults.yml"))
        definition = source.parent.parent / "env_definition.yml"
        data = json.loads(definition.read_text())
        data["envTemplate"]["envSpecificParamsets"]["oss"] = ["release-1-defaults"]
        definition.write_text(json.dumps(data))
    hint = _findings(repo, template)[0].hint
    assert "Merge into file:" in hint
    assert "Descriptor YAML:" not in hint
    assert "Instance repository changes:" in hint


def test_reference_parser_recursion_limit_is_a_review_failure():
    reference = "{{" + "(" * 1200 + "current_env.name" + ")" * 1200 + "}}"
    with pytest.raises(UnresolvedReference):
        resolve_reference_text(reference, {"current_env": {"name": "env-one"}})


def test_membership_parser_recursion_limit_is_unknown(tmp_path):
    prefix = "deployParameterSets: []\nprofile:\n"
    text = (
        prefix
        + "{% if "
        + "(" * 1200
        + "enabled"
        + ")" * 1200
        + " %}\n  name: small\n{% endif %}\n"
    )
    loaded = LoadedYaml(tmp_path / "source.j2", parse_yaml(prefix))
    assert not unconditional_reference_prefix(loaded, text, "deployParameterSets")


@pytest.mark.parametrize("value", [None, True, {}, ["1"], ""])
def test_selector_container_or_empty_values_are_not_stringified(value):
    with pytest.raises(UnresolvedReference):
        resolve_reference_text(
            "release-{{ current_env.cloud_passport.custom.RELEASE }}",
            {"current_env": {"cloud_passport": {"custom": {"RELEASE": value}}}},
        )


def test_protected_selector_paths_are_rejected_without_disclosing_the_value():
    with pytest.raises(UnresolvedReference) as error:
        resolve_reference_text(
            "release-{{ current_env.cloud_passport.custom.API_TOKEN }}",
            {
                "current_env": {
                    "cloud_passport": {"custom": {"API_TOKEN": "private-existing"}}
                }
            },
        )
    assert "private-existing" not in str(error.value)


def test_resolving_context_does_not_change_candidate_evidence(repo, tmp_path):
    template = _context(repo, tmp_path)
    ordinary = [f for f in run_check(repo.root).findings if f.rule == "PLACE-12"]
    resolved = _findings(repo, template)
    assert [(f.message, f.locations, f.action) for f in ordinary] == [
        (f.message, f.locations, f.action) for f in resolved
    ]


@pytest.mark.parametrize(
    "tail",
    [
        "{% if enabled %}deployParameterSets: [extra]\n{% endif %}\n",
        '{% if enabled %}"deploy\\u0050arameterSets": [extra]\n{% endif %}\n',
        "{% if enabled %}\n? deployParameterSets\n: [extra]\n{% endif %}\n",
        "{% if enabled %}\ndeployParameter{# hidden boundary #}Sets: [extra]\n{% endif %}\n",
        "deployParameter\n{%- if enabled -%}\nSets: [extra]\n{%- endif %}\n",
    ],
)
def test_control_flow_cannot_hide_redefined_keys_at_output_boundaries(
    repo, tmp_path, tail
):
    template = _context(repo, tmp_path)
    source = template / "templates/env_templates/oss.yml.j2"
    source.write_text("deployParameterSets: []\nprofile: {}\n" + tail)
    hint = _findings(repo, template)[0].hint
    assert "Template relocation proposal not generated." in hint
    assert "Instance repository changes:" not in hint


@pytest.mark.parametrize("boolean", ["true", "false"])
def test_anchored_yaml_boolean_is_not_a_numeric_release(repo, tmp_path, boolean):
    template = _context(repo, tmp_path)
    _existing(template, "release-0-defaults")
    passport = repo.root / "environments/cluster-01/cloud-passport/passport.yml"
    passport.write_text(f"custom:\n  RELEASE: &release {boolean}\n")
    hint = _findings(repo, template)[0].hint
    assert "Template relocation proposal not generated." in hint
    assert "Instance repository changes:" not in hint


def test_tagged_inventory_cannot_supply_an_environment_name_selector(repo, tmp_path):
    template = _context(
        repo, tmp_path, reference="release-{{ current_env.environmentName }}-defaults"
    )
    definition = (
        repo.root / "environments/cluster-01/env-01/Inventory/env_definition.yml"
    )
    doc = json.loads(definition.read_text())
    definition.write_text(
        'inventory: !custom\n  environmentName: "1"\n'
        + "envTemplate: "
        + json.dumps(doc["envTemplate"])
        + "\n"
    )
    other = repo.root / "environments/cluster-02/env-01/Inventory/env_definition.yml"
    other_doc = json.loads(other.read_text())
    other_doc["inventory"]["environmentName"] = "1"
    other.write_text(json.dumps(other_doc))
    hint = _findings(repo, template)[0].hint
    assert "Template relocation proposal not generated." in hint
    assert "Instance repository changes:" not in hint


def test_mixed_existing_reference_membership_cannot_authorize_one_shared_append(
    repo, tmp_path
):
    template = _context(
        repo,
        tmp_path,
        reference="{{ current_env.cloud_passport.custom.SELECTOR }}",
        existing="oss-common-deploy",
    )
    _existing(template, "other-defaults")
    for cluster, selector in (
        ("cluster-01", "oss-common-deploy"),
        ("cluster-02", "other-defaults"),
    ):
        passport = repo.root / f"environments/{cluster}/cloud-passport/passport.yml"
        passport.write_text(json.dumps({"custom": {"SELECTOR": selector}}))
    hint = _findings(repo, template)[0].hint
    assert "already selected in only some" in hint
    assert "Descriptor YAML:" not in hint and "Instance repository changes:" not in hint


def test_emitted_key_depth_is_relative_to_the_yaml_root_indent(repo, tmp_path):
    template = _context(repo, tmp_path)
    source = template / "templates/env_templates/oss.yml.j2"
    source.write_text(
        "  deployParameterSets: []\n  profile: {}\n"
        '{% if enabled %}\n  "deploy\\u0050arameterSets": [extra]\n{% endif %}\n'
    )
    hint = _findings(repo, template)[0].hint
    assert "Template relocation proposal not generated." in hint
    assert "Instance repository changes:" not in hint
