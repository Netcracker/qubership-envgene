import pytest
from click.testing import CliRunner

from envgene_linter.engine import run_check
from envgene_linter.model import Action, IssueType, Severity
from envgene_linter.connections import compute_connections
from envgene_linter.discovery import build_index
from envgene_linter.cli import main


def findings(repo):
    return [item for item in run_check(repo.root).findings if item.rule == 'NAME-8']


def write(path, text='{}\n'):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


@pytest.mark.parametrize('name', ['c', 'custom', 'Passport', 'cluster-infra'])
def test_used_noncanonical_passport_name(repo, name):
    repo.env('c', 'e', cloud_passport=name)
    repo.passport(name, cluster='c')
    result = findings(repo)
    assert len(result) == 1
    assert result[0].path.name == name + '.yml'
    assert result[0].severity is Severity.WARNING
    assert result[0].issue_type is IssueType.WARNING
    assert result[0].action is Action.FIX
    assert (result[0].line, result[0].column) == (1, 1)
    assert 'passport' in result[0].hint


@pytest.mark.parametrize('extension', ['yml', 'yaml'])
@pytest.mark.parametrize('name', ['passport', 'passport-infra'])
def test_standard_and_infra_names_are_accepted(repo, name, extension):
    repo.env('c', 'e', cloud_passport=name)
    write(repo.root / f'environments/c/cloud-passport/{name}.{extension}', 'version: 1.5\n')
    write(repo.root / f'environments/c/cloud-passport/{name}-creds.yml')
    assert findings(repo) == []


def test_cluster_name_auto_association_is_checked(repo):
    repo.env('c', 'e')
    repo.passport('c', cluster='c')
    assert len(findings(repo)) == 1


@pytest.mark.parametrize('folder', ['cloud-passport', 'cloud-passports'])
def test_multiple_cluster_passports_suppress_passport_and_companion_naming(repo, folder):
    repo.env('c', 'e', cloud_passport='custom')
    repo.passport('custom', cluster='c')
    repo.passport('second', cluster='c', folder=folder)
    write(repo.root / 'environments/c/cloud-passport/custom-creds.yml')
    assert findings(repo) == []


def test_another_clusters_passport_does_not_disable_naming(repo):
    repo.env('c', 'e', cloud_passport='custom')
    repo.passport('custom', cluster='c')
    repo.env('other', 'e', cloud_passport='passport')
    repo.passport('passport', cluster='other')
    assert [item.path.name for item in findings(repo)] == ['custom.yml']


def test_repository_passport_contributes_to_each_cluster_context(repo):
    repo.env('c', 'e', cloud_passport='custom')
    repo.passport('custom', cluster='c')
    repo.passport('repository-default')
    assert findings(repo) == []


def test_jinja_candidate_does_not_disable_yaml_passport_naming(repo):
    repo.env('c', 'e', cloud_passport='custom')
    repo.passport('custom', cluster='c')
    write(repo.root / 'environments/c/cloud-passport/second.yml.j2')
    assert [item.path.name for item in findings(repo)] == ['custom.yml']


def test_unsafe_unselected_candidate_does_not_disable_naming(repo):
    from envgene_linter.rules.name8 import check
    repo.env('c', 'e', cloud_passport='custom')
    repo.passport('custom', cluster='c')
    repo.passport('second', cluster='c')
    index = build_index(repo.root)
    connections = compute_connections(index)
    path = repo.root / 'environments/c/cloud-passport/second.yml'
    path.unlink()
    destination = write(repo.root.parent / (repo.root.name + '-external.yml'))
    path.symlink_to(destination)
    assert [item.path.name for item in check(index, connections)] == ['custom.yml']


def test_infra_passport_is_not_a_second_default_passport(repo):
    repo.env('c', 'e', cloud_passport='custom')
    repo.passport('custom', cluster='c')
    repo.passport('passport-infra', cluster='c')
    assert [item.path.name for item in findings(repo)] == ['custom.yml']


def test_multiple_environment_passports_in_one_cluster_are_not_renamed(repo):
    repo.env('c', 'one', cloud_passport='first')
    repo.env('c', 'two', cloud_passport='second')
    repo.passport('first', cluster='c', env='one')
    repo.passport('second', cluster='c', env='two')
    assert findings(repo) == []


def test_unused_and_ambiguous_passports_are_not_checked(repo):
    repo.env('c', 'e', cloud_passport='custom')
    repo.passport('custom', cluster='c')
    repo.passport('custom')
    repo.passport('unused', cluster='c')
    assert findings(repo) == []


