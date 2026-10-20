"""Recoverable input failures retain independent checks and honest reports."""

import json

import pytest
from click.testing import CliRunner

from envgene_linter.cli import main
from envgene_linter.engine import run_check
from envgene_linter.model import Action
from envgene_linter.yamlio import YamlReadError, load

pytestmark = pytest.mark.usefixtures('all_rules_enabled')


def write(root, relative, text):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')
    return path


def environment(root, name='e', references=('bad', 'good')):
    names = ', '.join(references)
    return write(root, f'environments/c/{name}/Inventory/env_definition.yml',
                 f'inventory:\n  environmentName: {name}\nenvTemplate:\n'
                 f'  envSpecificParamsets:\n    cloud: [{names}]\n')


def oversized(format_name):
    number = '1' * 5000
    if format_name == 'json':
        return '{"name":"bad","parameters":{"VALUE":' + number + '}}'
    return 'name: bad\nparameters:\n  VALUE: ' + number + '\n'


def exported(root):
    return json.loads((root / 'envgene-linter-report.json').read_text(encoding='utf-8'))


@pytest.mark.parametrize('suffix', ['yml', 'json'])
def test_oversized_integer_is_a_safe_read_error(tmp_path, suffix):
    path = write(tmp_path, f'bad.{suffix}', oversized(suffix))
    with pytest.raises(YamlReadError) as caught:
        load(path)
    assert (caught.value.line, caught.value.column) == (1, 1)
    assert '111111111111' not in str(caught.value)


@pytest.mark.parametrize('scalar', [
    '!!bool maybe', '!!int ""', '!!float ""', ':'.join(['1'] * 200) + '.0',
], ids=['invalid-bool', 'empty-int', 'empty-float', 'sexagesimal-overflow'])
def test_malformed_yaml_scalar_conversion_keeps_fresh_reports(tmp_path, scalar):
    environment(tmp_path)
    path = write(tmp_path, 'environments/parameters/bad.yml',
                 '%YAML 1.1\n---\nname: bad\nparameters:\n  VALUE: ' + scalar + '\n')
    with pytest.raises(YamlReadError):
        load(path)
    write(tmp_path, 'environments/parameters/good.yml', 'name: good\nparameters: {CONFIG: "[1]"}\n')
    write(tmp_path, 'envgene-linter-report.html', 'STALE_PREVIOUS_REPORT')
    write(tmp_path, 'envgene-linter-report.json', '[{"issue":"STALE_PREVIOUS_REPORT"}]')

    result = CliRunner().invoke(main, ['check', str(tmp_path)])

    assert result.exit_code == 0, result.output
    data = exported(tmp_path)
    assert any(item['rule_id'] == 'VAL-4' and item['issue'].startswith('Check skipped:') for item in data)
    assert any(item['rule_id'] == 'VAL-4' and not item['issue'].startswith('Check skipped:') for item in data)
    assert 'STALE_PREVIOUS_REPORT' not in json.dumps(data)
    assert 'STALE_PREVIOUS_REPORT' not in (tmp_path / 'envgene-linter-report.html').read_text()


@pytest.mark.parametrize('suffix', ['yml', 'json'])
def test_deep_decoded_containers_are_unavailable_before_consumers(tmp_path, suffix):
    text = '{"parameters":{"VALUE":' + '[' * 300 + '1' + ']' * 300 + '}}'
    path = write(tmp_path, f'deep.{suffix}', text)
    with pytest.raises(YamlReadError):
        load(path)


def test_ordinary_shared_yaml_aliases_remain_readable(tmp_path):
    path = write(tmp_path, 'shared.yml', 'parameters:\n  A: &same {VALUE: 1}\n  B: *same\n')
    document = load(path)
    assert document.doc['parameters'] == {'A': {'VALUE': 1}, 'B': {'VALUE': 1}}


@pytest.mark.parametrize('text', ['parameters: &params\n  SELF: *params\n', '&items [*items]'])
def test_cyclic_yaml_is_unavailable_instead_of_becoming_a_null_value(tmp_path, text):
    path = write(tmp_path, 'cycle.yml', text)
    with pytest.raises(YamlReadError):
        load(path)


