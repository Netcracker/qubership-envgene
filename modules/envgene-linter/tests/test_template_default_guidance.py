from datetime import date, datetime

import pytest
from ruamel.yaml import YAML
from ruamel.yaml.scalarbool import ScalarBoolean

from envgene_linter.model import Category, Scope
from envgene_linter.template_default_guidance import (
    assign_shared_name,
    build_template_default_hint,
    parameter_set_base,
    render_review_suggestion,
)


def _observed(hint):
    if "ParameterSet YAML:\n" in hint:
        snippet = hint.split("ParameterSet YAML:\n", 1)[1].split("\n\n", 1)[0]
    else:
        snippet = hint.split('":\n\n', 1)[1].split("\n\n2. ", 1)[0]
    return YAML(typ="safe").load(snippet)


@pytest.fixture
def local_templates(tmp_path):
    from envgene_linter.template_context import TemplateContext

    root = tmp_path / "source"
    descriptors = root / "templates/env_templates"
    descriptors.mkdir(parents=True)
    (descriptors / "business.yaml").write_text(
        'cloud: "{{ templates_dir }}/env_templates/cloud.yml"\n'
        "namespaces:\n"
        '  - template_path: "{{ templates_dir }}/env_templates/oss.yml"\n'
        "    deploy_postfix: oss\n"
    )
    for name in ("cloud", "oss"):
        (descriptors / f"{name}.yml").write_text(
            "deployParameterSets: []\ne2eParameterSets: []\ntechnicalConfigurationParameterSets: []\n"
        )
    return TemplateContext(root)


@pytest.mark.parametrize(
    "scope, binding",
    [
        (Scope("cloud", Category.DEPLOY), "deployParameterSets"),
        (Scope("cloud", Category.E2E), "e2eParameterSets"),
        (Scope("cloud", Category.TECHNICAL), "technicalConfigurationParameterSets"),
        (Scope("oss", Category.DEPLOY), "deployParameterSets"),
        (Scope("oss", Category.E2E), "e2eParameterSets"),
        (Scope("oss", Category.TECHNICAL), "technicalConfigurationParameterSets"),
        (Scope("oss", Category.DEPLOY, "app-one"), "deployParameterSets"),
        (
            Scope("oss", Category.TECHNICAL, "app-one"),
            "technicalConfigurationParameterSets",
        ),
        (Scope("oss", Category.E2E, "app-one"), None),
    ],
)
def test_no_context_explains_what_how_and_where_without_destination_paths(
    scope, binding
):
    hint = build_template_default_hint(
        "business",
        "templates:1",
        scope,
        [
            (("ATP_PARAMS_FILE", "branch"), "main"),
            (("ATP_PARAMS_FILE.branch",), "literal"),
            (("OPTIONS",), {"nested": ["line one\nline two"]}),
        ],
    )
    payload = _observed(hint)
    token = {
        Category.DEPLOY: "deploy",
        Category.E2E: "pipeline",
        Category.TECHNICAL: "runtime",
    }[scope.category]
    parts = ["business", scope.target]
    if scope.application:
        parts.append("app-one")
    parts.append(token)
    expected_name = "-".join(parts) + "-shared"
    assert payload["name"] == expected_name
    expected = {
        "ATP_PARAMS_FILE": {"branch": "main"},
        "ATP_PARAMS_FILE.branch": "literal",
        "OPTIONS": {"nested": ["line one\nline two"]},
    }
    if scope.application is None:
        assert payload["parameters"] == expected
    else:
        assert payload["applications"] == [
            {"appName": "app-one", "parameters": expected}
        ]
    assert "REVIEW ONLY. Nothing is applied automatically." in hint
    assert f'create ParameterSet "{expected_name}"' in hint
    assert "release a new version of templates:1" in hint
    assert "envgene-linter check -i <instance> -t <template>." in hint
    for concrete in (
        "Descriptor YAML:",
        "templates/parameters/",
        "Create file:",
        "Edit file:",
        "namespaces[0]",
        "Local descriptor:",
    ):
        assert concrete not in hint
    if binding is None:
        assert "no e2eParameters field" in hint
        assert "to the end of" not in hint
    else:
        where = (
            f"cloud.template_override.{binding} (Cloud)"
            if scope.target == "cloud"
            else f'namespaces[oss].template_override.{binding} (Namespace "oss")'
        )
        assert f'in "business", add "{expected_name}" to the end of {where}.' in hint
        assert "delete the same 3 keys from the files listed above" in hint


def test_context_yaml_preserves_nested_paths_and_literal_dotted_keys(local_templates):
    hint = build_template_default_hint(
        "business",
        "templates:1",
        Scope("cloud", Category.E2E),
        [
            (("ATP_PARAMS_FILE", "branch"), "main"),
            (("ATP_PARAMS_FILE.branch",), "literal"),
        ],
        context=local_templates,
    )
    assert _observed(hint)["parameters"] == {
        "ATP_PARAMS_FILE": {"branch": "main"},
        "ATP_PARAMS_FILE.branch": "literal",
    }


