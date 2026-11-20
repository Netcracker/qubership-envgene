import pytest
from test_place12_merge import _env, _findings, _relocation_template


@pytest.mark.parametrize(
    "category,field",
    [
        ("deploy", "deployParameterSets"),
        ("e2e", "e2eParameterSets"),
        ("technical", "technicalConfigurationParameterSets"),
    ],
)
def test_unresolved_reference_explains_missing_proposal_and_exact_source(
    repo, tmp_path, category, field
):
    for cluster in ("cluster-01", "cluster-02"):
        _env(repo, cluster, category=category)
    template = _relocation_template(tmp_path)
    source = template / "templates/env_templates/oss.yml.j2"
    reference = "release-{{ current_env.cloud_passport.custom.RELEASE }}-defaults"
    source.write_text(f'{field}:\n  - "{reference}"\n')

    hint = _findings(repo, template)[0].hint

    assert "Template relocation proposal not generated." in hint
    assert f"{source}:2:5" in hint
    assert reference in hint
    assert field in hint
    assert (
        "Resolve the referenced ParameterSets for every participating environment"
        in hint
    )
    assert "Create file:" not in hint and "Instance repository changes:" not in hint


def test_jinja_control_flow_blocker_points_to_statement_without_dumping_values(
    repo, tmp_path
):
    for cluster in ("cluster-01", "cluster-02"):
        _env(repo, cluster)
    template = _relocation_template(tmp_path)
    source = template / "templates/env_templates/oss.yml.j2"
    source.write_text(
        "deployParameterSets: []\n"
        '{% if mode == "private-condition-value" %}\n'
        "profile: {name: small}\n{% endif %}\n"
    )

    hint = _findings(repo, template)[0].hint

    assert "Template relocation proposal not generated." in hint
    assert f"{source}:2:1" in hint
    assert "Jinja control flow has not been evaluated" in hint
    assert "private-condition-value" not in hint
    assert "Instance repository changes:" not in hint


def test_descriptor_override_dynamic_reference_has_descriptor_coordinates(
    repo, tmp_path
):
    import json

    for cluster in ("cluster-01", "cluster-02"):
        _env(repo, cluster)
    template = _relocation_template(tmp_path)
    descriptor = template / "templates/env_templates/business.yml"
    value = json.loads(descriptor.read_text())
    reference = "release-{{ version }}-defaults"
    value["namespaces"][0]["template_override"] = {"deployParameterSets": [reference]}
    descriptor.write_text(json.dumps(value, indent=2))

    hint = _findings(repo, template)[0].hint

    assert "Template relocation proposal not generated." in hint
    assert f"Unresolved reference: {descriptor}:" in hint
    assert reference in hint
    assert "Instance repository changes:" not in hint
