from .collections_helper import *

def convert_list_elements_to_strings_in_place(lst):
    for i in range(len(lst)):
        lst[i] = str(lst[i])

def test_compare_dicts():
    # Test Case 1: Identical dictionaries
    source = {'a': 1, 'b': 2}
    target = {'a': 1, 'b': 2}
    diff, removed = compare_dicts(source, target)
    assert diff == [] and removed == [], f"Failed Test 1: {diff}, {removed}"

    # Test Case 2: Simple difference in dictionaries
    source = {'a': 1, 'b': 2}
    target = {'a': 1, 'b': 3}
    diff, removed = compare_dicts(source, target)
    assert diff == [['b']] and removed == [], f"Failed Test 2: {diff}, {removed}"

    # Test Case 3: Missing key in target
    source = {'a': 1, 'b': 2}
    target = {'a': 1}
    diff, removed = compare_dicts(source, target)
    assert diff == [] and removed == [['b']], f"Failed Test 3: {diff}, {removed}"

    # Test Case 4: Nested dictionaries
    source = {'a': 1, 'b': {'c': 2}}
    target = {'a': 1, 'b': {'c': 3}}
    diff, removed = compare_dicts(source, target)
    assert diff == [['b', 'c']] and removed == [], f"Failed Test 4: {diff}, {removed}"

    # Test Case 5: List difference
    source = [1, 2, 3]
    target = [1, 2, 4]
    diff, removed = compare_dicts(source, target)
    assert diff == [[2]] and removed == [], f"Failed Test 5: {diff}, {removed}"

    # Test Case 6: List with missing elements in target
    source = [1, 2, 3]
    target = [1, 2]
    diff, removed = compare_dicts(source, target)
    assert diff == [] and removed == [[2]], f"Failed Test 6: {diff}, {removed}"

    # Test Case 7: Complete difference between lists
    source = [1, 2]
    target = [3, 4]
    diff, removed = compare_dicts(source, target)
    assert diff == [[0], [1]] and removed == [], f"Failed Test 7: {diff}, {removed}"

    # Test Case 8: Complex nested dictionaries and lists
    source = {'a': [1, {'b': 2}], 'c': 3}
    target = {'a': [1, {'b': 4}], 'c': 3, 'd': 5}
    expected_arr = [['d'], ['a', 1, 'b']]
    diff, removed = compare_dicts(source, target)

    convert_list_elements_to_strings_in_place(diff)
    convert_list_elements_to_strings_in_place(expected_arr)
    s_diff = set(diff) # to compare regardless of the order of elements in a list

    assert len(s_diff) == len(diff) # no duplicates
    assert s_diff == set(expected_arr) and removed == [], f"Failed Test 8: {diff}, {removed}"
