"""Shared constants for External Credentials migration scripts."""

from __future__ import annotations

import re

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_NEEDS_INPUT = 2

CREDS_GET_RE = re.compile(
    r"""\$\{(?:creds|envgen\.creds|cmdb\.creds)\.get\(['"]([^'"]+)['"]\)"""
    r"""\.(username|password|secret)\}"""
)
HASH_CREDS_RE = re.compile(r"^#(creds|credscl|credsns)\{([^}]+)\}$")

TECHNICAL_KEYS = frozenset({"technicalConfigurationParameters"})

BUILTIN_FIELD_NAMES = frozenset(
    {
        "credentialsId",
        "defaultCredentialsId",
        "tokenSecret",
        "credential",
    }
)

DEFAULT_SECRET_STORE = "default_store"
DEFAULT_TEMPLATE_PATH = "{{ current_env.cloud }}/{{ current_env.name }}"
NAMESPACE_JINJA = "{{ current_env.namespace }}"

PROVIDER_MARKERS = (
    "consul",
    "dbaas",
    "argocd",
    "arango",
    "webex",
    "operator",
    "service-account",
    "service_account",
    "serviceaccount",
    "bootstrap",
)

SUPPORTED_LOCAL_TYPES = frozenset({"usernamePassword", "secret"})
UNSUPPORTED_LOCAL_TYPES = frozenset({"vaultAppRole", "sshPrivateKey"})
STUB_VALUES = frozenset({"", "envgeneNullValue", "null"})
