import pytest
from ruamel.yaml import YAML

from envgene_linter.connections import compute_connections
from envgene_linter.discovery import build_index


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w') as stream:
        YAML().dump(value, stream)
    return path


def candidates(repo):
    from envgene_linter.usage_candidates import collect_candidates
    index = build_index(repo.root)
    return collect_candidates(index, compute_connections(index))


def test_unbound_repository_parameter_set_is_candidate(repo):
    repo.site_paramset('orphan', {'VALUE': 1})
    assert [(x.kind, x.name, x.environments) for x in candidates(repo)] == [('ParameterSet', 'orphan', ())]


@pytest.mark.parametrize('base', ['environments', 'environments/c', 'environments/c/e/Inventory'])
@pytest.mark.parametrize('folder,kind,body', [
    ('parameters', 'ParameterSet', {'name': 'orphan', 'parameters': {'VALUE': 1}}),
    ('resource_profiles/nested', 'Resource Profile Override', {'baseline': 'small'}),
    ('shared-template-variables/nested', 'Shared Template Variable', {'value': 1}),
    ('credentials/nested', 'Credential', {'one': {'type': 'secret'}, 'two': {'type': 'secret'}}),
])
def test_typed_catalogs_at_each_scope(repo, base, folder, kind, body):
    repo.env('c', 'e')
    path = write(repo.root / base / folder / 'orphan.yaml', body)
    result = candidates(repo)
    assert len(result) == (2 if kind == 'Credential' else 1)
    assert all(x.path == path and x.kind == kind and x.environments == ('c/e',) for x in result)


@pytest.mark.parametrize('text', ['', '[1, 2]', 'secret: [broken', '\xff'])
def test_invalid_candidates_are_skipped(repo, text):
    repo.env('c', 'e')
    path = repo.root / 'environments/credentials/bad.yml'
    path.parent.mkdir()
    path.write_bytes(text.encode('latin1'))
    assert candidates(repo) == []


def test_generated_and_untyped_sources_are_not_candidates(repo):
    repo.env('c', 'e')
    for relative in ['environments/c/e/Credentials/credentials.yml', 'environments/c/e/Profiles/small.yml',
                     'environments/configuration/arbitrary.yml', 'environments/credentials/empty.yml']:
        write(repo.root / relative, {})
    write(repo.root / 'environments/parameters/template.yml.j2', {'parameters': {'V': 1}})
    assert candidates(repo) == []


def test_physical_aliases_retain_environment_contexts(repo):
    repo.env('c', 'one')
    repo.env('c', 'two')
    path = write(repo.root / 'environments/c/one/Inventory/credentials/shared.yml', {'one': {'type': 'secret'}})
    alias = repo.root / 'environments/c/two/Inventory/credentials/alias.yml'
    alias.parent.mkdir()
    alias.symlink_to(path)
    result = candidates(repo)
    assert len(result) == 1
    assert result[0].environments == ('c/one', 'c/two')
    assert set(result[0].aliases) == {path, alias}


def test_inventory_without_environment_definition(repo):
    path = write(repo.root / 'environments/c/orphan/Inventory/resource_profiles/small.yml', {'baseline': 'small'})
    result = candidates(repo)
    assert [(x.path, x.environments) for x in result] == [(path, ())]


def test_credential_case_alias_does_not_duplicate(repo):
    repo.env('c', 'e')
    path = write(repo.root / 'environments/credentials/catalog.yml', {'one': {'type': 'secret'}})
    if not (path.parent.parent / 'Credentials').exists():
        (path.parent.parent / 'Credentials').symlink_to(path.parent, target_is_directory=True)
    assert len(candidates(repo)) == 1


def test_implicit_inventory_credentials_are_excluded(repo):
    repo.env('c', 'e')
    write(repo.root / 'environments/c/e/Inventory/credentials/inventory_generation_creds.yml',
          {'implicit': {'type': 'secret'}})
    assert candidates(repo) == []


@pytest.mark.parametrize('target', ['external', '.git'])
def test_unsafe_candidate_alias_is_excluded(repo, tmp_path, target):
    repo.env('c', 'e')
    path = write((repo.root.parent / (repo.root.name + '-external.yml')) if target == 'external'
                 else repo.root / '.git/private.yml', {'one': {'type': 'secret'}})
    alias = repo.root / 'environments/credentials/alias.yml'
    alias.parent.mkdir()
    alias.symlink_to(path)
    assert candidates(repo) == []


def test_sops_metadata_is_not_credential_entry(repo):
    repo.env('c', 'e')
    write(repo.root / 'environments/credentials/shared.yml', {'sops': {'version': '3'}, 'real': {'type': 'secret'}})
    assert [x.name for x in candidates(repo)] == ['real']
