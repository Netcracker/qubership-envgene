import math
from functools import lru_cache

import jschon
from envgene_shared.utils.yaml_utils import load_schema

END_SORT_KEY = (math.inf,)
schema_sort_keys_by_uri = {}


@lru_cache(maxsize=None)
def get_jschon_schema(schema_path):
    schema_data = load_schema(schema_path)
    try:
        return jschon.JSONSchema(schema_data)
    except jschon.CatalogError:
        return jschon.JSONSchema({**schema_data, '$schema': 'https://json-schema.org/draft/2020-12/schema'})


def build_node_sort_keys(root_node):
    sort_keys_by_path = {}
    root_depth = len(root_node.path)

    def collect(node, node_sort_key):
        sort_keys_by_path[node.path[root_depth:]] = node_sort_key
        if node.type == 'object':
            children = node.data.values()
        elif node.type == 'array':
            children = node.data
        else:
            return
        for idx, child in enumerate(children):
            collect(child, (*node_sort_key, idx))

    collect(root_node, ())
    return sort_keys_by_path


def get_schema_sort_keys(schema):
    uri = schema.canonical_uri
    if uri not in schema_sort_keys_by_uri:
        schema_sort_keys_by_uri[uri] = build_node_sort_keys(schema)
    return schema_sort_keys_by_uri[uri]


def build_doc_sort_keys(root_result):
    doc_sort_keys = {}

    def collect(result):
        doc_sort_keys.setdefault(result.instance.path, get_schema_sort_keys(result.schema)[result.relpath])
        for child in result.children.values():
            collect(child)

    collect(root_result)
    return doc_sort_keys


def sort_by_schema(doc_data, schema_path, remove_additional_props=False):
    doc_json = jschon.JSON(doc_data)
    root_result = get_jschon_schema(str(schema_path)).evaluate(doc_json)
    if not root_result.valid:
        raise ValueError('Document failed schema validation')
    doc_sort_keys = build_doc_sort_keys(root_result)

    def traverse(node, json_node):
        if isinstance(node, dict):
            properties = []
            for (key, value), value_json in zip(node.items(), json_node.data.values()):
                sort_key = doc_sort_keys.get(value_json.path, END_SORT_KEY)
                if sort_key is not END_SORT_KEY or not remove_additional_props:
                    properties.append(((sort_key, key), key, traverse(value, value_json)))
            properties.sort(key=lambda item: item[0])
            node_copy = node.copy()
            node_copy.clear()
            node_copy.update((key, value) for _, key, value in properties)
            return node_copy
        if isinstance(node, list):
            return [traverse(item, item_json) for item, item_json in zip(node, json_node.data)]
        return node

    return traverse(doc_data, doc_json)
