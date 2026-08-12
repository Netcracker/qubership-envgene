import threading

import pytest
from ruyaml import CommentedMap

from envgene_shared.utils.yaml_utils import openYaml, readYaml, writeYamlToFile


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
        creds = CommentedMap({
            'consul-bootstrap-token': CommentedMap({
                'type': 'secret',
                'data': CommentedMap({
                    'secret': 'token'
                })
            })
        })

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
        writeYamlToFile(cred_path, loaded)

        assert_no_yaml_comments(cred_path)


class TestYamlThreadSafety:
    @pytest.mark.unit
    def test_concurrent_load_and_dump(self):
        errors = []
        results = []

        def worker(index: int) -> None:
            try:
                data = readYaml(f"key_{index}: value_{index}\n")
                assert data[f"key_{index}"] == f"value_{index}"
                results.append(index)
            except Exception as exc:
                errors.append((index, exc))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(20)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert not errors, f"Concurrent YAML operations raised errors: {errors}"
        assert len(results) == 20
