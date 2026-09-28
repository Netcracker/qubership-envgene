import pytest
from click.testing import CliRunner

from envgene_linter.cli import main
from envgene_linter.discovery import build_index
from envgene_linter.engine import run_check
from envgene_linter.model import Action, Severity
from test_tpl1 import write


def tpl1(root):
    return [item for item in run_check(root).findings if item.rule == 'TPL-1']


def test_template_repository_without_environments_is_supported(tmp_path):
    path = write(tmp_path / 'templates/parameters/service.yml', 'parameters:\n  VALUE: "{{ current_env.name }}"\n')
    assert build_index(tmp_path).environments == []
    items = tpl1(tmp_path)
    assert [(item.path, item.line, item.column, item.action) for item in items] == [(path, 2, 11, Action.FIX)]
    cli = CliRunner().invoke(main, ['check', str(tmp_path), '--console'])
    assert cli.exit_code == 0
    assert 'TPL-1' in cli.output
    assert (tmp_path / 'envgene-linter-report.html').is_file()


def test_template_repository_does_not_invoke_instance_rules(tmp_path, monkeypatch):
    from envgene_linter import engine
    write(tmp_path / 'templates/parameters/service.yml', 'parameters: {}\n')
    def forbidden(*args):
        raise AssertionError('Instance rule invoked on a template repository')
    monkeypatch.setattr(engine, 'check_int4', forbidden)
    monkeypatch.setattr(engine, 'check_val4', forbidden)
    result = run_check(tmp_path)
    assert result.findings == []
    assert result.skipped == []


@pytest.mark.parametrize('relative', [
    'templates/parameters/deep/service.yml', 'templates/regdefs/service.yml',
    'templates/env_templates/deep/cloud.yml', 'environments/parameters/unused.yml',
    'environments/c/e/Inventory/env_definition.yml', 'configuration/credentials/credentials.yml',
])
def test_all_yaml_in_supported_roots_is_checked(tmp_path, relative):
    (tmp_path / 'templates').mkdir()
    path = write(tmp_path / relative, 'VALUE: "{{ current_env.name }}"\n')
    assert [item.path for item in tpl1(tmp_path)] == [path]


def test_mixed_repository_checks_both_trees(tmp_path):
    paths = [write(tmp_path / relative, 'VALUE: "{{ current_env.name }}"\n') for relative in (
        'templates/parameters/service.yml', 'environments/parameters/service.yml')]
    assert {item.path for item in tpl1(tmp_path)} == set(paths)


@pytest.mark.parametrize('relative,expected', [
    ('templates/env_templates/cloud.yml.j2', 0), ('templates/parameters/service.yaml.j2', 0),
    ('templates/macros/helpers.j2', 0), ('environments/parameters/service.yml.j2', 1),
    ('environments/c/e/Inventory/template.j2', 1), ('configuration/template.yml.j2', 1),
])
def test_template_file_placement(tmp_path, relative, expected):
    (tmp_path / 'templates').mkdir()
    path = write(tmp_path / relative, 'VALUE: safe\n')
    items = tpl1(tmp_path)
    assert len(items) == expected
    if items:
        assert (items[0].path, items[0].line, items[0].action) == (path, 1, Action.FIX)
        assert 'templates/' in items[0].hint


def descriptor(extra=''):
    return ('tenant: "{{ templates_dir }}/tenant.yml.j2"\n'
            'cloud:\n  template_path: "{{ templates_dir }}/cloud.yml.j2"\n'
            '  template_override:\n    name: "{{ current_env.name }}"\n'
            'namespaces:\n  - template_path: "{{ templates_dir }}/namespace.yml.j2"\n'
            '    template_override:\n      name: "{{ current_env.name }}-core"\n'
            'composite_structure: "{{ templates_dir }}/composite.yml.j2"\n'
            'bg_domain: "{{ templates_dir }}/bg.yml.j2"\n'
            'external_credential_template: "{{ templates_dir }}/credentials.yml.j2"\n' + extra)