def test_context_collector_restores_outer_scope_after_exception(tmp_path):
    from envgene_linter.read_errors import collect_read_errors

    with collect_read_errors() as outer:
        with pytest.raises(RuntimeError):
            with collect_read_errors() as inner:
                with pytest.raises(YamlReadError):
                    load(tmp_path / 'inner.yml')
                raise RuntimeError('synthetic implementation error')
        with pytest.raises(YamlReadError):
            load(tmp_path / 'outer.yml')
    with pytest.raises(YamlReadError):
        load(tmp_path / 'outside.yml')
    assert [problem.path.name for problem in inner] == ['inner.yml']
    assert [problem.path.name for problem in outer] == ['outer.yml']


def test_unexpected_rule_failure_propagates(tmp_path, monkeypatch):
    from envgene_linter import engine

    (tmp_path / 'environments').mkdir()
    def broken_check(*args):
        raise ValueError('synthetic implementation error')
    monkeypatch.setattr(engine, 'check_val4', broken_check)
    with pytest.raises(ValueError, match='synthetic implementation error'):
        run_check(tmp_path)


def test_json_syntax_error_keeps_location_without_source_excerpt(tmp_path):
    path = write(tmp_path, 'bad.json', '{"parameters":\n  SYNTHETIC_PRIVATE_VALUE\n}\n')
    with pytest.raises(YamlReadError) as caught:
        load(path)
    assert (caught.value.line, caught.value.column) == (2, 3)
    assert 'SYNTHETIC_PRIVATE_VALUE' not in str(caught.value)


def test_position_builder_defects_are_not_reclassified_as_input_errors(tmp_path, monkeypatch):
    from envgene_linter import yamlio

    path = write(tmp_path, 'valid.json', '{"parameters": {"VALUE": 1}}')
    def broken_positions(text):
        raise ValueError('position implementation defect')
    monkeypatch.setattr(yamlio, '_json_positions', broken_positions)
    with pytest.raises(ValueError, match='position implementation defect'):
        load(path)


@pytest.mark.parametrize('suffix', ['yml', 'json'])
@pytest.mark.parametrize('failure', ['conversion', 'syntax', 'encoding', 'depth'])
def test_failed_parameter_source_preserves_good_findings_and_both_reports(tmp_path, suffix, failure):
    environment(tmp_path)
    bad = write(tmp_path, f'environments/parameters/bad.{suffix}', oversized(suffix))
    if failure == 'syntax':
        bad.write_text('{"parameters": [SYNTHETIC_PRIVATE_VALUE}', encoding='utf-8')
    elif failure == 'encoding':
        bad.write_bytes(b'\xff\xfe')
    elif failure == 'depth':
        bad.write_text('{"parameters":{"VALUE":' + '[' * 300 + '1' + ']' * 300 + '}}', encoding='utf-8')
    write(tmp_path, 'environments/parameters/good.yml', 'name: good\nparameters:\n  CONFIG: "[1]"\n')

    result = CliRunner().invoke(main, ['check', str(tmp_path), '--console'])

    assert result.exit_code == 0, result.output
    data = exported(tmp_path)
    skips = [item for item in data if item['issue'].startswith('Check skipped:')]
    assert any(item['rule_id'] == 'VAL-4' and item['files'][0].startswith(f'environments/parameters/bad.{suffix}:')
               for item in skips)
    assert any(item['rule_id'] == 'VAL-4' and item['files'] == ['environments/parameters/good.yml:3:3']
               for item in data if not item['issue'].startswith('Check skipped:'))
    assert all(item['action'] == 'Review' for item in skips)
    html = (tmp_path / 'envgene-linter-report.html').read_text(encoding='utf-8')
    assert 'Incomplete checks' in html
    assert 'SYNTHETIC_PRIVATE_VALUE' not in html + json.dumps(data) + result.output
    assert 'HTML report saved here:' in result.output and 'JSON report saved here:' in result.output


@pytest.mark.parametrize('relative', ['templates/bad.j2', 'templates/env_templates/bad.yaml'])
def test_oversized_jinja_literal_is_skipped_while_valid_template_is_checked(tmp_path, relative):
    expression = '{{ ' + '1' * 5000 + ' }}'
    text = expression if relative.endswith('.j2') else f'tenant: "{expression}"\ncloud: cloud.j2\nnamespaces: []\n'
    write(tmp_path, relative, text)
    write(tmp_path, 'templates/good.j2', '{% include "missing.j2" %}\n')

    result = CliRunner().invoke(main, ['check', str(tmp_path)])

    assert result.exit_code == 0, result.output
    data = exported(tmp_path)
    skips = [item for item in data if item['issue'].startswith('Check skipped:')]
    assert {item['rule_id'] for item in skips} == {'TPL-4', 'TPL-6'}
    assert all(item['files'] == [f'{relative}:1:1'] for item in skips)
    assert any(item['rule_id'] == 'TPL-6' and item['action'] == 'Fix' for item in data)


