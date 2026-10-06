import pytest
from click.testing import CliRunner

from envgene_linter.cli import main
from envgene_linter.connections import compute_connections
from envgene_linter.discovery import build_index
from envgene_linter.engine import run_check
from envgene_linter.html_report import render_html
from envgene_linter.model import Action, Severity
from envgene_linter.report import render


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')
    return path


def parameter(repo, text, category='deploy'):
    repo.env('c', 'e', **{category: {'cloud': ['service-deploy']}})
    return write(repo.root / 'environments/parameters/service-deploy.yml', text)


def findings(repo):
    return [item for item in run_check(repo.root).findings if item.rule == 'TPL-1']


@pytest.mark.parametrize('text,line,column', [
    ('name: service-deploy\nparameters:\n  VALUE: "{{ current_env.name }}"\n', 3, 11),
    ('name: service-deploy\nparameters:\n  VALUE: {{ current_env.name }}\n', 3, 10),
    ('{% if enabled %}\nparameters: {}\n', 1, 1),
    ('{# template comment #}\nparameters: {}\n', 1, 1),
    ('parameters:\n  VALUE: |\n    {{ current_env.name }}\n', 3, 5),
    ('parameters:\n  VALUE: >\n    {{ current_env.name }}\n', 3, 5),
    ('parameters:\n  VALUE: "{{\n    current_env.name\n  }}"\n', 2, 11),
    ('parameters:\n  "{{ current_env.key }}": value\n', 2, 4),
    ('name: "{{ current_env.name }}"\nparameters: {}\n', 1, 8),
    ('parameters:\n  VALUE: "{{- current_env.name -}}"\n', 2, 11),
])
def test_jinja_is_reported_at_opening_delimiter(repo, text, line, column):
    path = parameter(repo, text)
    result = findings(repo)
    assert len(result) == 1
    item = result[0]
    assert (item.path, item.line, item.column) == (path, line, column)
    assert (item.severity, item.action) == (Severity.WARNING, Action.FIX)
    assert '.j2' in item.hint


@pytest.mark.parametrize('text', [
    'parameters: {VALUE: "plain text"}\n',
    'parameters: {VALUE: "${NAMESPACE}-core"}\n',
    'parameters: {VALUE: "${creds.get(\'service\').password}"}\n',
    'parameters: {VALUE: "{literal}"}\n',
    'parameters: {VALUE: "{{"}\n', 'parameters: {VALUE: "}}"}\n',
    'parameters: {VALUE: "{%"}\n', 'parameters: {VALUE: "{#"}\n',
    'parameters: [\n', '',
])
def test_plain_yaml_macros_and_incomplete_delimiters_are_silent(repo, text):
    parameter(repo, text)
    assert findings(repo) == []


@pytest.mark.parametrize('category', ['deploy', 'e2e', 'technical'])
def test_all_parameter_categories(repo, category):
    parameter(repo, 'parameters: {VALUE: "{{ value }}"}\n', category)
    assert len(findings(repo)) == 1


def test_one_finding_per_source_line_and_shared_file(repo):
    parameter(repo, 'parameters:\n  VALUE: "{{ first }}-{{ second }}"\n  OTHER: "{{ third }}"\n')
    repo.env('c', 'other', deploy={'cloud': ['service-deploy']})
    result = findings(repo)
    assert [(item.line, item.column) for item in result] == [(2, 11), (3, 11)]
    assert all(item.scope == 'environments' for item in result)


@pytest.mark.parametrize('relative', [
    'environments/c/cloud-passport/passport.yml',
    'environments/c/cloud-passport/passport-creds.yml',
    'environments/c/cloud-passport/credentials/passport.yml',
    'environments/c/e/Credentials/credentials.yml',
    'environments/c/e/Inventory/credentials/inventory_generation_creds.yml',
    'environments/shared-credentials/shared.yml',
])
def test_selected_passports_and_credentials(repo, relative):
    repo.env('c', 'e')
    repo.passport('passport', {'cloud': {'CLOUD_API_HOST': 'example.invalid'}}, cluster='c')
    if 'shared-credentials' in relative:
        definition = repo.root / 'environments/c/e/Inventory/env_definition.yml'
        definition.write_text(definition.read_text() + '  sharedMasterCredentialFiles: [shared]\n')
    path = write(repo.root / relative, 'VALUE: "{{ value }}"\n')
    assert [item.path for item in findings(repo)] == [path]


