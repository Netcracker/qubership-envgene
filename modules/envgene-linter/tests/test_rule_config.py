from pathlib import Path
from shutil import copytree
from unittest.mock import Mock

import pytest
from click.testing import CliRunner

from envgene_linter import engine
from envgene_linter.cli import main
from envgene_linter.rulemeta import RULES

EXAMPLES = Path(__file__).resolve().parents[1] / 'testdata/rules'


def config():
    from envgene_linter import rule_config
    return rule_config


@pytest.fixture
def naming_disabled(monkeypatch):
    flags = dict.fromkeys(RULES, True)
    for rule in ('NAME-1', 'NAME-3', 'NAME-4'):
        flags[rule] = False
    monkeypatch.setattr(config(), 'RULE_ENABLED', flags)


def test_source_flags_are_valid():
    disabled = config().disabled_rules()
    assert set(disabled) == {rule for rule, enabled in config().RULE_ENABLED.items() if not enabled}


def test_default_disabled_rules_are_not_reported_as_passed(naming_disabled, tmp_path):
    target = copytree(EXAMPLES / 'name1/not-ok', tmp_path / 'instance')
    result = CliRunner().invoke(main, ['check', str(target), '--console'])
    assert result.exit_code == 0, result.output
    for rule in ('NAME-1', 'NAME-3', 'NAME-4'):
        assert f'{rule}\nDisabled' in result.output
        assert f'{rule}\nNo findings' not in result.output
    assert 'share the value' not in result.output


@pytest.mark.parametrize('rule', sorted(RULES))
def test_each_flag_skips_the_rule_function(monkeypatch, rule):
    flags = {name: True for name in RULES}
    flags[rule] = False
    monkeypatch.setattr(config(), 'RULE_ENABLED', flags)
    checker = Mock(side_effect=AssertionError('disabled rule was called'))
    monkeypatch.setattr(engine, 'check_' + rule.lower().replace('-', ''), checker)
    result = engine.run_check(EXAMPLES / rule.lower().replace('-', '') / 'not-ok')
    checker.assert_not_called()
    assert not [f for f in result.findings if f.rule == rule]
    assert result.disabled_rules == (rule,)


@pytest.mark.parametrize('rule', ['NAME-1', 'NAME-3', 'NAME-4'])
def test_disabled_default_can_be_enabled(monkeypatch, rule, naming_disabled):
    monkeypatch.setitem(config().RULE_ENABLED, rule, True)
    result = engine.run_check(EXAMPLES / rule.lower().replace('-', '') / 'not-ok')
    assert any(f.rule == rule for f in result.findings)
    assert rule not in result.disabled_rules


def test_all_disabled_skips_preparation_and_produces_explicit_report(monkeypatch, tmp_path):
    monkeypatch.setattr(config(), 'RULE_ENABLED', dict.fromkeys(RULES, False))
    monkeypatch.setattr(engine, 'build_index', Mock(side_effect=AssertionError('unnecessary scan')))
    result = CliRunner().invoke(main, ['check', str(tmp_path), '--console'])
    assert result.exit_code == 0, result.output
    assert result.output.count('\nDisabled') == len(RULES)
    assert 'No findings' not in result.output
    body = (tmp_path / 'envgene-linter-report.html').read_text()
    assert 'No rules enabled' in body
    assert all(rule in body for rule in RULES)


@pytest.mark.parametrize('change', ['unknown', 'missing', 'string', 'number'])
def test_invalid_flags_fail_before_scanning(monkeypatch, tmp_path, change):
    flags = dict(config().RULE_ENABLED)
    if change == 'unknown':
        flags['NAME-999'] = True
    elif change == 'missing':
        del flags['SEC-1']
    else:
        flags['SEC-1'] = 'False' if change == 'string' else 0
    monkeypatch.setattr(config(), 'RULE_ENABLED', flags)
    monkeypatch.setattr(engine, 'build_index', Mock(side_effect=AssertionError('scan before validation')))
    result = CliRunner().invoke(main, ['check', str(tmp_path)])
    assert result.exit_code == 2
    assert 'Invalid rule configuration' in result.output


def test_cli_html_records_disabled_defaults(tmp_path, naming_disabled):
    (tmp_path / 'environments').mkdir()
    result = CliRunner().invoke(main, ['check', str(tmp_path)])
    assert result.exit_code == 0, result.output
    body = (tmp_path / 'envgene-linter-report.html').read_text()
    assert 'Disabled rules' in body
    assert all(rule in body for rule in ('NAME-1', 'NAME-3', 'NAME-4'))
