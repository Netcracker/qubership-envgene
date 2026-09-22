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
