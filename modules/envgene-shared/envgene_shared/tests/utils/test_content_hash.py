import datetime

import pytest

from envgene_shared.utils.content_hash import canonical_hash
from envgene_shared.utils.yaml_utils import readYaml


@pytest.mark.unit
def test_hash_ignores_key_order():
    assert canonical_hash(readYaml("a: 1\nb: [1, 2]\n")) == canonical_hash({"b": [1, 2], "a": 1})


@pytest.mark.unit
def test_hash_accepts_mixed_key_types():
    assert canonical_hash({1: "a", "b": "c"}) != canonical_hash({1: "a", "b": "d"})


@pytest.mark.unit
def test_hash_accepts_dates():
    assert canonical_hash({"d": datetime.date(2024, 1, 1)}) != canonical_hash({"d": datetime.date(2024, 1, 2)})
