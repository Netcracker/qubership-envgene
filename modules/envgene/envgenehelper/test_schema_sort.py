import json
from pathlib import Path

import jschon_tools
import pytest
import ruyaml

from envgenehelper.schema_sort import sort_by_schema

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMAS_DIR = REPO_ROOT / 'schemas'
TEST_DATA_DIR = REPO_ROOT / 'test_data'

SCHEMA_AND_DOC = [
    ('resource-profile', 'test_environments/cluster-01/env-01/Profiles/prod_billing_override.yml'),
    ('namespace', 'build_env/tmp/initial_namespaces_content/Namespaces/bg-controller/namespace.yml'),
    ('application', 'build_env/tmp/initial_namespaces_content/Namespaces/origin-app/Applications/crm.yml'),
]


def load_doc(doc_path):
    return ruyaml.YAML().load((TEST_DATA_DIR / doc_path).read_text())


@pytest.mark.parametrize('remove_additional_props', [False, True])
@pytest.mark.parametrize('schema_name, doc_path', SCHEMA_AND_DOC)
def test_sort_by_schema_matches_jschon_tools(schema_name, doc_path, remove_additional_props):
    schema_path = SCHEMAS_DIR / f'{schema_name}.schema.json'
    expected = jschon_tools.process_json_doc(
        schema_data=json.loads(schema_path.read_text()),
        doc_data=load_doc(doc_path),
        sort=True,
        remove_additional_props=remove_additional_props,
    )

    actual = sort_by_schema(load_doc(doc_path), schema_path, remove_additional_props)

    assert json.dumps(actual) == json.dumps(expected)


def test_sort_by_schema_is_repeatable_with_cached_schema():
    schema_path = SCHEMAS_DIR / 'namespace.schema.json'
    doc_path = SCHEMA_AND_DOC[1][1]

    first = sort_by_schema(load_doc(doc_path), schema_path)
    second = sort_by_schema(load_doc(doc_path), schema_path)

    assert json.dumps(first) == json.dumps(second)


def test_sort_by_schema_rejects_invalid_doc():
    schema_path = SCHEMAS_DIR / 'namespace.schema.json'

    with pytest.raises(ValueError):
        sort_by_schema({'name': 1}, schema_path)