@pytest.mark.parametrize(
    "value",
    [
        "true",
        True,
        1,
        1.0,
        "on",
        "2026-01-01",
        "line one\nline two",
        '</pre><script>alert("example")</script>',
        ["true", True, 1, 1.0, {"option": "off"}],
        date(2026, 1, 1),
        datetime(2026, 1, 1, 12, 30),
        b"example",
        ScalarBoolean(1),
    ],
)
@pytest.mark.parametrize("with_context", [False, True])
def test_grouped_yaml_preserves_actual_value_and_scalar_type(
    value, local_templates, with_context
):
    hint = build_template_default_hint(
        "business",
        "templates:1",
        Scope("oss", Category.DEPLOY),
        [(("SETTING",), value)],
        context=local_templates if with_context else None,
    )
    actual = _observed(hint)["parameters"]["SETTING"]
    assert actual == value
    assert type(actual) is (bool if isinstance(value, ScalarBoolean) else type(value))
    if isinstance(actual, list):
        assert [type(item) for item in actual[:4]] == [str, bool, int, float]


@pytest.mark.parametrize("category", list(Category))
def test_application_observations_keep_the_application_container(
    category, local_templates
):
    hint = build_template_default_hint(
        "business",
        "templates:1",
        Scope("oss", category, "app-one"),
        [(("SETTING",), "value")],
        context=local_templates,
    )
    assert _observed(hint)["applications"] == [
        {"appName": "app-one", "parameters": {"SETTING": "value"}}
    ]
    if category is Category.E2E:
        assert "no e2eParameters field" in hint
        assert "Descriptor YAML:" not in hint


@pytest.mark.parametrize(
    "target, category, binding, stem",
    [
        ("cloud", Category.E2E, "e2eParameterSets", "cloud-common-pipeline"),
        ("oss", Category.DEPLOY, "deployParameterSets", "oss-common-deploy"),
        (
            "oss",
            Category.TECHNICAL,
            "technicalConfigurationParameterSets",
            "oss-common-runtime",
        ),
    ],
)
def test_local_recipe_identifies_where_to_append_the_shared_reference(
    tmp_path, target, category, binding, stem
):
    import json

    from envgene_linter.template_context import TemplateContext

    root = tmp_path / "source/templates/env_templates"
    root.mkdir(parents=True)
    entry = {
        "template_path": f"{{{{ templates_dir }}}}/env_templates/{target}.yml",
        "template_override": {binding: ["first-existing", "second-existing"]},
    }
    descriptor = (
        {"cloud": entry}
        if target == "cloud"
        else {"namespaces": [dict(entry, deploy_postfix="oss")]}
    )
    (root / "business.yaml").write_text(json.dumps(descriptor))
    (root / f"{target}.yml").write_text(json.dumps({binding: ["base-defaults"]}))
    hint = build_template_default_hint(
        "business",
        "templates:1",
        Scope(target, category),
        [
            (("FIRST",), "shared"),
            (("SECOND",), True),
        ],
        context=TemplateContext(root.parent.parent),
    )
    assert f"1. Create file: {root.parent / 'parameters' / (stem + '.yml')}" in hint
    assert _observed(hint) == {
        "name": stem,
        "parameters": {"FIRST": "shared", "SECOND": True},
    }
    assert f"2. Edit file: {root / 'business.yaml'}:" in hint
    selector = "cloud" if target == "cloud" else "namespaces[0]"
    assert f"YAML path: {selector}.template_override.{binding}" in hint
    location = (
        "existing cloud entry"
        if target == "cloud"
        else 'existing namespaces entry for "oss"'
    )
    assert location in hint
    assert f'Append "{stem}" as the last item in template_override.{binding}.' in hint
    assert "Environment-specific ParameterSets are applied afterwards and keep priority." not in hint
    fragment = YAML(typ="safe").load(
        hint.split("Descriptor YAML:\n", 1)[1].split("\n\n", 1)[0]
    )
    selected = fragment["cloud"] if target == "cloud" else fragment["namespaces"][0]
    assert selected["template_override"][binding] == [
        "first-existing",
        "second-existing",
        stem,
    ]
    assert "Descriptor YAML:" in hint and "template_path:" in hint
    assert "Local source comparison only:" not in hint
    assert hint.count("ParameterSet YAML:") == 1


