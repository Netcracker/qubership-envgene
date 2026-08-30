"""Consumer-file macro parsing and rewriting.

Recognizes three equivalent forms of value macros:
- ${creds.get('<credId>').<field>}
- ${envgen.creds.get('<credId>').<field>}    (alias, envgen. prefix stripped)
- ${cmdb.creds.get('<credId>').<field>}      (alias, cmdb. prefix stripped)

And hash-style key macros (recognized here; key-vs-value handling lives in the file-walker):
- #creds{<credId>, <field>}
- #credscl{<credId>, <field>}
- #credsns{<credId>, <field>}

Rewrites value macros to a credRef structural mapping:
    {"$type": "credRef", "credId": "<credId>", "property": "<field>"}
    (property omitted when field == "secret" - single-value cred).

Composite values (macro embedded in a larger string) are unsupported by design because
credRef is structural, not textual substitution. Composite raises CompositeMacroError.
"""

import re

# Anchored value-macro pattern. Whitespace tolerant. Both quote styles accepted.
_VALUE_MACRO_RE = re.compile(
    r"""
    ^\s*
    \$\{
        \s*(?:envgen\.|cmdb\.)?creds\.get\s*
        \(\s*['"](?P<cred_id>[\w.-]+)['"]\s*\)\s*
        \.\s*(?P<field>\w+)\s*
    \}
    \s*$
    """,
    re.VERBOSE,
)

# Detect a creds macro anywhere in a string (for composite detection).
_ANY_MACRO_RE = re.compile(
    r"""\$\{\s*(?:envgen\.|cmdb\.)?creds\.get\s*\(\s*['"][\w.-]+['"]\s*\)\s*\.\s*\w+\s*\}"""
)

# Hash-style key macro: #creds{USERNAME_KEY, PASSWORD_KEY} (also #credscl, #credsns aliases).
_HASH_MACRO_KEY_RE = re.compile(
    r"^#creds(?:cl|ns)?\{\s*(?P<u_key>[^,\s]+)\s*,\s*(?P<p_key>[^}\s]+)\s*\}$"
)

_VALID_FIELDS = {"username", "password", "secret"}


class CompositeMacroError(ValueError):
    """Macro embedded in a larger string; credRef cannot express partial substitution."""


def rewrite_value(value):
    """Rewrite a YAML scalar to a credRef mapping if it is a creds macro.

    Non-string values and strings without a macro are returned unchanged.
    A macro that is only a fragment of a larger string raises CompositeMacroError.
    An unknown property raises ValueError.
    """
    if not isinstance(value, str):
        return value

    match = _VALUE_MACRO_RE.match(value)
    if match:
        field = match.group("field")
        if field not in _VALID_FIELDS:
            raise ValueError(f"unknown property {field!r}; expected one of {sorted(_VALID_FIELDS)}")
        result = {"$type": "credRef", "credId": match.group("cred_id")}
        if field != "secret":
            result["property"] = field
        return result

    if _ANY_MACRO_RE.search(value):
        raise CompositeMacroError(
            f"composite value contains an embedded creds macro that credRef cannot express: {value!r}"
        )

    return value


def rewrite_dict(mapping):
    """Rewrite an ordered dict of parameter entries.

    - Hash-macro keys (`#creds{U, P}: cred-id`) expand to two credRef entries (`U`, `P`) with
      properties `username` and `password`, in place at the original position.
    - Value macros (`${creds.get(...)}`) are rewritten via rewrite_value.
    - All other entries pass through unchanged, preserving insertion order.
    """
    out = {}
    for key, value in mapping.items():
        if isinstance(key, str):
            match = _HASH_MACRO_KEY_RE.match(key)
            if match:
                cred_id = value
                out[match.group("u_key")] = {
                    "$type": "credRef",
                    "credId": cred_id,
                    "property": "username",
                }
                out[match.group("p_key")] = {
                    "$type": "credRef",
                    "credId": cred_id,
                    "property": "password",
                }
                continue
        out[key] = rewrite_value(value)
    return out
