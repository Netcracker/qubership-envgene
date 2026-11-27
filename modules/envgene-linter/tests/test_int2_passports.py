"""Explicit Cloud Passport bindings use local generator lookup and honest uncertainty."""

import json
import os
from pathlib import Path

import pytest
from click.testing import CliRunner
from ruamel.yaml import YAML

from envgene_linter import rule_config
from envgene_linter.cli import main
from envgene_linter.discovery import build_index
from envgene_linter.model import Action
from envgene_linter.rules.int2 import check

ABSENT = object()
REFERENCE = 'synthetic-private-passport-name'


def write(path, document):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as stream:
        YAML().dump(document, stream)
    return path


def definition(repo, reference=REFERENCE, template=None):
    repo.env('c', 'e')
    document = {'inventory': {'environmentName': 'e'}}
    if reference is not ABSENT:
        document['inventory']['cloudPassport'] = reference
    if template is not None:
        document['envTemplate'] = template
    return write(repo.root / 'environments/c/e/Inventory/env_definition.yml', document)


def passports(repo):
    return [item for item in check(build_index(repo.root)) if item.key == 'Cloud Passport']


@pytest.mark.parametrize('template', [None, {}, {'name': 'remote-template'}, {'artifact': 'template:1'}])
def test_missing_explicit_passport_is_located_even_without_env_template(repo, template):
    path = definition(repo, template=template)

    findings = passports(repo)

    assert len(findings) == 1
    assert (findings[0].path, findings[0].line, findings[0].column) == (path, 3, 3)
    assert findings[0].action is Action.FIX and 'missing' in findings[0].message
    assert REFERENCE not in repr(findings)


@pytest.mark.parametrize('reference', [ABSENT, None, '', False, 0])
def test_optional_passport_absence_is_silent(repo, reference):
    definition(repo, reference)
    assert passports(repo) == []


@pytest.mark.parametrize('directory', [
    'environments/c/e/Inventory/cloud-passport', 'environments/c/e/Inventory/cloud-passports',
    'environments/c/cloud-passport', 'environments/c/cloud-passports',
    'environments/cloud-passport', 'environments/cloud-passports',
])
def test_readable_explicit_passport_can_resolve_at_each_supported_level(repo, directory):
    definition(repo)
    write(repo.root / directory / 'nested' / f'{REFERENCE}.yaml', {'cloud': {}})
    assert passports(repo) == []


def test_passport_in_a_sibling_cluster_does_not_resolve_reference(repo):
    definition(repo)
    write(repo.root / 'environments/other/cloud-passport' / f'{REFERENCE}.yml', {'cloud': {}})
    findings = passports(repo)
    assert len(findings) == 1 and findings[0].action is Action.FIX


@pytest.mark.parametrize('reference', ['{{ passport_name }}', '${PASSPORT_NAME}', ' ', ['name'], {'name': 'value'}])
def test_dynamic_or_unsupported_passport_reference_is_review(repo, reference):
    definition(repo, reference)
    findings = passports(repo)
    assert len(findings) == 1 and findings[0].action is Action.REVIEW
    assert 'unknown' in findings[0].message


@pytest.mark.parametrize('failure', ['syntax', 'encoding'])
def test_unreadable_passport_target_is_review_without_parser_content(repo, failure):
    definition(repo)
    path = write(repo.root / 'environments/c/cloud-passport' / f'{REFERENCE}.yml', {})
    path.write_bytes(b'\xff\xfe' if failure == 'encoding' else b'cloud: [SYNTHETIC_PRIVATE_VALUE')
    findings = passports(repo)
    assert len(findings) == 1 and findings[0].action is Action.REVIEW
    assert 'SYNTHETIC_PRIVATE_VALUE' not in repr(findings)


@pytest.mark.parametrize('target_kind', ['external', 'git', 'broken'])
def test_unsafe_or_broken_passport_target_is_review(repo, target_kind, monkeypatch):
    definition(repo)
    if target_kind == 'external':
        target = repo.root.parent / (repo.root.name + '-external.yml')
    else:
        target = repo.root / ('.git/private.yml' if target_kind == 'git' else 'missing.yml')
    if target_kind != 'broken':
        write(target, {'cloud': {}})
    alias = repo.root / 'environments/c/cloud-passport' / f'{REFERENCE}.yml'
    alias.parent.mkdir(parents=True)
    alias.symlink_to(target)
    index = build_index(repo.root)
    read_text = Path.read_text

    def guarded_read(path, *args, **kwargs):
        if path.resolve() == target:
            raise AssertionError('INT-2 must not read an unsafe target')
        return read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, 'read_text', guarded_read)
    findings = [item for item in check(index) if item.key == 'Cloud Passport']
    assert len(findings) == 1 and findings[0].action is Action.REVIEW