@pytest.mark.parametrize("templates_directory", [False, True])
@pytest.mark.parametrize("shape", ["cloud-string", "cloud-object", "namespace"])
def test_template_actions_identify_the_selected_entry_and_preserve_existing_lists(
    tmp_path, templates_directory, shape
):
    from envgene_linter.template_context import TemplateContext

    root = tmp_path / "template with spaces \u0438 Unicode"
    descriptors = root / "templates/env_templates"
    descriptors.mkdir(parents=True)
    target = "oss" if shape == "namespace" else "cloud"
    if shape == "cloud-string":
        text = '# Descriptor\ncloud: "{{ templates_dir }}/env_templates/cloud.yml"\n'
        position, selector, previous = (2, 1), "cloud", []
    elif shape == "cloud-object":
        text = (
            "# Descriptor\ncloud:\n"
            '  template_path: "{{ templates_dir }}/env_templates/cloud.yml"\n'
            "  template_override:\n"
            "    deployParameterSets:\n      - previous\n"
            "    e2eParameterSets:\n      - unrelated\n"
        )
        position, selector, previous = (2, 1), "cloud", ["previous"]
    else:
        text = (
            "# Descriptor\nnamespaces:\n"
            '  - template_path: "{{ templates_dir }}/env_templates/other.yml"\n'
            "    deploy_postfix: other\n"
            "    template_override:\n"
            "      deployParameterSets:\n        - keep-other\n"
            '  - template_path: "{{ templates_dir }}/env_templates/oss.yml"\n'
            "    deploy_postfix: oss\n"
            "    template_override:\n"
            "      deployParameterSets:\n        - previous\n"
            "      e2eParameterSets:\n        - unrelated\n"
        )
        position, selector, previous = (8, 5), "namespaces[1]", ["previous"]
    descriptor = descriptors / "business.yaml"
    descriptor.write_text(text)
    renderer = descriptors / f"{target}.yml"
    renderer.write_text("deployParameterSets: []\n")
    originals = {path: path.read_bytes() for path in (descriptor, renderer)}
    selected = root / "templates" if templates_directory else root
    hint = build_template_default_hint(
        "business",
        "templates:1",
        Scope(target, Category.DEPLOY),
        [(("SETTING",), "shared")],
        context=TemplateContext(selected),
    )

    stem = f"{target}-common-deploy"
    assert "Template repository changes:\n" in hint
    assert f"Create file: {root / 'templates/parameters' / (stem + '.yml')}\n" in hint
    assert f"Edit file: {descriptor}:{position[0]}:{position[1]}\n" in hint
    assert f"YAML path: {selector}.template_override.deployParameterSets\n" in hint
    assert "Merge the shown fields into this entry." in hint
    assert "Preserve other descriptor entries and override fields." in hint
    fragment = YAML(typ="safe").load(
        hint.split("Descriptor YAML:\n", 1)[1].split("\n\n", 1)[0]
    )
    entry = fragment["namespaces"][0] if shape == "namespace" else fragment["cloud"]
    assert entry["template_override"]["deployParameterSets"] == [*previous, stem]
    assert "e2eParameterSets" not in entry["template_override"]
    assert all(path.read_bytes() == contents for path, contents in originals.items())


def test_unresolved_template_reports_its_absolute_descriptor_without_inventing_edits(
    tmp_path,
):
    from envgene_linter.template_context import TemplateContext

    root = tmp_path / "source"
    descriptor = root / "templates/env_templates/business.yaml"
    descriptor.parent.mkdir(parents=True)
    descriptor.write_text('cloud: "{{ external_directory }}/cloud.yml"\n')
    hint = build_template_default_hint(
        "business",
        "templates:1",
        Scope("cloud", Category.DEPLOY),
        [(("SETTING",), "shared")],
        context=TemplateContext(root),
    )

    assert f"Local descriptor: {descriptor}.\n" in hint
    assert "dynamic or outside" in hint
    assert "Create file:" not in hint and "Edit file:" not in hint


