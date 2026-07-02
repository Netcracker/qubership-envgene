# jschon-sort — JSON Schema-Ordered YAML Sorting

Sorts YAML/JSON document keys to match the property order declared in a JSON Schema. Used by `envgenehelper.yaml_helper.sortYaml()` to keep generated files stable across runs.

## Files

| File | Responsibility |
|------|---------------|
| `jschon_tools/_main.py` | `process_json_doc(doc_data, schema_data, sort, remove_additional_props)` — validates doc against schema, builds a path→sort-key map from the schema evaluation tree, then reorders keys; additional properties get sort key `(math.inf,)` so they appear last |
| `jschon_tools/_yaml.py` | YAML I/O helpers used by the CLI |
| `jschon_tools/cli.py` | CLI entry point |

## How It Works

1. Load schema with `jschon.create_catalog('2020-12')`.
2. Validate the document — produces a result tree with property-order metadata.
3. Walk the result tree to map each key path → its index in the schema's `properties` list.
4. Recursively reorder dict keys according to that map.
5. If `remove_additional_props=True`, strip keys not in the schema.

## Usage from envgenehelper

```python
from envgenehelper.yaml_helper import sortYaml
sortYaml(yaml_data, schema_path, remove_additional_props=False)
```