def test_generator_descriptor_fields_are_exempt(tmp_path):
    write(tmp_path / 'templates/env_templates/dev.yaml', descriptor())
    assert tpl1(tmp_path) == []


def test_descriptor_scalar_cloud_and_inline_override_are_exempt(tmp_path):
    write(tmp_path / 'templates/env_templates/dev.yml',
          'tenant: "{{ templates_dir }}/tenant.yml.j2"\n'
          'cloud: "{{ templates_dir }}/cloud.yml.j2"\n'
          'namespaces: [{template_path: "{{ templates_dir }}/ns.yml.j2", '
          'template_override: {name: "{{ current_env.name }}"}}]\n')
    assert tpl1(tmp_path) == []


@pytest.mark.parametrize('extra', [
    'description: "{{ current_env.name }}"\n',
    '# {{ current_env.name }}\n',
    'unexpected: "{{ current_env.name }}"\n',
])
def test_descriptor_exemption_is_limited_to_rendered_fields(tmp_path, extra):
    path = write(tmp_path / 'templates/env_templates/dev.yml', descriptor(extra))
    items = tpl1(tmp_path)
    assert [(item.path, item.line) for item in items] == [(path, 13)]


def test_comment_on_allowed_field_is_not_exempt(tmp_path):
    text = descriptor().replace('tenant.yml.j2"', 'tenant.yml.j2" # {{ current_env.name }}')
    write(tmp_path / 'templates/env_templates/dev.yml', text)
    assert [(item.line, item.action) for item in tpl1(tmp_path)] == [(1, Action.FIX)]


def test_descriptor_alias_does_not_exempt_unrelated_anchor(tmp_path):
    text = ('unrelated: &p "{{ current_env.name }}"\n'
            'tenant: *p\ncloud: plain.yml.j2\nnamespaces: []\n')
    write(tmp_path / 'templates/env_templates/dev.yml', text)
    assert [(item.line, item.action) for item in tpl1(tmp_path)] == [(1, Action.FIX)]


def test_descriptor_like_data_outside_descriptor_directory_is_checked(tmp_path):
    write(tmp_path / 'templates/parameters/data.yml', descriptor())
    assert len(tpl1(tmp_path)) == 8


def test_incomplete_yaml_descriptor_has_no_exemptions(tmp_path):
    path = write(tmp_path / 'templates/env_templates/dev.yml',
                 'tenant: "{{ templates_dir }}/tenant.yml.j2"\n{% if enabled %}\ncloud: [\n')
    assert [(item.path, item.line) for item in tpl1(tmp_path)] == [(path, 1), (path, 2)]


@pytest.mark.parametrize('expression', ['{{ .Values.host }}', '{{ this.id === "x" }}', '{{ runtime_value }}'])
def test_ambiguous_delimiters_require_review(tmp_path, expression):
    write(tmp_path / 'templates/parameters/service.yml', 'VALUE: |\n  ' + expression + '\n')
    items = tpl1(tmp_path)
    assert len(items) == 1
    assert (items[0].severity, items[0].action) == (Severity.INFORMATION, Action.REVIEW)
    assert expression not in items[0].message


def test_fix_takes_priority_over_review_on_same_line(tmp_path):
    write(tmp_path / 'templates/parameters/service.yml', 'VALUE: "{{ runtime_value }} {{ current_env.name }}"\n')
    items = tpl1(tmp_path)
    assert [(item.line, item.column, item.action) for item in items] == [(1, 29, Action.FIX)]


def test_ignored_directories_and_unsafe_symlinks(tmp_path):
    (tmp_path / 'templates').mkdir()
    for relative in ('templates/.git/private.yml', '.github/workflows/ci.yml', 'README.md',
                     'samples/example.yml', 'description_template.yaml'):
        write(tmp_path / relative, 'VALUE: "{{ current_env.name }}"\n')
    outside = write(tmp_path.parent / (tmp_path.name + '-outside.yml'), 'VALUE: "{{ current_env.name }}"\n')
    (tmp_path / 'templates/external.yml').symlink_to(outside)
    (tmp_path / 'templates/cycle.yml').symlink_to(tmp_path / 'templates/cycle.yml')
    assert tpl1(tmp_path) == []