@pytest.mark.parametrize('slot', ['custom-creds.yml', 'credentials/custom.yml'])
def test_selected_companion_has_separate_naming_finding(repo, slot):
    repo.env('c', 'e', cloud_passport='custom')
    repo.passport('custom', cluster='c')
    credential = write(repo.root / 'environments/c/cloud-passport' / slot,
                       'private-id:\n  type: external\n  remoteRefPath: private-value\n')
    result = findings(repo)
    assert len(result) == 2
    assert credential in {item.path for item in result}
    assert all('private-id' not in repr(item) and 'private-value' not in repr(item) for item in result)


def test_legacy_credentials_priority_and_unselected_companion(repo):
    repo.env('c', 'e')
    repo.passport('passport', cluster='c')
    legacy = write(repo.root / 'environments/c/cloud-passport/credentials/passport.yml')
    write(repo.root / 'environments/c/cloud-passport/passport-creds.yml')
    write(repo.root / 'environments/c/cloud-passport/unrelated-creds.yaml')
    assert [item.path for item in findings(repo)] == [legacy]


def test_shared_file_is_reported_once(repo):
    repo.env('c', 'one', cloud_passport='custom')
    repo.env('c', 'two', cloud_passport='custom')
    repo.passport('custom', cluster='c')
    result = findings(repo)
    assert len(result) == 1
    assert 'c/one' in result[0].scope and 'c/two' in result[0].scope


def test_missing_credential_does_not_create_finding(repo):
    repo.env('c', 'e')
    repo.passport('passport', cluster='c')
    write(repo.root / 'environments/c/cloud-passport/passport-creds.yaml')
    assert findings(repo) == []


def test_rule_disabled_and_existing_findings_unchanged(repo, monkeypatch):
    from envgene_linter import engine, rule_config
    repo.env('c', 'e', cloud_passport='custom')
    repo.passport('custom', cluster='c')
    enabled = run_check(repo.root)
    assert any(item.rule == 'NAME-8' for item in enabled.findings)
    monkeypatch.setitem(rule_config.RULE_ENABLED, 'NAME-8', False)
    def forbidden(*args):
        raise AssertionError('Disabled rule invoked')
    monkeypatch.setattr(engine, 'check_name8', forbidden)
    disabled = run_check(repo.root)
    assert [item for item in enabled.findings if item.rule != 'NAME-8'] == disabled.findings
    assert 'NAME-8' in disabled.disabled_rules


def test_cli_reports_name8(repo):
    repo.env('c', 'e', cloud_passport='custom')
    repo.passport('custom', cluster='c')
    result = CliRunner().invoke(main, ['check', str(repo.root), '--console'])
    assert result.exit_code == 0
    assert 'NAME-8' in result.output
    assert 'NAME-8' in next(repo.root.rglob('*.html')).read_text()


@pytest.mark.parametrize('kind', ['directory', 'broken-link'])
def test_invalid_first_companion_does_not_select_fallback(repo, kind):
    repo.env('c', 'e', cloud_passport='custom')
    repo.passport('custom', cluster='c')
    legacy = repo.root / 'environments/c/cloud-passport/credentials/custom.yml'
    legacy.parent.mkdir()
    if kind == 'directory':
        legacy.mkdir()
    else:
        legacy.symlink_to(legacy.parent / 'missing.yml')
    write(repo.root / 'environments/c/cloud-passport/custom-creds.yml')
    assert [item.path.name for item in findings(repo)] == ['custom.yml']


@pytest.mark.parametrize('target', ['external', 'git', 'cycle'])
def test_changed_unsafe_passport_after_index_is_not_reported(repo, target):
    from envgene_linter.rules.name8 import check
    repo.env('c', 'e', cloud_passport='custom')
    repo.passport('custom', cluster='c')
    index = build_index(repo.root)
    connections = compute_connections(index)
    path = repo.root / 'environments/c/cloud-passport/custom.yml'
    path.unlink()
    if target == 'cycle':
        path.symlink_to(path)
    else:
        destination = (repo.root.parent / (repo.root.name + '-external.yml') if target == 'external'
                       else repo.root / '.git/private.yml')
        write(destination)
        path.symlink_to(destination)
    assert check(index, connections) == []


def test_file_aliases_are_deduplicated(repo):
    repo.env('c', 'one', cloud_passport='custom')
    repo.env('c', 'two', cloud_passport='alias')
    repo.passport('custom', cluster='c')
    base = repo.root / 'environments/c/cloud-passport'
    (base / 'alias.yml').symlink_to(base / 'custom.yml')
    assert len(findings(repo)) == 1


def test_passport_and_companion_alias_share_one_finding(repo):
    repo.env('c', 'e', cloud_passport='custom')
    repo.passport('custom', cluster='c')
    base = repo.root / 'environments/c/cloud-passport'
    (base / 'custom-creds.yml').symlink_to(base / 'custom.yml')
    result = findings(repo)
    assert len(result) == 1
    assert 'passport-creds' in result[0].message and "'passport'" in result[0].message
    assert 'separate' in result[0].hint
