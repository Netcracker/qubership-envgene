"""Orphaned Shared credential detection.

Algorithm (per design doc):
1. Collect declared cred-ids from each Shared cred file.
2. Collect referenced cred-ids by walking consumer files.
3. A file is orphaned when every cred-id it declares is missing from the referenced set.
"""

import re

# Match cred-id inside ${creds.get('X').Y} / ${envgen.creds.get('X').Y} / ${cmdb.creds.get('X').Y}.
_VALUE_MACRO_CRED_RE = re.compile(
    r"""\$\{\s*(?:envgen\.|cmdb\.)?creds\.get\s*\(\s*['"](?P<cred_id>[\w.-]+)['"]"""
)

# Built-in cred fields on Cloud/Namespace/Tenant/BG-domain objects and nested configs.
_BUILTIN_CRED_FIELDS = {
    "credentialsId",
    "defaultCredentialsId",
    "tokenSecret",
    "credential",
    "credentials",
}

# Hash-macro key form (value is the cred-id).
_HASH_MACRO_KEY_RE = re.compile(r"^#creds(?:cl|ns)?\{[^}]*\}$")


def collect_declared_from_cred_file(cred_yaml):
    """Return the set of cred-ids declared as top-level keys in a Shared cred file."""
    if not cred_yaml:
        return set()
    return set(cred_yaml.keys())


def collect_referenced_from_consumer(consumer_yaml):
    """Walk a consumer YAML and collect all referenced cred-ids.

    Recognized reference forms:
    - value macros: `${creds.get('X').Y}`, `${envgen.creds.get(...)}`, `${cmdb.creds.get(...)}`
    - hash-macro keys: `#creds{U, P}` (value is cred-id)
    - built-in cred fields: `credentialsId`, `defaultCredentialsId`, `tokenSecret`, `credential`,
      `credentials` (value is cred-id)
    - `$type: credRef` mapping: reads its `credId` field
    """
    found = set()
    _walk(consumer_yaml, found)
    return found


def _walk(node, found):
    if isinstance(node, dict):
        # $type: credRef mapping - extract credId, no further descent needed for this node's shape.
        if node.get("$type") == "credRef" and "credId" in node:
            found.add(node["credId"])
            return
        for key, value in node.items():
            # Hash-macro key: value is the cred-id (string).
            if isinstance(key, str) and _HASH_MACRO_KEY_RE.match(key):
                if isinstance(value, str):
                    found.add(value)
                continue
            # Built-in cred field: value is the cred-id (string).
            if key in _BUILTIN_CRED_FIELDS and isinstance(value, str):
                found.add(value)
                continue
            _walk(value, found)
    elif isinstance(node, list):
        for item in node:
            _walk(item, found)
    elif isinstance(node, str):
        for m in _VALUE_MACRO_CRED_RE.finditer(node):
            found.add(m.group("cred_id"))


def compute_orphaned_files(declared_by_file, referenced):
    """Return set of file paths whose declared cred-ids are all missing from `referenced`."""
    orphans = set()
    for path, declared_ids in declared_by_file.items():
        if not declared_ids:
            orphans.add(path)
            continue
        if declared_ids.isdisjoint(referenced):
            orphans.add(path)
    return orphans
