import json
from pathlib import Path

import pytest

from envgene_linter.yamlio import YamlReadError, dotted, leaves, load, plain


def test_load_reports_key_line(tmp_path: Path):
    path = tmp_path / "params.yml"
    path.write_text("parameters:\n  MONITORING_URL: https://m.example.com\n", encoding="utf-8")
    loaded = load(path)
    assert loaded.position(("parameters", "MONITORING_URL")) == (2, 3)


def test_leaves_walks_nested_maps():
    assert leaves({"a": {"b": 1}, "c": [2]}) == [(("a", "b"), 1), (("c",), [2])]


def test_dotted_joins_path():
    assert dotted(("deploy", "LOG_LEVEL")) == "deploy.LOG_LEVEL"


def test_plain_strips_ruamel_types(tmp_path: Path):
    path = tmp_path / "x.yml"
    path.write_text("k: v\n", encoding="utf-8")
    value = plain(load(path).doc)
    assert value == {"k": "v"}
    assert type(value) is dict


def test_bad_yaml_raises(tmp_path: Path):
    path = tmp_path / "bad.yml"
    path.write_text("[:\n", encoding="utf-8")
    with pytest.raises(YamlReadError):
        load(path)


def test_non_utf8_raises_yaml_read_error(tmp_path: Path):
    path = tmp_path / "bad.yml"
    path.write_bytes(b"\xff\xfe parameters:\n")
    with pytest.raises(YamlReadError):
        load(path)


@pytest.mark.parametrize('text', [
    'parameters:\n  VALUE: 1\n', '{"parameters": {"VALUE": 1,}}', '# comment\n{"parameters": {}}',
])
def test_json_rejects_yaml_only_syntax(tmp_path: Path, text):
    path = tmp_path / 'params.json'
    path.write_text(text, encoding='utf-8')
    with pytest.raises(YamlReadError):
        load(path)


def test_json_uses_native_decoded_values_and_key_positions(tmp_path: Path):
    path = tmp_path / 'params.json'
    path.write_text('''{
  "parameters": {
    "FLOAT": 1.0,
    "INT": 1,
    "BOOL": true,
    "NULL": null,
    "TEXT": "line\\nquote\\\"slash\\/",
    "escaped\\u005fkey": {"VALUE": 2}
  },
  "applications": [
    {"appName": "app", "parameters": {"PASSWORD": "synthetic"}}
  ]
}''', encoding='utf-8')
    document = load(path)
    values = document.doc['parameters']
    assert type(values) is dict
    assert type(values['FLOAT']) is float and values['FLOAT'] == 1.0
    assert type(values['INT']) is int and values['INT'] == 1
    assert values['BOOL'] is True and values['NULL'] is None
    assert type(values['TEXT']) is str and values['TEXT'] == 'line\nquote"slash/'
    assert document.position(('parameters', 'FLOAT')) == (3, 5)
    assert document.position(('parameters', 'escaped_key', 'VALUE')) == (8, 26)
    assert document.position(('applications', 0, 'parameters', 'PASSWORD')) == (11, 39)


def test_json_duplicate_keys_keep_last_value_and_last_subtree_positions(tmp_path: Path):
    path = tmp_path / 'params.json'
    path.write_text('''{
  "parameters": {"REMOVED": {"LEAF": 1}},
  "parameters": {
    "VALUE": "first",
    "VALUE": "last"
  }
}''', encoding='utf-8')
    document = load(path)
    assert document.doc == {'parameters': {'VALUE': 'last'}}
    assert document.position(('parameters',)) == (3, 3)
    assert document.position(('parameters', 'VALUE')) == (5, 5)
    assert document.position(('parameters', 'REMOVED', 'LEAF')) == (3, 3)


def test_json_accepts_tab_whitespace_without_shifting_columns(tmp_path: Path):
    path = tmp_path / 'params.json'
    path.write_text('{\n\t"parameters": {\n\t\t"VALUE": 1\n\t}\n}', encoding='utf-8')
    document = load(path)
    assert document.doc == {'parameters': {'VALUE': 1}}
    assert document.position(('parameters', 'VALUE')) == (3, 3)


@pytest.mark.parametrize('key,ensure_ascii', [('😀', True), ('line\u0085key', False), ('line\u2028key', False)])
def test_json_unicode_keys_keep_json_positions(tmp_path: Path, key, ensure_ascii):
    path = tmp_path / 'params.json'
    encoded = json.dumps(key, ensure_ascii=ensure_ascii)
    path.write_text('{"parameters": {\n  ' + encoded + ': {"VALUE": 1}}}', encoding='utf-8')
    document = load(path)
    assert document.doc == {'parameters': {key: {'VALUE': 1}}}
    assert document.position(('parameters', key)) == (2, 3)
