import json

import pytest

from envgene_linter.model import Category, Scope
from envgene_linter.template_context import TemplateContext


def _write(root, relative, value):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value if isinstance(value, str) else json.dumps(value))
    return path


def _template(tmp_path, **entry):
    root = tmp_path / "source"
    _write(
        root,
        "templates/env_templates/business.yaml",
        {
            "cloud": "{{ templates_dir }}/env_templates/cloud.yml.j2",
            "namespaces": [
                dict(
                    template_path="{{ templates_dir }}/env_templates/oss.yml.j2",
                    **entry,
                )
            ],
        },
    )
    _write(root, "templates/env_templates/cloud.yml.j2", {"e2eParameterSets": []})
    _write(
        root,
        "templates/env_templates/oss.yml.j2",
        {"deployParameterSets": ["product-defaults"]},
    )
    return root


def _proposal(context, scope=None, **kwargs):
    return context.propose(
        "business",
        "templates:1",
        scope or Scope("oss", Category.DEPLOY),
        [(("SETTING",), "shared")],
        **kwargs,
    )


def test_cloud_path_becomes_a_real_descriptor_entry(tmp_path):
    context = TemplateContext(_template(tmp_path))
    proposal = _proposal(context, Scope("cloud", Category.E2E))
    assert proposal.descriptor == "templates/env_templates/business.yaml"
    assert proposal.stem == "cloud-common-pipeline"
    assert proposal.attachment == {
        "cloud": {
            "template_path": "{{ templates_dir }}/env_templates/cloud.yml.j2",
            "template_override": {"e2eParameterSets": ["cloud-common-pipeline"]},
        }
    }
    assert proposal.reason is None


def test_namespace_uses_explicit_postfix_and_retains_existing_override_references(
    tmp_path,
):
    root = _template(
        tmp_path,
        deploy_postfix="payments",
        template_override={
            "deployParameterSets": ["project-defaults"],
            "profile": {"name": "small"},
        },
    )
    proposal = _proposal(TemplateContext(root), Scope("payments", Category.DEPLOY))
    entry = proposal.attachment["namespaces"][0]
    assert entry["deploy_postfix"] == "payments"
    assert entry["template_path"].endswith("/oss.yml.j2")
    assert entry["template_override"]["deployParameterSets"] == [
        "project-defaults",
        "payments-common-deploy",
    ]
    assert (
        "profile" not in entry["template_override"]
    )  # A merge fragment, not a replacement of unrelated fields.
    assert _proposal(TemplateContext(root)).attachment is None


def test_local_definitions_are_compared_only_in_selected_scope_and_category(tmp_path):
    root = _template(tmp_path)
    _write(
        root,
        "templates/parameters/nested/product-defaults.yml",
        {
            "name": "product-defaults",
            "parameters": {"SETTING": "different"},
            "applications": [
                {"appName": "worker", "parameters": {"SETTING": "shared"}}
            ],
        },
    )
    _write(
        root,
        "templates/parameters/unselected.yml",
        {"name": "unselected", "parameters": {"SETTING": "shared"}},
    )
    context = TemplateContext(root)
    proposal = _proposal(context)
    assert len(proposal.definitions) == 1
    assert "nested/product-defaults.yml:1:" in proposal.definitions[0]
    assert "different value" in proposal.definitions[0]
    assert "unselected" not in str(proposal.definitions)
    application = _proposal(context, Scope("oss", Category.DEPLOY, "worker"))
    assert "same value" in application.definitions[0]
    assert _proposal(context, Scope("oss", Category.E2E)).definitions == ()


def test_jinja_prefix_and_dynamic_reference_are_source_evidence_not_effective_defaults(
    tmp_path,
):
    root = _template(tmp_path)
    _write(
        root,
        "templates/env_templates/oss.yml.j2",
        """deployParameters:
  SETTING: "shared"
deployParameterSets:
  - "product-{{ release }}"
profile:
{% if small %}
  name: "small"
{% endif %}
""",
    )
    _write(
        root,
        "templates/parameters/product-v1.yml",
        {"name": "product-v1", "parameters": {"SETTING": "other"}},
    )
    proposal = _proposal(TemplateContext(root))
    assert proposal.attachment is not None
    assert len(proposal.definitions) == 2
    assert any(
        "oss.yml.j2:2:3" in line and "same value" in line
        for line in proposal.definitions
    )
    assert any(
        "dynamic reference" in line and "different value" in line
        for line in proposal.definitions
    )


