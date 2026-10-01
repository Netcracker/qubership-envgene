"""Template-mode constants."""

SUPPORTED_CRED_TYPES = frozenset({"usernamePassword", "secret"})

ENVGENE_NULL = "envgeneNullValue"

# Template env-tier default (Jinja). No namespace segment — operator may add
# /{{ current_env.namespace }} via override when needed.
TEMPLATE_ENV_TIER_PATH = "{{ current_env.cloud }}/{{ current_env.name }}"
TEMPLATE_PASSPORT_PATH = "{{ current_env.cloud }}"
