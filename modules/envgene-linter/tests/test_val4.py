import json

import pytest
from click.testing import CliRunner
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import FoldedScalarString, LiteralScalarString

from envgene_linter.cli import main
from envgene_linter.connections import compute_connections
from envgene_linter.discovery import build_index
from envgene_linter.engine import run_check
from envgene_linter.html_report import render_html
from envgene_linter.model import Action, IssueType, Severity
from envgene_linter.report import render


def write(path, doc):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w') as stream:
        YAML().dump(doc, stream)
    return path


def paramset(repo, value, category='deploy'):
    repo.env('c', 'e', **{category: {'cloud': ['service-deploy']}})
    return write(repo.root / 'environments/parameters/service-deploy.yml',
                 {'name': 'service-deploy', 'parameters': {'CONFIG': value}})


def findings(repo):
    return [item for item in run_check(repo.root).findings if item.rule == 'VAL-4']


@pytest.mark.parametrize('value,kind', [
    ('{"retries": 3, "targets": ["a", "b"]}', 'JSON map'),
    ('["a", {"b": true}]', 'JSON list'), (' {} ', 'JSON map'), ('[]', 'JSON list'),
    (LiteralScalarString('retries: 3\ntargets:\n  - a\n'), 'YAML map'),
    (LiteralScalarString('- a\n- b\n'), 'YAML list'),
    (FoldedScalarString('retries: 3\n'), 'YAML map'),
    (LiteralScalarString('{"retries": 3}\n'), 'JSON map'),
])
def test_encoded_collection_is_reviewed_at_source(repo, value, kind):
    path = paramset(repo, value)
    result = findings(repo)
    assert len(result) == 1
    item = result[0]
    assert (item.path, item.key, item.line, item.column) == (path, 'parameters.CONFIG', 3, 3)
    assert (item.severity, item.issue_type, item.action) == (Severity.WARNING, IssueType.WARNING, Action.REVIEW)
    assert kind in item.message
    assert 'consumer' in item.hint


@pytest.mark.parametrize('value', [
    None, 3, True, '', 'plain text', 'Note: restart required', 'https://example.com/',
    '3', 'true', 'null', '"text"', '{bad json}', '{"key": 3} suffix', '[NaN]',
    '{"value": Infinity}', '[1,]', '{a: 1}',
    '${CONFIG}', '{{ config }}', '{"key": "${VALUE}"}', '{"key": "{{ value }}"}',
    LiteralScalarString('text\nwith lines\n'), LiteralScalarString('42\n'),
    LiteralScalarString('a: [\n'), LiteralScalarString('a: 1\n---\nb: 2\n'),
    LiteralScalarString('a: !custom value\n'), LiteralScalarString('a: &x [1]\nb: *x\n'),
    LiteralScalarString('a: "{% if flag %}"\n'), LiteralScalarString('a: "{# comment #}"\n'),
    {'retries': 3, 'targets': ['a', 'b']}, ['a', 'b'], {}, [],
])
def test_native_values_and_uncertain_strings_are_not_reported(repo, value):
    paramset(repo, value)
    assert findings(repo) == []


@pytest.mark.parametrize('category', ['deploy', 'e2e', 'technical'])
def test_all_connected_categories_are_checked(repo, category):
    paramset(repo, '[1, 2]', category)
    assert len(findings(repo)) == 1


def test_nested_and_application_values_but_not_metadata(repo):
    path = paramset(repo, 'safe')
    write(path, {'name': 'service-deploy', 'description': '{"ignored": true}',
                 'parameters': {'outer': ['[1]', {'VALUE': '{"a": 1}'}]},
                 'applications': [{'appName': 'app', 'parameters': {'CONFIG': '[2]'}}]})
    result = findings(repo)
    assert {f.key for f in result} == {
        'parameters.outer.0', 'parameters.outer.1.VALUE', 'applications.0.parameters.CONFIG'}
    lines = path.read_text().splitlines()
    for item in result:
        assert '[' in lines[item.line - 1] or 'VALUE:' in lines[item.line - 1]
        assert item.column > 0


def test_shared_physical_file_reported_once(repo):
    paramset(repo, '[1]')
    repo.env('c', 'second', technical={'cloud': ['service-deploy']})
    repo.env('other', 'e', e2e={'cloud': ['service-deploy']})
    assert len(findings(repo)) == 1


def test_unused_shadowed_and_other_entity_types_are_excluded(repo):
    paramset(repo, '[1]')
    repo.cluster_paramset('c', 'service-deploy', {'CONFIG': 'native'})
    write(repo.root / 'environments/parameters/unused.yml', {'parameters': {'CONFIG': '[2]'}})
    repo.passport('passport', {'cloud': {'CONFIG': "'[3]'"}}, cluster='c')
    write(repo.root / 'environments/c/e/cloud.yml', {'deployParameters': {'CONFIG': '[4]'}})
    assert findings(repo) == []


def test_invalid_and_jinja_files_are_skipped(repo):
    path = paramset(repo, '[1]')
    path.write_text('parameters: [\n')
    assert findings(repo) == []
    path.rename(path.with_suffix('.yml.j2'))
    assert findings(repo) == []


