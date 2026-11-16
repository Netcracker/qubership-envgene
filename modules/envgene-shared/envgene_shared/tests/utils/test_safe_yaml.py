import datetime
from pathlib import Path

import pytest

from envgene_shared.utils.yaml_utils import readYaml

REPO_ROOT = Path(__file__).resolve().parents[5]
SCALAR_TYPES = (bool, int, float, str, datetime.datetime, datetime.date, type(None))


def plain(data):
    if isinstance(data, dict):
        return {key: plain(value) for key, value in data.items()}
    if isinstance(data, list):
        return [plain(value) for value in data]
    scalar_type = next(t for t in SCALAR_TYPES if isinstance(data, t))
    return scalar_type, data


def corpus():
    for path in sorted((REPO_ROOT / "test_data").rglob("*.y*ml")):
        text = path.read_text(encoding="utf-8")
        if "{{" in text or "{%" in text:
            continue
        yield path, text


@pytest.mark.unit
@pytest.mark.parametrize("value", ["yes", "on", "no", "0755", "0o755", "010", "1e3", "12:30", "1_000", "2024-01-01",
                                   "1.10", "null", "~", "true", '"5"'])
def test_safe_and_round_trip_load_same_scalars(value):
    text = f"key: {value}\n"

    assert plain(readYaml(text, safe_load=True)) == plain(readYaml(text))


@pytest.mark.unit
def test_safe_and_round_trip_load_same_test_data():
    checked = 0
    for path, text in corpus():
        try:
            expected = plain(readYaml(text))
        except Exception:
            continue
        assert plain(readYaml(text, safe_load=True)) == expected, path
        checked += 1

    assert checked > 100


@pytest.mark.unit
def test_safe_load_returns_plain_dict():
    data = readYaml("a:\n  b: [1, 2]\n", safe_load=True)

    assert type(data) is dict
    assert type(data["a"]["b"]) is list
