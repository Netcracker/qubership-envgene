"""Shared helpers for External Credentials migration scripts."""

from extcreds_mig.constants import (
    CREDS_GET_RE,
    DEFAULT_SECRET_STORE,
    DEFAULT_TEMPLATE_PATH,
    EXIT_ERROR,
    EXIT_NEEDS_INPUT,
    EXIT_OK,
    HASH_CREDS_RE,
    PROVIDER_MARKERS,
    TECHNICAL_KEYS,
)
from extcreds_mig.emit import emit
from extcreds_mig.macros import (
    base_external_entry,
    collect_referenced_cred_ids,
    find_macro_issues,
    find_remaining_macros,
    heuristic_provider_markers,
    path_contains_cred_id,
    walk_replace_macros,
)
from extcreds_mig.yaml_io import dump_yaml, load_yaml

__all__ = [
    "CREDS_GET_RE",
    "DEFAULT_SECRET_STORE",
    "DEFAULT_TEMPLATE_PATH",
    "EXIT_ERROR",
    "EXIT_NEEDS_INPUT",
    "EXIT_OK",
    "HASH_CREDS_RE",
    "PROVIDER_MARKERS",
    "TECHNICAL_KEYS",
    "base_external_entry",
    "collect_referenced_cred_ids",
    "dump_yaml",
    "emit",
    "find_macro_issues",
    "find_remaining_macros",
    "heuristic_provider_markers",
    "load_yaml",
    "path_contains_cred_id",
    "walk_replace_macros",
]
