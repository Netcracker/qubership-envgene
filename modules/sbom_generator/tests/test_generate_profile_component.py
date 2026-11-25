import base64
import json
import logging

import pytest
import yaml
from envgenehelper import logger
from sbom_generator.generate_bom import generate_profile_component


@pytest.mark.parametrize('filename', ['.gitkeep', 'LICENSE', 'README.md', 'dev.yaml.bak', 'dev.notyaml'])
def test_generate_profile_component_skips_non_profiles(tmp_path, caplog, monkeypatch, filename):
    profile_dir = tmp_path / 'charts' / 'sample-api' / 'resource-profiles'
    profile_dir.mkdir(parents=True)
    (profile_dir / filename).write_text('not a resource profile', encoding='utf-8')
    profile_contents = {
        'dev.yaml': 'REPLICAS: 1\n',
        'prod.yml': 'REPLICAS: 3\n',
        'test.json': '{"REPLICAS": 2}',
    }
    for profile_name, content in profile_contents.items():
        (profile_dir / profile_name).write_text(content, encoding='utf-8')
    monkeypatch.setattr(logger, 'propagate', True)

    component = generate_profile_component(tmp_path, 'sample-api')

    assert [profile['name'] for profile in component.data] == sorted(profile_contents)
    for profile in component.data:
        attachment = profile['contents']['attachment']
        decoded = base64.b64decode(attachment['content']).decode('utf-8')
        loader = json.loads if profile['name'].endswith('.json') else yaml.safe_load
        assert loader(decoded) == loader(profile_contents[profile['name']])
    assert [record.levelno for record in caplog.records] == [logging.WARNING]


def test_generate_profile_component_omits_component_for_only_non_profiles(tmp_path, caplog, monkeypatch):
    profile_dir = tmp_path / 'charts' / 'sample-api' / 'resource-profiles'
    profile_dir.mkdir(parents=True)
    (profile_dir / '.gitkeep').touch()
    monkeypatch.setattr(logger, 'propagate', True)

    assert generate_profile_component(tmp_path, 'sample-api') is None
    assert [record.levelno for record in caplog.records] == [logging.WARNING]


@pytest.mark.parametrize('suffix', ['.json', '.yaml', '.yml'])
def test_generate_profile_component_rejects_malformed_profiles(tmp_path, suffix):
    profile_dir = tmp_path / 'charts' / 'sample-api' / 'resource-profiles'
    profile_dir.mkdir(parents=True)
    (profile_dir / f'dev{suffix}').write_text('{', encoding='utf-8')
    error = json.JSONDecodeError if suffix == '.json' else yaml.YAMLError

    with pytest.raises(error):
        generate_profile_component(tmp_path, 'sample-api')