def test_incomplete_higher_priority_passport_search_blocks_lower_fallback(repo, monkeypatch):
    definition(repo)
    blocked = repo.root / 'environments/c/e/Inventory/cloud-passport'
    blocked.mkdir()
    write(repo.root / 'environments/cloud-passport' / f'{REFERENCE}.yml', {'cloud': {}})
    walk = os.walk

    def inaccessible(top, *args, **kwargs):
        if Path(top) == blocked:
            kwargs['onerror'](PermissionError('synthetic directory failure'))
            return iter(())
        return walk(top, *args, **kwargs)

    monkeypatch.setattr(os, 'walk', inaccessible)
    findings = passports(repo)
    assert len(findings) == 1 and findings[0].action is Action.REVIEW


@pytest.mark.parametrize('symlink', [False, True])
@pytest.mark.parametrize('lower_fallback', [False, True])
def test_file_in_place_of_passport_directory_requires_review(repo, symlink, lower_fallback):
    definition(repo)
    directory = repo.root / 'environments/c/e/Inventory/cloud-passport'
    if symlink:
        target = write(repo.root / 'passport-source.yml', {'cloud': {}})
        directory.symlink_to(target)
    else:
        write(directory, {'cloud': {}})
    if lower_fallback:
        write(repo.root / 'environments/c/cloud-passport' / f'{REFERENCE}.yml', {'cloud': {}})

    findings = passports(repo)

    assert len(findings) == 1 and findings[0].action is Action.REVIEW


def test_higher_priority_passport_is_not_ambiguous_with_lower_matches(repo):
    definition(repo)
    write(repo.root / 'environments/c/e/Inventory/cloud-passport' / f'{REFERENCE}.yml', {'cloud': {}})
    lower = write(repo.root / 'environments/c/cloud-passport' / f'{REFERENCE}.yml', {})
    lower.write_text('cloud: [\n')
    assert passports(repo) == []


def test_several_passports_in_one_lookup_directory_require_review(repo):
    definition(repo)
    for suffix in ('yml', 'yaml'):
        write(repo.root / 'environments/c/cloud-passport' / f'{REFERENCE}.{suffix}', {'cloud': {}})
    findings = passports(repo)
    assert len(findings) == 1 and findings[0].action is Action.REVIEW


def test_unrendered_passport_target_is_review(repo):
    definition(repo)
    path = repo.root / 'environments/c/cloud-passport' / f'{REFERENCE}.yml.j2'
    path.parent.mkdir(parents=True)
    path.write_text('cloud: {{ CLOUD }}\n')
    findings = passports(repo)
    assert len(findings) == 1 and findings[0].action is Action.REVIEW


def test_json_is_not_a_supported_passport_target(repo):
    definition(repo)
    path = repo.root / 'environments/c/cloud-passport' / f'{REFERENCE}.json'
    path.parent.mkdir(parents=True)
    path.write_text('{"cloud": {}}')
    findings = passports(repo)
    assert len(findings) == 1 and findings[0].action is Action.FIX


@pytest.mark.parametrize('enabled', [True, False])
def test_explicit_passport_finding_reaches_reports_and_respects_rule_switch(repo, monkeypatch, enabled):
    definition(repo)
    monkeypatch.setitem(rule_config.RULE_ENABLED, 'INT-2', enabled)

    result = CliRunner().invoke(main, ['check', str(repo.root)])

    assert result.exit_code == 0, result.output
    data = json.loads((repo.root / 'envgene-linter-report.json').read_text())
    findings = [item for item in data if item['rule_id'] == 'INT-2']
    assert len(findings) == int(enabled)
    if enabled:
        assert findings[0]['files'] == ['environments/c/e/Inventory/env_definition.yml:3:3']
        assert findings[0]['action'] == 'Fix'
        assert REFERENCE not in json.dumps(findings)
        assert set(findings[0]) == {'rule_id', 'rule_title', 'files', 'issue', 'action', 'fix_suggestion'}
        assert 'INT-2' in (repo.root / 'envgene-linter-report.html').read_text()
