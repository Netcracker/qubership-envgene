import pytest
from ruyaml import CommentedMap

from .yaml_helper import openYaml, store_value_to_yaml, writeYamlToFile

CRED_VALUE = {'type': 'secret', 'data': {'secret': 'token'}}


def cred_path_in(tmp_path, name='credentials.yml'):
    path = tmp_path / 'environments' / 'cluster-01' / 'env-01' / 'Credentials' / name
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def assert_no_yaml_comments(path):
    for line in path.read_text().splitlines():
        if '#' in line:
            raise AssertionError(f"unexpected comment in credential file: {line!r}")


class TestCredentialYamlWithoutComments:
    @pytest.mark.unit
    def test_write_cred_file_has_no_comments(self, tmp_path):
        creds = CommentedMap()
        store_value_to_yaml(creds, 'consul-bootstrap-token', CRED_VALUE)

        cred_path = cred_path_in(tmp_path)
        writeYamlToFile(cred_path, creds)

        assert 'consul-bootstrap-token:' in cred_path.read_text()
        assert_no_yaml_comments(cred_path)

    @pytest.mark.unit
    def test_write_strips_existing_comments(self, tmp_path):
        cred_path = cred_path_in(tmp_path)
        cred_path.write_text(
            '# provenance comment\n'
            '# tenant prod\n'
            'token-a:\n'
            '  type: "secret"\n'
            '  data:\n'
            '    secret: "envgeneNullValue" # FillMe\n'
        )

        loaded = openYaml(cred_path)
        store_value_to_yaml(loaded, 'token-a', loaded['token-a'])
        writeYamlToFile(cred_path, loaded)

        assert_no_yaml_comments(cred_path)
