from .yaml_helper import merge_yaml_into_target, readYaml, store_value_to_yaml


def test_merge_without_source_comment_allows_commented_insert():
    target = readYaml("A: 1\nB: 2  # from template\n")
    merge_yaml_into_target(target, '', readYaml("A: 10\nD: 4\n"))

    store_value_to_yaml(target, "C", 3, "paramset: ps")

    assert target == {"C": 3, "A": 10, "B": 2, "D": 4}
    assert "A" not in target.ca.items
    assert "D" not in target.ca.items