def test_descriptor_extension_priority_matches_the_generator(tmp_path):
    root = _template(tmp_path)
    _write(
        root,
        "templates/env_templates/business.yml.j2",
        {"cloud": "{{ templates_dir }}/env_templates/cloud.yml.j2"},
    )
    proposal = _proposal(TemplateContext(root), Scope("cloud", Category.E2E))
    assert proposal.descriptor.endswith("business.yml.j2")


def test_names_respect_existing_files_references_and_distinct_normalized_scopes(
    tmp_path,
):
    root = _template(tmp_path)
    _write(
        root,
        "templates/parameters/deep/oss-common-deploy.yml",
        {"name": "oss-common-deploy", "parameters": {}},
    )
    context = TemplateContext(root)
    first = _proposal(
        context, identity=("first",), source_references=("oss-common-deploy-2",)
    )
    second = _proposal(context, identity=("second",))
    assert first.stem == "oss-common-deploy-3"
    assert second.stem == "oss-common-deploy-4"
    assert (
        _proposal(
            context, identity=("first",), source_references=("oss-common-deploy-2",)
        ).stem
        == first.stem
    )


def test_inherited_namespace_keeps_parent_context_unresolved(tmp_path):
    root = _template(tmp_path)
    _write(
        root,
        "templates/env_templates/business.yaml",
        {
            "parent-templates": {"product": "product:1"},
            "namespaces": [
                {
                    "parent": "product",
                    "deploy_postfix": "oss",
                    "overrides-parent": {"name": "env-oss"},
                }
            ],
        },
    )
    proposal = _proposal(TemplateContext(root))
    assert proposal.attachment is None
    assert "overrides-parent" in proposal.reason and "parent" in proposal.reason


@pytest.mark.parametrize(
    "kind",
    ["malformed", "conditional", "ambiguous", "traversal", "linked-file", "linked-dir"],
)
def test_unsafe_or_unresolved_context_does_not_invent_an_attachment(tmp_path, kind):
    root = _template(tmp_path)
    descriptor = root / "templates/env_templates/business.yaml"
    if kind == "malformed":
        descriptor.write_text("namespaces: [")
    elif kind == "conditional":
        descriptor.write_text("{% if enabled %}\nnamespaces: []\n{% endif %}")
    elif kind == "ambiguous":
        item = {"template_path": "{{ templates_dir }}/env_templates/oss.yml.j2"}
        descriptor.write_text(json.dumps({"namespaces": [item, item]}))
    elif kind == "traversal":
        descriptor.write_text(
            json.dumps(
                {
                    "namespaces": [
                        {
                            "deploy_postfix": "oss",
                            "template_path": "{{ templates_dir }}/../outside.yml",
                        }
                    ]
                }
            )
        )
    else:
        external = _write(tmp_path, "outside/source.yml", {"deployParameterSets": []})
        if kind == "linked-file":
            target = root / "templates/env_templates/oss.yml.j2"
            target.unlink()
            target.symlink_to(external)
        else:
            linked = root / "templates/env_templates/linked"
            linked.symlink_to(external.parent, target_is_directory=True)
            descriptor.write_text(
                json.dumps(
                    {
                        "namespaces": [
                            {
                                "deploy_postfix": "oss",
                                "template_path": "{{ templates_dir }}/env_templates/linked/source.yml",
                            }
                        ]
                    }
                )
            )
    proposal = _proposal(TemplateContext(root))
    assert proposal.attachment is None and proposal.reason


def test_templates_directory_is_accepted_but_a_missing_root_is_explained(tmp_path):
    root = _template(tmp_path)
    assert _proposal(TemplateContext(root / "templates")).attachment
    assert _proposal(TemplateContext(tmp_path / "missing")).reason


def test_duplicate_selected_parameter_set_stems_are_reported_as_uncertain(tmp_path):
    root = _template(tmp_path)
    for folder in ("one", "two"):
        _write(
            root,
            f"templates/parameters/{folder}/product-defaults.yml",
            {"name": "product-defaults", "parameters": {"SETTING": "shared"}},
        )
    proposal = _proposal(TemplateContext(root))
    assert len(proposal.definitions) == 2
    assert all("ambiguous" in item for item in proposal.definitions)


