# jschon-sort — Legacy, Now an External Dependency

This directory contains only this file. On `main`, `python/jschon-sort/jschon_tools/` was a local package providing schema-ordered YAML/JSON key sorting.

In this branch `jschon_tools` is installed as a regular pip dependency (see `build_envgene/build/requirements.txt`) rather than built from local source — there is nothing to edit here. If you need to change sorting behavior, it must be done in the upstream `jschon-tools` package, not in this repo.

## How It's Used

`envgenehelper.yaml_helper.sortYaml()` calls `jschon_tools.process_json_doc(doc_data, schema_data, sort, remove_additional_props)`:
1. Validates the document against the JSON Schema (`jsonschema.validate`).
2. Walks the schema's `properties` order to build a path → sort-key map.
3. Reorders dict keys according to that map; additional properties sort last.
4. If `remove_additional_props=True`, strips keys not declared in the schema.

```python
from envgenehelper.yaml_helper import sortYaml
sortYaml(yaml_data, schema_path, remove_additional_props=False)
```