def test_unselected_companion_is_also_checked(repo):
    repo.env('c', 'e')
    repo.passport('passport', {}, cluster='c')
    write(repo.root / 'environments/c/cloud-passport/credentials/passport.yml', 'VALUE: safe\n')
    companion = write(repo.root / 'environments/c/cloud-passport/passport-creds.yml', 'VALUE: "{{ unused }}"\n')
    assert [item.path for item in findings(repo)] == [companion]


def test_unused_and_shadowed_yaml_is_checked_but_readme_is_excluded(repo):
    original = parameter(repo, 'parameters: {VALUE: "{{ shadowed }}"}\n')
    repo.cluster_paramset('c', 'service-deploy', {'VALUE': 'safe'})
    expected = {original}
    for relative in (
        'environments/parameters/unused.yml', 'environments/shared-credentials/unused.yml',
        'environments/c/cloud-passport/unused.yml', 'templates/parameters.yml',
        'environments/c/e/cloud.yml',
    ):
        expected.add(write(repo.root / relative, 'VALUE: "{{ unused }}"\n'))
    write(repo.root / 'README.md', '{{ ignored }}')
    assert {item.path for item in findings(repo)} == expected


@pytest.mark.parametrize('suffix', ['.yml.j2', '.yaml.j2'])
def test_template_location_does_not_produce_a_finding(repo, suffix):
    path = parameter(repo, '{% if enabled %}\nVALUE: "{{ value }}"\n{% endif %}\n')
    path.rename(path.with_suffix(suffix))
    write(repo.root / f'templates/parameters{suffix}', '{{ value }}')
    assert findings(repo) == []


def test_invalid_utf8_records_generic_skip(repo):
    path = parameter(repo, '')
    path.write_bytes(b'\xff{{ synthetic-private-value }}')
    result = run_check(repo.root)
    assert not [item for item in result.findings if item.rule == 'TPL-1']
    notes = [note for note in result.skipped if note.startswith('TPL-1:')]
    assert len(notes) == 1
    assert 'synthetic-private-value' not in notes[0]


@pytest.mark.parametrize('target', ['external', 'git', 'cycle'])
def test_unsafe_paths_after_discovery(repo, target):
    from envgene_linter.rules.tpl1 import check
    path = parameter(repo, 'VALUE: "{{ value }}"\n')
    index = build_index(repo.root)
    connections = compute_connections(index)
    path.unlink()
    if target == 'cycle':
        path.symlink_to(path)
    else:
        destination = repo.root / '.git/private.yml' if target == 'git' else repo.root.parent / (repo.root.name + '.yml')
        write(destination, 'VALUE: "{{ value }}"\n')
        path.symlink_to(destination)
    assert check(index, connections) == []


def test_cli_redaction_no_mutation_and_disable(repo, monkeypatch):
    from envgene_linter import engine, rule_config
    path = parameter(repo, 'parameters: {VALUE: "{{ synthetic_private_value }}"}\n')
    before = path.read_bytes()
    result = findings(repo)
    assert len(result) == 1
    for output in (repr(result), render(result), render_html(result, repo.root)):
        assert 'synthetic_private_value' not in output
    cli = CliRunner().invoke(main, ['check', str(repo.root), '--console'])
    assert cli.exit_code == 0
    assert 'TPL-1' in cli.output
    assert 'TPL-1' in (repo.root / 'envgene-linter-report.html').read_text()
    assert path.read_bytes() == before
    monkeypatch.setitem(rule_config.RULE_ENABLED, 'TPL-1', False)
    def forbidden(*args):
        raise AssertionError('Disabled TPL-1 was called')
    monkeypatch.setattr(engine, 'check_tpl1', forbidden)
    disabled = run_check(repo.root)
    assert not [item for item in disabled.findings if item.rule == 'TPL-1']
    assert 'TPL-1' in disabled.disabled_rules
    assert not [note for note in disabled.skipped if note.startswith('TPL-1:')]


