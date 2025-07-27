import math
from typing import cast
from typing import Dict
from typing import List
from typing import Mapping
from typing import Sequence
from typing import Tuple

import jschon.jsonschema
from jschon.json import JSONCompatible


_END_SORT_KEY = (math.inf,)


def _get_sort_keys_for_json_nodes(root_node: jschon.JSON) -> Mapping[jschon.JSONPointer, Tuple[int, ...]]:
    """
    Gets a mapping from JSON nodes (as JSON pointers) to sort keys (as tuples of integers) that match their position
    within the JSON.
    """
    mapping = {}
    root_depth = len(root_node.path)

    def _recurse(node: jschon.JSON, node_sort_key: Tuple[int, ...]) -> None:
        relative_path = node.path[root_depth:]
        mapping[relative_path] = node_sort_key

        if node.type == "object":
            object_data = cast(Mapping[str, jschon.JSON], node.data)
            for idx, v in enumerate(object_data.values()):
                new_loc = (*node_sort_key, idx)
                _recurse(v, new_loc)
        elif node.type == "array":
            array_data = cast(Sequence[jschon.JSON], node.data)
            for idx, v in enumerate(array_data):
                new_loc = (*node_sort_key, idx)
                _recurse(v, new_loc)

    _recurse(root_node, ())

    return mapping


def _get_sort_keys_for_json_doc(
    *, root_result: jschon.jsonschema.Result
) -> Mapping[jschon.JSONPointer, Tuple[int, ...]]:
    schema_sort_keys_cache: Dict[jschon.URI, Mapping[jschon.JSONPointer, Tuple[int, ...]]] = {}

    def _get_sort_keys_for_schema(schema: jschon.JSONSchema) -> Mapping[jschon.JSONPointer, Tuple[int, ...]]:
        canonical_uri = schema.canonical_uri
        if canonical_uri is None:  # pragma: no cover
            raise ValueError('Schema must have a canonical URI')
        if sort_keys := schema_sort_keys_cache.get(canonical_uri):
            return sort_keys
        sort_keys = _get_sort_keys_for_json_nodes(schema)
        schema_sort_keys_cache[canonical_uri] = sort_keys
        return sort_keys

    doc_sort_keys: Dict[jschon.JSONPointer, Tuple[int, ...]] = {}

    def _traverse_result(result: jschon.jsonschema.Result) -> None:
        schema_sort_keys = _get_sort_keys_for_schema(result.schema)
        doc_sort_keys.setdefault(result.instance.path, schema_sort_keys[result.relpath])
        for child in result.children.values():
            _traverse_result(child)

    _traverse_result(root_result)

    return doc_sort_keys


def _get_root_result(doc_json: jschon.JSON, schema_data: Mapping[str, JSONCompatible]) -> jschon.jsonschema.Result:
    try:
        root_schema = jschon.JSONSchema(schema_data)
    except jschon.CatalogError:
        # jschon only supports newer jsonschema drafts
        schema_data = dict(schema_data)
        schema_data['$schema'] = "https://json-schema.org/draft/2020-12/schema"
        root_schema = jschon.JSONSchema(schema_data)
    res = root_schema.evaluate(doc_json)
    if not res.valid:
        raise ValueError('Document failed schema validation')
    return res


def process_json_doc(
    *,
    doc_data: JSONCompatible,
    schema_data: Mapping[str, JSONCompatible],
    sort: bool = False,
    remove_additional_props: bool = False,
) -> JSONCompatible:
    doc_json = jschon.JSON(doc_data)
    root_result = _get_root_result(doc_json, schema_data=schema_data)
    doc_sort_keys = _get_sort_keys_for_json_doc(root_result=root_result)

    def _traverse_node(node: JSONCompatible, json_node: jschon.JSON) -> JSONCompatible:
        """
        @param node: the node being traversed (the data)
        @param json_node: the node being traversed (jschon's representation)
        @return: sorted copy
        """
        if isinstance(node, Dict):
            object_data = cast(Mapping[str, jschon.JSON], json_node.data)
            key_sort_keys: Dict[str, Tuple[Tuple[float, ...], str]] = {}

            properties: List[Tuple[str, JSONCompatible]] = []

            k: str
            v: JSONCompatible
            v_json: jschon.JSON
            for (k, v), v_json in zip(node.items(), object_data.values()):
                v = _traverse_node(v, v_json)
                # Keys which don't map to the schema (e.g. undefined properties when additionalProperties is missing,
                # defaulting to true) are assumed to come last (end_sort_key).
                # As a tie breaker for multiple such undefined properties, we use the key's name.
                # TODO: update jschon to add additional properties to res.children when appropriate
                sk = doc_sort_keys.get(v_json.path, _END_SORT_KEY)
                if sk is not _END_SORT_KEY or not remove_additional_props:
                    key_sort_keys[k] = sk, k
                    properties.append((k, v))

            if sort:
                properties.sort(key=lambda pair: key_sort_keys[pair[0]])

            # to maintain YAML round-trip data, copy node and re-populate
            node_copy = node.copy()
            node_copy.clear()
            node_copy.update(properties)

            return node_copy

        elif isinstance(node, list):
            list_data = cast(Sequence[jschon.JSON], json_node.data)
            return [_traverse_node(node[idx], v_json) for idx, v_json in enumerate(list_data)]

        return node

    # we recurse down both the "JSON" and the actual document, and mutate only the actual document
    # which is the primitive type that we can serialize back to JSON/YAML easily
    return _traverse_node(doc_data, doc_json)
