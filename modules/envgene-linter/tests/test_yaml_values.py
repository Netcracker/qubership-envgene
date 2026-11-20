from ruamel.yaml import YAML

import pytest


@pytest.mark.parametrize(('left', 'right', 'expected'), [
    ('true', '1', False),
    ('false', '0', False),
    ('1', '1.0', False),
    ('"1"', '1', False),
    ('info', '"info"', True),
    ("'info'", '"info"', True),
    ('0x10', '16', True),
    ('1.00', '1.0', True),
    ('null', '~', True),
    ('[]', '[]', True),
    ('[true]', '[1]', False),
    ('[{flag: true}]', '[{flag: 1}]', False),
    ('[1, 2]', '[2, 1]', False),
    ('{a: 1, b: false}', '{b: false, a: 1}', True),
    ('{true: value}', '{1: value}', False),
    ('{1: value}', '{1.0: value}', False),
    ('{a: {}}', '{}', False),
    ('&value true', '1', False),
    ('&value true', 'true', True),
    ('.nan', '.nan', None),
    ('!custom value', '!custom value', None),
    ('!custom [1]', '[1]', None),
    ('!custom {a: 1}', '{a: 1}', None),
    ('!custom [1]', '!custom [1]', None),
    ('{a: !custom [1]}', '{a: [1]}', None),
    ('!!seq [1]', '[1]', True),
    ('!!map {a: 1}', '{a: 1}', True),
])
def test_yaml_value_comparison_preserves_types_and_collection_structure(left, right, expected):
    from envgene_linter.yaml_values import equal

    yaml = YAML()
    assert equal(yaml.load(left), yaml.load(right)) is expected


def test_cyclic_values_have_no_confirmed_equality():
    from envgene_linter.yaml_values import equal

    left, right = [], []
    left.append(left)
    right.append(right)
    assert equal(left, right) is None