def test_compatibility_only_jinja_failure_is_visible(tmp_path):
    (tmp_path / 'environments').mkdir()
    write(tmp_path, 'configuration/service.yml',
          'VALUE: "{{ lookup(\'env\', \'HOME\') + ' + '1' * 5000 + ' }}"\n')
    result = CliRunner().invoke(main, ['check', str(tmp_path)])
    assert result.exit_code == 0, result.output
    skips = [item for item in exported(tmp_path) if item['issue'].startswith('Check skipped:')]
    assert any(item['rule_id'] == 'TPL-6' and item['files'] == ['configuration/service.yml:1:1'] for item in skips)


def test_compatibility_parse_failure_retains_independent_rewrite_findings(tmp_path):
    path = write(tmp_path, 'templates/example.yaml.j2',
                 "{% raw %}{{ _foo }}{% endraw %}\n{{ lookup('ansible.builtin.env', 'bad$key') }}\n")
    result = run_check(tmp_path)
    assert any(item.rule == 'TPL-6' and item.path == path and item.line == 1
               and 'literal' in item.message for item in result.findings)
    assert any(item.rule == 'TPL-6' and item.path == path and item.line == 2 for item in result.skipped_checks)


def test_malformed_descriptor_cannot_silently_remove_template_checks(tmp_path):
    write(tmp_path, 'templates/env_templates/bad.yaml', 'tenant: [\n  SYNTHETIC_PRIVATE_VALUE\n')
    result = CliRunner().invoke(main, ['check', str(tmp_path)])
    assert result.exit_code == 0, result.output
    skips = [item for item in exported(tmp_path) if item['issue'].startswith('Check skipped:')]
    assert {item['rule_id'] for item in skips} == {'TPL-1', 'TPL-4', 'TPL-6'}
    assert 'SYNTHETIC_PRIVATE_VALUE' not in result.output + json.dumps(exported(tmp_path))


def test_failed_descriptor_exemptions_cannot_produce_tpl1_fix(tmp_path, monkeypatch):
    from envgene_linter import rule_config

    monkeypatch.setattr(rule_config, 'RULE_ENABLED', {rule: rule == 'TPL-1' for rule in rule_config.RULES})
    write(tmp_path, 'templates/env_templates/bad.yaml',
          'tenant: "{{ templates_dir }}/tenant.yaml.j2"\ncloud: [\nnamespaces: []\n')
    result = CliRunner().invoke(main, ['check', str(tmp_path)])
    assert result.exit_code == 0, result.output
    data = exported(tmp_path)
    assert len(data) == 1 and data[0]['rule_id'] == 'TPL-1'
    assert data[0]['action'] == 'Review' and data[0]['issue'].startswith('Check skipped:')