def test_normalized_scopes_and_artifacts_do_not_share_new_names(tmp_path):
    root = _template(tmp_path)
    _write(
        root,
        "templates/env_templates/business.yaml",
        {
            "namespaces": [
                {
                    "deploy_postfix": "oss-app",
                    "template_path": "{{ templates_dir }}/env_templates/oss.yml.j2",
                },
                {
                    "deploy_postfix": "oss",
                    "template_path": "{{ templates_dir }}/env_templates/oss.yml.j2",
                },
            ]
        },
    )
    context = TemplateContext(root)
    one = _proposal(context, Scope("oss-app", Category.DEPLOY, "one"))
    two = _proposal(context, Scope("oss", Category.DEPLOY, "app-one"))
    three = context.propose(
        "business",
        "templates:2",
        Scope("oss", Category.DEPLOY, "app-one"),
        [(("SETTING",), "shared")],
    )
    assert len({one.stem, two.stem, three.stem}) == 3
    assert all(p.stem and p.attachment for p in (one, two, three))


@pytest.mark.parametrize(
    "override",
    [[], "dynamic", {"deployParameterSets": {}}, {"deployParameterSets": [False]}],
)
def test_invalid_override_shapes_leave_a_located_review(tmp_path, override):
    proposal = _proposal(
        TemplateContext(_template(tmp_path, template_override=override))
    )
    assert proposal.attachment is None and proposal.reason
    assert proposal.descriptor == "templates/env_templates/business.yaml"


def test_inline_descriptor_overrides_are_listed_as_source_definitions(tmp_path):
    root = _template(
        tmp_path, template_override={"deployParameters": {"SETTING": "shared"}}
    )
    proposal = _proposal(TemplateContext(root))
    assert any(
        "business.yaml:1:" in item and "same value" in item
        for item in proposal.definitions
    )


def test_unreadable_selected_parameter_source_has_a_concrete_uncertainty(tmp_path):
    root = _template(tmp_path)
    _write(root, "templates/parameters/product-defaults.yml", "parameters: [")
    proposal = _proposal(TemplateContext(root))
    assert any(
        "product-defaults.yml" in item and "Cannot inspect" in item
        for item in proposal.definitions
    )


@pytest.mark.parametrize("extension", [".json", ".j2"])
def test_all_supported_parameter_formats_reserve_names_and_supply_evidence(
    tmp_path, extension
):
    root = _template(tmp_path)
    _write(
        root,
        "templates/parameters/oss-common-deploy" + extension,
        {"name": "oss-common-deploy", "parameters": {}},
    )
    _write(
        root,
        "templates/parameters/product-defaults" + extension,
        {"name": "product-defaults", "parameters": {"SETTING": "shared"}},
    )
    proposal = _proposal(TemplateContext(root))
    assert proposal.stem == "oss-common-deploy-2"
    assert any(
        "product-defaults" + extension in item and "same value" in item
        for item in proposal.definitions
    )


@pytest.mark.parametrize(
    "filename,postfix",
    [
        ("oss.yml", "oss.yml"),
        ("oss.yaml", "oss.yaml"),
        ("oss.yml.j2", "oss"),
        ("oss.yaml.j2", "oss"),
        ("oss.j2", "oss.j2"),
    ],
)
def test_namespace_fallback_matches_generator_filename_rules(
    tmp_path, filename, postfix
):
    root = _template(tmp_path)
    _write(root, "templates/env_templates/" + filename, {"deployParameterSets": []})
    _write(
        root,
        "templates/env_templates/business.yaml",
        {
            "namespaces": [
                {"template_path": "{{ templates_dir }}/env_templates/" + filename}
            ]
        },
    )
    context = TemplateContext(root)
    assert _proposal(context, Scope(postfix, Category.DEPLOY)).attachment is not None
    if postfix != "oss":
        assert _proposal(context).attachment is None


def test_rejected_linked_template_root_never_opens_an_external_source(
    tmp_path, monkeypatch
):
    external = _template(tmp_path)
    _write(
        external,
        "templates/parameters/product-defaults.yml",
        {"name": "product-defaults", "parameters": {"SETTING": "shared"}},
    )
    selected = tmp_path / "selected"
    selected.mkdir()
    (selected / "templates").symlink_to(
        external / "templates", target_is_directory=True
    )
    context = TemplateContext(selected)
    opened = []
    original = type(selected).open

    def record(path, *args, **kwargs):
        opened.append(path.resolve())
        return original(path, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(type(selected), "open", record)
        proposal = _proposal(context)
    assert proposal.attachment is None and proposal.reason
    assert opened == []
    assert context._cache == {}