def test_template_report_marks_instance_rules_not_applicable(tmp_path):
    write(tmp_path / 'templates/parameters/service.yml', 'parameters: {}\n')
    result = CliRunner().invoke(main, ['check', str(tmp_path), '--console'])
    assert result.exit_code == 0
    assert 'VAL-4\nNot applicable' in result.output
    assert 'TPL-1\nNo findings' in result.output
    html = (tmp_path / 'envgene-linter-report.html').read_text()
    assert 'Not applicable' in html
    assert 'VAL-4' in html


def test_composed_descriptor_keeps_rendered_field_exemptions(tmp_path):
    text = descriptor().replace('tenant: "{{ templates_dir }}/tenant.yml.j2"', 'tenant:\n  parent: basic-template')
    write(tmp_path / 'templates/env_templates/composed.yml', text)
    assert tpl1(tmp_path) == []


@pytest.mark.parametrize('expression', ['{{ $current_env.name }}', '{{ current_env.name === "prod" }}',
                                         '{{ current_env.name !== "prod" }}', '{{ this.current_env }}'])
def test_downstream_syntax_overrides_context_name_heuristic(tmp_path, expression):
    write(tmp_path / 'templates/parameters/service.yml', 'VALUE: |\n  ' + expression + '\n')
    items = tpl1(tmp_path)
    assert len(items) == 1
    assert items[0].action == Action.REVIEW


def test_composed_descriptor_can_inherit_tenant_and_cloud(tmp_path):
    write(tmp_path / 'templates/env_templates/composed.yml',
          'parent-templates: {base: "base:1.0.0"}\nnamespaces:\n'
          '  - parent: base\n    template_path: "{{ templates_dir }}/namespace.yml.j2"\n')
    assert tpl1(tmp_path) == []


def test_documented_namespace_name_is_exempt(tmp_path):
    text = descriptor().replace('  - template_path:', '  - name: "{{ current_env.name }}-core"\n    template_path:')
    write(tmp_path / 'templates/env_templates/dev.yml', text)
    assert tpl1(tmp_path) == []


def test_composition_rendered_overrides_are_exempt_but_lookup_fields_are_not(tmp_path):
    text = ('parent-templates: {base: "base:1.0.0"}\nnamespaces:\n'
            '  - parent: base\n    name: base\n    overrides-parent:\n'
            '      name: "{{ current_env.name }}"\n'
            '      deployParameters: {VALUE: "{{ current_env.name }}"}\n'
            '      deployParameterSets: ["{{ current_env.name }}"]\n')
    write(tmp_path / 'templates/env_templates/dev.yml', text)
    assert [(item.line, item.action) for item in tpl1(tmp_path)] == [(8, Action.FIX)]


def test_invalid_descriptor_path_type_is_not_exempt(tmp_path):
    text = descriptor().replace('template_path: "{{ templates_dir }}/cloud.yml.j2"',
                                'template_path: {invalid: "{{ current_env.name }}"}')
    write(tmp_path / 'templates/env_templates/dev.yml', text)
    assert [(item.line, item.action) for item in tpl1(tmp_path)] == [(3, Action.FIX)]


@pytest.mark.parametrize('parents,expected', [('base: "base:1.0.0"', 0),
                                              ('base: "base:1.0.0", other: "other:1.0.0"', 2)])
def test_namespace_override_implicit_parent_requires_single_parent(tmp_path, parents, expected):
    text = ('parent-templates: {' + parents + '}\nnamespaces:\n'
            '  - name: base\n    overrides-parent:\n'
            '      name: "{{ current_env.name }}"\n'
            '      deployParameters: {VALUE: "{{ current_env.name }}"}\n')
    write(tmp_path / 'templates/env_templates/dev.yml', text)
    assert len(tpl1(tmp_path)) == expected