def test_failed_run_replaces_previous_reports_with_current_incomplete_results(tmp_path):
    environment(tmp_path)
    write(tmp_path, 'environments/parameters/bad.yml', oversized('yml'))
    write(tmp_path, 'environments/parameters/good.yml', 'name: good\nparameters: {CONFIG: "[1]"}\n')
    write(tmp_path, 'envgene-linter-report.html', 'STALE_PREVIOUS_REPORT')
    write(tmp_path, 'envgene-linter-report.json', '[{"issue":"STALE_PREVIOUS_REPORT"}]')
    result = CliRunner().invoke(main, ['check', str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert 'STALE_PREVIOUS_REPORT' not in (tmp_path / 'envgene-linter-report.html').read_text()
    assert 'STALE_PREVIOUS_REPORT' not in json.dumps(exported(tmp_path))
    assert any(item['issue'].startswith('Check skipped:') for item in exported(tmp_path))


@pytest.mark.parametrize('failure', ['syntax', 'conversion'])
def test_unreadable_definition_remains_a_potential_shared_consumer(tmp_path, failure):
    environment(tmp_path, 'a', ('base', 'shared'))
    definition = environment(tmp_path, 'b', ('shared',))
    definition.write_text('inventory: [\n' if failure == 'syntax' else 'VALUE: ' + '1' * 5000, encoding='utf-8')
    write(tmp_path, 'environments/parameters/base.yml', 'name: base\nparameters: {VALUE: 1}\n')
    write(tmp_path, 'environments/c/parameters/shared.yml', 'name: shared\nparameters: {VALUE: 1}\n')
    result = run_check(tmp_path)
    restatements = [item for item in result.findings if item.rule == 'PLACE-2']
    assert len(restatements) == 1 and restatements[0].action is Action.REVIEW


def test_incomplete_merge_context_cannot_confirm_place1_promotion(tmp_path):
    environment(tmp_path, 'a', ('good', 'bad'))
    environment(tmp_path, 'b', ('good',))
    for name in ('a', 'b'):
        write(tmp_path, f'environments/c/{name}/Inventory/parameters/good.yml', 'name: good\nparameters: {VALUE: 1}\n')
    write(tmp_path, 'environments/parameters/bad.yml', 'parameters: [\n')
    result = run_check(tmp_path)
    assert not any(item.rule == 'PLACE-1' and item.action is Action.FIX for item in result.findings)
    assert any(item.rule == 'PLACE-1' for item in result.skipped_checks)


def test_shadowed_and_unbound_failures_do_not_gain_connected_skip_entries(tmp_path):
    environment(tmp_path, references=('bad',))
    write(tmp_path, 'environments/parameters/bad.yml', oversized('yml'))
    write(tmp_path, 'environments/c/parameters/bad.yml', 'name: bad\nparameters: {VALUE: 1}\n')
    write(tmp_path, 'environments/parameters/orphan.json', oversized('json'))
    result = CliRunner().invoke(main, ['check', str(tmp_path)])
    assert result.exit_code == 0, result.output
    skips = [item for item in exported(tmp_path) if item['issue'].startswith('Check skipped:')]
    assert all(item['rule_id'] == 'INT-4' for item in skips)


def test_read_problem_collection_is_isolated_between_runs(tmp_path):
    broken, good = tmp_path / 'broken', tmp_path / 'good'
    environment(broken, references=('bad',))
    write(broken, 'environments/parameters/bad.yml', oversized('yml'))
    environment(good, references=('good',))
    write(good, 'environments/parameters/good.yml', 'name: good\nparameters: {VALUE: 1}\n')
    first = CliRunner().invoke(main, ['check', str(broken)])
    second = CliRunner().invoke(main, ['check', str(good)])
    assert first.exit_code == second.exit_code == 0
    assert any(item['issue'].startswith('Check skipped:') for item in exported(broken))
    assert not any(item['issue'].startswith('Check skipped:') for item in exported(good))


def test_disabled_rules_remain_absent_from_input_error_reports(tmp_path, monkeypatch):
    from envgene_linter import rule_config

    environment(tmp_path, references=('bad',))
    write(tmp_path, 'environments/parameters/bad.json', oversized('json'))
    monkeypatch.setitem(rule_config.RULE_ENABLED, 'VAL-4', False)
    result = CliRunner().invoke(main, ['check', str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert exported(tmp_path)
    assert not any(item['rule_id'] == 'VAL-4' for item in exported(tmp_path))


@pytest.mark.parametrize('relative,binding,rules', [
    ('environments/c/cloud-passport/passport.yml', '', {'PLACE-1', 'PLACE-4', 'PLACE-9', 'NAME-2'}),
    ('environments/resource_profiles/selected.yml', '  envSpecificResourceProfiles: {cloud: selected}\n', {'PLACE-8'}),
    ('environments/credentials/selected.yml', '  sharedMasterCredentialFiles: [selected]\n', {'PLACE-8'}),
    ('configuration/artifact_definitions/app.yml', '  artifact: app:1\n', {'NAME-2', 'SEC-5'}),
])
def test_selected_discovery_failures_keep_consumer_diagnostics(tmp_path, relative, binding, rules):
    definition = environment(tmp_path, references=())
    definition.write_text(definition.read_text() + binding, encoding='utf-8')
    path = write(tmp_path, relative, 'VALUE: ' + '1' * 5000 + '\n')
    result = run_check(tmp_path)
    assert rules <= {item.rule for item in result.skipped_checks if item.path == path}
    assert '111111111111' not in repr(result.skipped_checks)


def test_build_index_retains_safe_read_problems_outside_engine(tmp_path):
    from envgene_linter.discovery import build_index

    environment(tmp_path, references=('bad',))
    path = write(tmp_path, 'environments/parameters/bad.yml', 'parameters: [\n')
    index = build_index(tmp_path)
    assert any(item.path == path and (item.line, item.column) == (2, 1) for item in index.read_problems)
