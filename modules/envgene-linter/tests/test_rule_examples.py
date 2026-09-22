"""Check the public, runnable examples for every implemented rule."""
from pathlib import Path

import pytest

from envgene_linter.engine import run_check
from envgene_linter.rulemeta import RULES

ROOT = Path(__file__).resolve().parents[1] / 'testdata' / 'rules'


def test_example_catalog_covers_registered_rules():
    assert {p.name for p in ROOT.iterdir() if p.is_dir()} == {
        rule.lower().replace('-', '') for rule in RULES
    }


@pytest.mark.parametrize('rule', sorted(RULES))
@pytest.mark.parametrize('case', ['ok', 'not-ok'])
def test_rule_example(rule, case):
    folder = ROOT / rule.lower().replace('-', '')
    repo = folder / case
    assert (repo / 'environments').is_dir()
    result = run_check(repo)
    assert not result.skipped, result.skipped
    findings = [f for f in result.findings if f.rule == rule]
    if rule == 'NAME-3':
        expected = {'env_definition.yml'} if case == 'ok' else {'env_definition.yml', 'Bad_Name.yml'}
        assert {f.path.name for f in findings} == expected
        assert len(findings) == len(expected)
        return
    if case == 'ok':
        assert findings == []
    else:
        assert findings, f'{rule}: not-ok must demonstrate this rule'
        for finding in findings:
            assert finding.path.is_relative_to(repo)
            assert finding.path.is_file()
            assert finding.line >= 1 and finding.column >= 1
            assert finding.issue_type == RULES[rule].default_issue_type
            assert finding.action == RULES[rule].default_action