def test_multiline_comment_suppresses_nested_delimiters(repo):
    parameter(repo, '{#\n{{ nested }}\n#}\nparameters: {}\n')
    assert [(item.line, item.column) for item in findings(repo)] == [(1, 1)]


def test_standalone_statements_and_application_parameters(repo):
    parameter(repo, 'name: service-deploy\napplications:\n  - appName: service\n    parameters:\n'
                   '{% if enabled %}\n      VALUE: "{{ value }}"\n{% endif %}\n')
    assert [(item.line, item.column) for item in findings(repo)] == [(5, 1), (6, 15), (7, 1)]


def test_yaml_extension_and_crlf_source_positions(repo):
    path = parameter(repo, '')
    path = path.rename(path.with_suffix('.yaml'))
    path.write_bytes('parameters:\r\n  VALUE: "текст {{ value }}"\r\n'.encode('utf-8'))
    result = findings(repo)
    assert [(item.path, item.line, item.column) for item in result] == [(path, 2, 17)]


def test_physical_aliases_are_inspected_once(repo):
    path = parameter(repo, 'VALUE: "{{ value }}"\n')
    alias = path.with_name('alias-deploy.yml')
    alias.symlink_to(path)
    repo.env('c', 'other', technical={'cloud': ['alias-deploy']})
    result = findings(repo)
    assert len(result) == 1
    assert result[0].scope == 'environments'


@pytest.mark.parametrize('target', ['external', 'broken'])
def test_unsafe_companion_does_not_hide_other_yaml(repo, target):
    repo.env('c', 'e')
    repo.passport('passport', {}, cluster='c')
    directory = repo.root / 'environments/c/cloud-passport'
    legacy = directory / 'credentials/passport.yml'
    legacy.parent.mkdir()
    destination = repo.root.parent / (repo.root.name + '-external.yml')
    if target == 'external':
        write(destination, 'VALUE: "{{ private_value }}"\n')
    legacy.symlink_to(destination)
    companion = write(directory / 'passport-creds.yml', 'VALUE: "{{ unused }}"\n')
    assert [item.path for item in findings(repo)] == [companion]


def test_instance_template_passport_is_allowed_and_yaml_companion_is_checked(repo):
    repo.env('c', 'e', cloud_passport='passport')
    write(repo.root / 'environments/c/cloud-passport/passport.yml.j2', '{{ value }}\n')
    assert findings(repo) == []
    companion = write(repo.root / 'environments/c/cloud-passport/passport-creds.yml', 'VALUE: "{{ value }}"\n')
    assert [item.path for item in findings(repo)] == [companion]


def test_disabled_rule_does_not_add_read_notes(repo, monkeypatch):
    from envgene_linter import rule_config
    path = parameter(repo, '')
    path.write_bytes(b'\xff')
    monkeypatch.setitem(rule_config.RULE_ENABLED, 'TPL-1', False)
    result = run_check(repo.root)
    assert not [note for note in result.skipped if note.startswith('TPL-1:')]
    assert 'TPL-1' not in render(result.findings, disabled_rules=result.disabled_rules)


@pytest.mark.parametrize('text', [
    '{# {{ #}\nVALUE: "{{ actual }}"\n',
    '{% set note = "{{" %}\nVALUE: "{{ actual }}"\n',
    '{{ "{%" }}\nVALUE: "{% if enabled %}"\n',
])
def test_nested_opening_does_not_hide_later_construct(repo, text):
    parameter(repo, text)
    assert [(item.line, item.column) for item in findings(repo)] == [(1, 1), (2, 9)]
