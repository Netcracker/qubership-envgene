import json

import pytest
from click.testing import CliRunner

from envgene_linter import rule_config
from envgene_linter.cli import main
from envgene_linter.engine import run_check
from envgene_linter.html_report import render_html


def write(root, relative, text):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')
    return path


def test_cli_reports_incomplete_jinja_checks_without_disclosing_source(tmp_path):
    write(tmp_path, 'templates/invalid.yml.j2',
          '# template\n# second line\n{{ synthetic_private_name + }}\n')
    write(tmp_path, 'templates/valid.yml.j2', '{% include "missing.j2" %}\n')

    result = CliRunner(mix_stderr=False).invoke(main, ['check', str(tmp_path)])

    assert result.exit_code == 0, result.output
    html = (tmp_path / 'envgene-linter-report.html').read_text()
    data = json.loads((tmp_path / 'envgene-linter-report.json').read_text())
    skipped = [item for item in data if item['issue'].startswith('Check skipped:')]
    assert len(skipped) == 2
    assert {item['rule_id'] for item in skipped} == {'TPL-4', 'TPL-6'}
    assert all(item['files'] == ['templates/invalid.yml.j2:3:1'] for item in skipped)
    assert all(item['action'] == 'Review' for item in skipped)
    assert all(set(item) == {'rule_id', 'rule_title', 'files', 'issue', 'action', 'fix_suggestion'}
               for item in data)
    assert len([item for item in data if not item['issue'].startswith('Check skipped:')]) == 1
    assert 'Incomplete checks' in html
    assert 'templates/invalid.yml.j2:3:1' in html
    assert 'cannot parse Jinja' in result.stderr
    assert 'synthetic_private_name' not in html + json.dumps(data) + result.output


def test_skipped_source_cannot_look_like_a_clean_report(tmp_path):
    write(tmp_path, 'templates/invalid.j2', '{{ value + }}')

    result = CliRunner().invoke(main, ['check', str(tmp_path)])

    assert result.exit_code == 0, result.output
    html = (tmp_path / 'envgene-linter-report.html').read_text()
    assert 'Incomplete checks' in html
    assert '<p>No findings</p>' not in html
    assert json.loads((tmp_path / 'envgene-linter-report.json').read_text())


def test_descriptor_skip_locations_identify_each_scalar(tmp_path):
    write(tmp_path, 'templates/env_templates/example.yaml',
          'tenant: "{{ tenant + }}"\ncloud: "{{ cloud + }}"\nnamespaces: []\n')

    result = run_check(tmp_path)

    assert len(result.skipped) == 4
    assert {note.rsplit(':', 2)[-2] for note in result.skipped} == {'1', '2'}


@pytest.mark.parametrize('disabled', [('TPL-4',), ('TPL-4', 'TPL-6')])
def test_disabled_rules_do_not_create_skipped_report_entries(tmp_path, monkeypatch, disabled):
    write(tmp_path, 'templates/invalid.j2', '{{ value + }}')
    for rule in disabled:
        monkeypatch.setitem(rule_config.RULE_ENABLED, rule, False)

    result = CliRunner().invoke(main, ['check', str(tmp_path)])

    assert result.exit_code == 0, result.output
    data = json.loads((tmp_path / 'envgene-linter-report.json').read_text())
    assert {item['rule_id'] for item in data} == ({'TPL-6'} - set(disabled))
    html = (tmp_path / 'envgene-linter-report.html').read_text()
    assert ('Incomplete checks' in html) == ('TPL-6' not in disabled)


def test_unreadable_template_is_visible_in_both_reports(tmp_path):
    path = write(tmp_path, 'templates/invalid-encoding.j2', '')
    path.write_bytes(b'\xff\xfe')

    result = CliRunner().invoke(main, ['check', str(tmp_path)])

    assert result.exit_code == 0, result.output
    data = json.loads((tmp_path / 'envgene-linter-report.json').read_text())
    assert len(data) == 2
    assert all('cannot read template source' in item['issue'] for item in data)
    assert all(item['files'] == ['templates/invalid-encoding.j2:1:1'] for item in data)
    html = (tmp_path / 'envgene-linter-report.html').read_text()
    assert 'Incomplete checks' in html


def test_html_escapes_skip_notes(tmp_path):
    html = render_html([], tmp_path, skipped=['TPL-4: cannot read: templates/<unsafe>.j2:1:1'])
    assert '&lt;unsafe&gt;' in html
    assert '<unsafe>' not in html


def test_tpl4_analysis_recursion_is_visible_as_an_incomplete_check(tmp_path):
    # Jinja parses a long left-associative expression without exhausting its parser stack.
    write(tmp_path, 'templates/deep.yml.j2', '{{ ' + ' + '.join(['1'] * 1800) + ' }}')

    result = CliRunner().invoke(main, ['check', str(tmp_path)])

    assert result.exit_code == 0, result.output
    data = json.loads((tmp_path / 'envgene-linter-report.json').read_text())
    assert len(data) == 1
    assert data[0]['rule_id'] == 'TPL-4'
    assert data[0]['issue'].startswith('Check skipped:')
    assert data[0]['files'] == ['templates/deep.yml.j2:1:1']


@pytest.mark.parametrize('relative', [
    'configuration/artifact_definitions/example.yml',
    'environments/cloud-passport/example.yml',
    'environments/c/e/Inventory/env_definition.yml',
])
def test_legacy_yaml_skip_does_not_copy_source_into_reports(tmp_path, relative):
    (tmp_path / 'environments').mkdir()
    write(tmp_path, relative, 'password: TOP_SECRET_SYNTHETIC: invalid\n')

    result = CliRunner().invoke(main, ['check', str(tmp_path)])

    assert result.exit_code == 0, result.output
    html = (tmp_path / 'envgene-linter-report.html').read_text()
    assert 'Incomplete checks' in html
    assert relative in html
    assert 'TOP_SECRET_SYNTHETIC' not in html + result.output


def test_html_hides_disabled_rule_skip_but_retains_shared_skip(tmp_path, monkeypatch):
    (tmp_path / 'environments').mkdir()
    write(tmp_path, 'environments/credentials/shared.yml', 'password: [\n')
    write(tmp_path, 'configuration/artifact_definitions/example.yml', 'password: [\n')
    monkeypatch.setitem(rule_config.RULE_ENABLED, 'PLACE-8', False)

    result = CliRunner().invoke(main, ['check', str(tmp_path)])

    assert result.exit_code == 0, result.output
    html = (tmp_path / 'envgene-linter-report.html').read_text()
    assert 'PLACE-8' not in html
    assert 'INT-4: skipped unreadable or invalid Credential candidate:' in html
    assert 'Incomplete checks' in html
    assert 'configuration/artifact_definitions/example.yml' in html
