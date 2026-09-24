import pytest

from envgene_linter.discovery import build_index
from envgene_linter.connections import compute_connections
from envgene_linter.model import Action, IssueType, Severity
from envgene_linter.report import render
from envgene_linter.html_report import render_html
from test_usage_candidates import write
from test_usage_references import bind, shared


def findings(repo):
    from envgene_linter.rules.int4 import check
    return check(build_index(repo.root))


def test_unreferenced_file_requires_review(repo):
    repo.env('c', 'e')
    repo.site_paramset('orphan', {'VALUE': 1})
    result = findings(repo)
    assert len(result) == 1
    item = result[0]
    assert (item.severity, item.issue_type, item.action) == (Severity.INFORMATION, IssueType.INFORMATION, Action.REVIEW)
    assert item.message == 'No references to this ParameterSet were found in the available sources.'
    assert 'External template consumers' in item.hint
    assert (item.line, item.column) == (1, 1)


def test_credential_findings_locate_entries_without_disclosing_ids(repo):
    repo.env('c', 'e')
    path = shared(repo, ids=('private-id-one', 'private-id-two'))
    result = findings(repo)
    assert len(result) == 2
    assert {x.path for x in result} == {path}
    assert {x.line for x in result} == {1, 5}
    for output in [repr(result), render(result), render_html(result, repo.root)]:
        assert 'private-id-one' not in output
        assert 'private-id-two' not in output
        assert 'synthetic' not in output
        assert 'safe to remove' not in output


@pytest.mark.parametrize('case,reason', [('dynamic', 'dynamic reference'), ('unreadable', 'could not be read'),
                                        ('no-env', 'No consuming environment'), ('lookup', 'lookup paths'),
                                        ('provenance', 'origin')])
def test_uncertainty_is_explained(repo, case, reason):
    if case != 'no-env':
        repo.env('c', 'e')
    if case == 'lookup':
        write(repo.root / 'environments/shared-template-variables/orphan.yml', {'VALUE': 1})
    elif case == 'no-env':
        repo.site_paramset('orphan', {'VALUE': 1})
    else:
        shared(repo)
        if case == 'dynamic':
            bind(repo, sharedMasterCredentialFiles=['${DYNAMIC}'])
        elif case == 'unreadable':
            (repo.root / 'environments/c/e/Inventory/env_definition.yml').write_text('invalid: [')
        else:
            bind(repo, sharedMasterCredentialFiles=['shared'])
            write(repo.root / 'environments/c/e/cloud.yml', {'defaultCredentialsId': 'used'})
            write(repo.root / 'environments/c/e/Credentials/credentials.yml', {'used': {'type': 'secret'}})
    assert findings(repo)
    assert all(reason in item.hint for item in findings(repo))


def test_used_in_one_environment_protects_repository_file(repo):
    repo.env('c', 'e', deploy={'cloud': ['used']})
    repo.env('c', 'other')
    repo.site_paramset('used', {'VALUE': 1})
    assert findings(repo) == []


def test_physical_alias_is_reported_once(repo):
    repo.env('c', 'e')
    path = shared(repo, ids=('orphan',))
    alias = repo.root / 'environments/c/e/Inventory/credentials/alias.yml'
    alias.parent.mkdir()
    alias.symlink_to(path)
    assert len(findings(repo)) == 1


def test_analysis_does_not_change_connections(repo):
    from envgene_linter.rules.int4 import check
    import copy
    repo.env('c', 'e')
    shared(repo)
    index = build_index(repo.root)
    connections = compute_connections(index)
    before = copy.deepcopy(connections)
    check(index, connections)
    assert connections == before


def test_engine_integration_and_disable_bypasses_analysis(repo, monkeypatch):
    from envgene_linter import engine, rule_config
    from envgene_linter.rulemeta import RULES
    from envgene_linter.report import RULE_ORDER
    repo.env('c', 'e')
    repo.site_paramset('orphan', {'VALUE': 1})
    result = engine.run_check(repo.root)
    assert len([x for x in result.findings if x.rule == 'INT-4']) == 1
    assert RULES['INT-4'].default_action is Action.REVIEW
    assert RULE_ORDER.index('INT-4') == RULE_ORDER.index('INT-3') + 1
    def forbidden(*args):
        raise AssertionError('Disabled analysis was invoked')
    monkeypatch.setattr(engine, 'check_int4', forbidden)
    monkeypatch.setitem(rule_config.RULE_ENABLED, 'INT-4', False)
    result = engine.run_check(repo.root)
    assert not any(x.rule == 'INT-4' for x in result.findings)
    assert 'INT-4' in result.disabled_rules


def test_cli_reports_review_and_returns_zero(repo):
    from click.testing import CliRunner
    from envgene_linter.cli import main
    repo.env('c', 'e')
    repo.site_paramset('orphan', {'VALUE': 1})
    result = CliRunner().invoke(main, ['check', str(repo.root), '--console'])
    assert result.exit_code == 0, result.output
    assert 'No references to this ParameterSet' in result.output
    pages = list(repo.root.rglob('*.html'))
    assert pages
    page = pages[0].read_text()
    assert 'No references to this ParameterSet' in page
    assert 'Information' in page and 'Review' in page


def test_other_rule_findings_are_unchanged_when_int4_is_enabled(repo, monkeypatch):
    from envgene_linter import engine, rule_config
    repo.env('c', 'e', deploy={'cloud': ['service']})
    repo.site_paramset('service', {'VALUE': 1})
    repo.cluster_paramset('c', 'service', {'VALUE': 2})
    shared(repo)
    enabled = engine.run_check(repo.root)
    monkeypatch.setitem(rule_config.RULE_ENABLED, 'INT-4', False)
    disabled = engine.run_check(repo.root)
    assert [x for x in enabled.findings if x.rule != 'INT-4'] == disabled.findings