def test_redaction_disable_and_cli(repo, monkeypatch):
    from envgene_linter import engine, rule_config
    path = paramset(repo, '{"private-key": "synthetic-private-value"}')
    original = path.read_bytes()
    result = run_check(repo.root)
    selected = [f for f in result.findings if f.rule == 'VAL-4']
    assert selected
    for output in (repr(selected), render(selected), render_html(selected, repo.root)):
        assert 'synthetic-private-value' not in output
        assert 'private-key' not in output
    cli = CliRunner().invoke(main, ['check', str(repo.root), '--console'])
    assert cli.exit_code == 0
    assert 'VAL-4' in cli.output
    html = (repo.root / 'envgene-linter-report.html').read_text()
    assert 'VAL-4' in html and '>Review</span>' in html
    assert path.read_bytes() == original
    monkeypatch.setitem(rule_config.RULE_ENABLED, 'VAL-4', False)
    def forbidden(*args):
        raise AssertionError('Disabled VAL-4 was called')
    monkeypatch.setattr(engine, 'check_val4', forbidden)
    disabled = run_check(repo.root)
    assert disabled.findings == [f for f in result.findings if f.rule != 'VAL-4']
    assert 'VAL-4' in disabled.disabled_rules
    assert 'VAL-4' not in render(disabled.findings, disabled_rules=disabled.disabled_rules)


@pytest.mark.parametrize('target', ['external', 'git', 'cycle'])
def test_unsafe_path_after_discovery_is_skipped(repo, target):
    from envgene_linter.rules.val4 import check
    path = paramset(repo, '[1]')
    index = build_index(repo.root)
    connections = compute_connections(index)
    path.unlink()
    if target == 'cycle':
        path.symlink_to(path)
    else:
        destination = repo.root / '.git/private.yml' if target == 'git' else repo.root.parent / (repo.root.name + '.yml')
        write(destination, {'parameters': {'CONFIG': '[1]'}})
        path.symlink_to(destination)
    assert check(index, connections) == []


@pytest.mark.parametrize('value', [
    json.dumps({'value': 'x' * 65536}), '[' * 65 + '0' + ']' * 65,
    LiteralScalarString('x: ' + '[' * 65 + '0' + ']' * 65),
    LiteralScalarString('\n'.join(f'key{i}: 1' for i in range(1500))),
], ids=['size', 'json-depth', 'yaml-depth', 'yaml-token-count'])
def test_recognition_limits_record_generic_note(repo, value):
    paramset(repo, value)
    result = run_check(repo.root)
    assert not [f for f in result.findings if f.rule == 'VAL-4']
    notes = [note for note in result.skipped if note.startswith('VAL-4:')]
    assert len(notes) == 1
    assert 'limit' in notes[0]
    assert value not in notes[0]


def test_native_aliases_cycles_and_depth_are_bounded(repo):
    from envgene_linter.rules.val4 import check
    path = paramset(repo, '[1]')
    index = build_index(repo.root)
    connections = compute_connections(index)
    bag = connections.parameter_files[path.resolve()].parameters
    shared = {'VALUE': '[2]'}
    bag['left'] = shared
    bag['right'] = shared
    bag['cycle'] = bag
    deep = bag
    for _ in range(70):
        deep['nested'] = {}
        deep = deep['nested']
    deep['VALUE'] = '[3]'
    result = check(index, connections)
    assert {f.key for f in result} == {'parameters.CONFIG', 'parameters.left.VALUE', 'parameters.right.VALUE'}
    assert len([note for note in index.skipped if note.startswith('VAL-4:')]) == 1


def test_shared_alias_graph_has_work_budget(repo):
    from envgene_linter.rules.val4 import check
    path = paramset(repo, 'safe')
    index = build_index(repo.root)
    connections = compute_connections(index)
    bag = connections.parameter_files[path.resolve()].parameters
    shared = {'value': 'plain text'}
    for _ in range(17):
        shared = {'left': shared, 'right': shared}
    bag['graph'] = shared
    assert check(index, connections) == []
    assert len([note for note in index.skipped if note.startswith('VAL-4:')]) == 1


def test_limit_does_not_hide_sibling_values_and_disabled_has_no_note(repo, monkeypatch):
    from envgene_linter import rule_config
    path = paramset(repo, 'safe')
    write(path, {'parameters': {'large': '[' * 65 + '0' + ']' * 65, 'valid': '[1]'}})
    result = run_check(repo.root)
    assert [f.key for f in result.findings if f.rule == 'VAL-4'] == ['parameters.valid']
    assert len([note for note in result.skipped if note.startswith('VAL-4:')]) == 1
    monkeypatch.setitem(rule_config.RULE_ENABLED, 'VAL-4', False)
    assert not [note for note in run_check(repo.root).skipped if note.startswith('VAL-4:')]


def test_yaml_indentless_sequences_count_toward_depth_limit(repo):
    text = 'value: 1'
    for _ in range(40):
        text = 'key:\n- ' + text.replace('\n', '\n  ')
    paramset(repo, LiteralScalarString(text))
    result = run_check(repo.root)
    assert not [item for item in result.findings if item.rule == 'VAL-4']
    assert len([note for note in result.skipped if note.startswith('VAL-4:')]) == 1
