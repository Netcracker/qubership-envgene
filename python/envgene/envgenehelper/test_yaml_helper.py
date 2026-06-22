import pytest
from ruyaml import CommentedMap

from .yaml_helper import store_value_to_yaml, writeYamlToFile

COMMENT = 'cloud passport: test version: 0'
CRED_VALUE = {'type': 'secret', 'data': {'secret': 'token'}}


class TestStoreValueToYaml:
    @pytest.mark.unit
    def test_adds_comment_above_key(self, tmp_path):
        creds = CommentedMap()
        store_value_to_yaml(creds, 'consul-bootstrap-token', CRED_VALUE, COMMENT)

        cred_path = tmp_path / 'credentials.yml'
        writeYamlToFile(cred_path, creds)
        rendered = cred_path.read_text()
        assert f'# {COMMENT}\nconsul-bootstrap-token:' in rendered