@pytest.mark.parametrize(
    "shape, target, selector",
    [
        ("namespace-alias", "oss", "namespaces[1]"),
        ("cloud-alias", "cloud", "cloud"),
        ("inherited-cloud", "cloud", "cloud"),
        ("inherited-namespaces", "oss", "namespaces[0]"),
    ],
)
def test_aliases_and_inherited_entry_locations_do_not_suggest_an_anchor_edit(
    tmp_path, shape, target, selector
):
    from envgene_linter.template_context import TemplateContext

    root = tmp_path / "source"
    descriptors = root / "templates/env_templates"
    descriptors.mkdir(parents=True)
    if shape == "namespace-alias":
        text = (
            "tenant: tenant.yml\ncloud: cloud.yml\nshared: &base\n"
            '  template_path: "{{ templates_dir }}/env_templates/oss.yml"\n'
            "  deploy_postfix: oss\n"
            "namespaces:\n  - <<: *base\n    deploy_postfix: other\n  - *base\n"
        )
    elif shape == "cloud-alias":
        text = (
            "shared: &base\n"
            '  template_path: "{{ templates_dir }}/env_templates/cloud.yml"\n'
            "cloud: *base\n"
        )
    elif shape == "inherited-cloud":
        text = (
            "shared: &base\n"
            '  cloud: "{{ templates_dir }}/env_templates/cloud.yml"\n'
            "<<: *base\n"
        )
    else:
        text = (
            "shared: &base\n  namespaces:\n"
            '    - template_path: "{{ templates_dir }}/env_templates/oss.yml"\n'
            "      deploy_postfix: oss\n"
            "<<: *base\n"
        )
    descriptor = descriptors / "business.yaml"
    descriptor.write_text(text)
    (descriptors / f"{target}.yml").write_text("deployParameterSets: []\n")
    hint = build_template_default_hint(
        "business",
        "templates:1",
        Scope(target, Category.DEPLOY),
        [(("SETTING",), "shared")],
        context=TemplateContext(root),
    )

    assert f"Local descriptor: {descriptor}.\n" in hint
    assert f"YAML entry: {selector}\n" in hint
    assert "anchors or inherited keys" in hint
    assert "Create file:" not in hint and "Edit file:" not in hint
    assert descriptor.read_text() == text


def test_shared_names_follow_template_subject_and_repeated_groups_use_the_first_key():
    template = "sample-template"
    cloud = Scope("cloud", Category.DEPLOY)
    env_files = (
        ("cluster-01/env-01", "cluster-01-env-01-cloud-deploy"),
        ("cluster-01/env-02", "cluster-01-env-02-cloud-deploy"),
    )
    cloud_base = parameter_set_base(template, cloud, env_files)
    assert cloud_base == "sample-template-cloud-deploy"
    assert (
        assign_shared_name(cloud_base, ["SERVICE_URL"], disambiguate=False, used=set())
        == "sample-template-cloud-deploy-shared"
    )

    app = parameter_set_base(
        template,
        Scope("cloud", Category.DEPLOY, "app-one"),
        (("cluster-01/env-01", "catalog-1.2"), ("cluster-01/env-02", "catalog-1.2")),
    )
    assert app == "sample-template-cloud-catalog-1.2-app-one"

    pipeline = parameter_set_base(
        template,
        Scope("cloud", Category.E2E),
        (
            ("cluster-01/env-01", "delivery-pipeline"),
            ("cluster-01/env-02", "delivery-pipeline"),
        ),
    )
    assert pipeline == "sample-template-cloud-delivery-pipeline"

    namespace = Scope("oss", Category.DEPLOY)
    repeated = (
        ("cluster-01/env-01", "cluster-01-env-01-oss-deploy"),
        ("cluster-01/env-02", "cluster-01-env-02-oss-deploy"),
    )
    base = parameter_set_base(template, namespace, repeated)
    used = set()
    assert (
        assign_shared_name(base, ["FIRST_SETTING"], disambiguate=True, used=used)
        == "sample-template-oss-deploy-first-setting-shared"
    )
    assert (
        assign_shared_name(
            base, ["option.defaultFlag.enabled"], disambiguate=True, used=used
        )
        == "sample-template-oss-deploy-option.defaultflag.enabled-shared"
    )

    hint = render_review_suggestion(
        template,
        "sample-templates",
        namespace,
        [(("ALPHA_FLAG",), "true"), (("job.enabled",), "false")],
        "sample-template-oss-deploy-alpha-flag-shared",
        keys=["ALPHA_FLAG", "job.enabled"],
        agreed=7,
        exception_lines=(
            "cluster-01/env-03: ALPHA_FLAG is absent",
            "cluster-01/env-03: job.enabled is absent",
        ),
    )
    assert "REVIEW ONLY. Nothing is applied automatically." in hint
    assert "Look twice at:" not in hint
    assert 'create ParameterSet "sample-template-oss-deploy-alpha-flag-shared"' in hint
    assert (
        "to the end of namespaces[oss].template_override.deployParameterSets "
        '(Namespace "oss").'
    ) in hint
    assert "update the 7 environments to it." in hint
    assert "delete the same 2 keys from the files listed above." in hint
    assert "   Keep as they are:\n   - cluster-01/env-03: ALPHA_FLAG is absent" in hint
    assert "envgene-linter check -i <instance> -t <template>." in hint

    cautious = render_review_suggestion(
        template,
        "sample-templates",
        cloud,
        [(("SERVICE_URL",), "https://example.invalid"), (("RUN_MODE",), "local")],
        "sample-template-cloud-deploy-shared",
        keys=["SERVICE_URL", "RUN_MODE"],
        agreed=8,
    )
    assert "Look twice at: SERVICE_URL" in cautious
    assert "RUN_MODE" not in cautious.split("Look twice at: ", 1)[1].split("\n", 1)[0]
