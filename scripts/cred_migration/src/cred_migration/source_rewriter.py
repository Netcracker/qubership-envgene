"""Source cred entry rewriter: transforms `type: usernamePassword` / `secret` to `type: external`.

- `properties` is derived from the source `data` keys (skipped for single-value secrets).
- `data` is removed.
- Unsupported cred types raise UnsupportedCredTypeError (initial impl supports usernamePassword
  and secret only).
- Already-`type: external` source entry raises PartialMigrationError (per Consistency validation
  rule #6).
"""

_SUPPORTED_TYPES = {"usernamePassword", "secret"}


class UnsupportedCredTypeError(ValueError):
    """Raised when a source cred entry has a type not supported by migration."""


class PartialMigrationError(ValueError):
    """Raised when a source cred entry is already `type: external` (partial migration)."""


def derive_properties(source_data):
    """Return a properties list for multi-field creds, None for single-value.

    - dict with keys other than the sole 'secret' → [{"name": <key>}, ...]
    - dict with only 'secret' key → None
    - scalar (string) → None
    """
    if isinstance(source_data, dict):
        keys = list(source_data.keys())
        if keys == ["secret"]:
            return None
        return [{"name": key} for key in keys]
    return None


def rewrite_source_entry(source_entry, plan_entry, omit_create_when_false=False):
    """Rewrite one cred entry to `type: external` form.

    - source_entry: original {type, data, ...} mapping from the cred file.
    - plan_entry: {remoteRefPath, create, ...} from the migration plan.
    - omit_create_when_false: if True and create=false, omit the `create` key (external-tier
      convention).
    """
    source_type = source_entry.get("type")
    if source_type == "external":
        raise PartialMigrationError(
            "source cred entry is already `type: external` (partial migration); "
            "remove from plan or restore source before re-running apply"
        )
    if source_type not in _SUPPORTED_TYPES:
        raise UnsupportedCredTypeError(
            f"unsupported cred type {source_type!r}; migration supports {sorted(_SUPPORTED_TYPES)}"
        )

    new_entry = {
        "type": "external",
        "remoteRefPath": plan_entry["remoteRefPath"],
    }
    create = plan_entry.get("create", False)
    if not (omit_create_when_false and create is False):
        new_entry["create"] = create

    props = derive_properties(source_entry.get("data"))
    if props is not None:
        new_entry["properties"] = props
    return new_entry
