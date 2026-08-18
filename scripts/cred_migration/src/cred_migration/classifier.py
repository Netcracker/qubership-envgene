"""Cred classification: tier assignment by source path + shadow-platform heuristics.

See `docs/analysis/cred-migration-flow.md`:
- Credential types section defines the three tiers (passport, env, external) and
  file-location rules.
- Classification algorithm section defines the four signal families.
"""

import enum
import re

from .known_creds import KNOWN_CLOUD_PASSPORT_CRED_IDS


class Tier(enum.Enum):
    PASSPORT = "passport-tier"
    ENV = "env-tier"
    EXTERNAL = "external-tier"


# ---- Tier assignment by file-location rules ----

_TIER_RULES = [
    # passport-tier: environments/<cluster>/cloud-passport/*-creds.yml
    (re.compile(r"^environments/[^/]+/cloud-passport/[^/]+-creds\.ya?ml$"), Tier.PASSPORT),
    # env-tier: Credential Template
    (re.compile(r"^templates/env_templates/.+/external-credentials\.yml\.j2$"), Tier.ENV),
    # env-tier: Env-scoped Shared cred (environments/<cluster>/<env>/Inventory/credentials/*.yml)
    (re.compile(r"^environments/[^/]+/[^/]+/Inventory/credentials/.+\.ya?ml$"), Tier.ENV),
    # external-tier: repo-scoped Shared cred (environments/credentials/*.yml)
    (re.compile(r"^environments/credentials/[^/]+\.ya?ml$"), Tier.EXTERNAL),
    # external-tier: cluster-scoped Shared cred (environments/<cluster>/credentials/*.yml)
    (re.compile(r"^environments/[^/]+/credentials/[^/]+\.ya?ml$"), Tier.EXTERNAL),
    # external-tier: System Credentials (configuration/credentials/*.yml)
    (re.compile(r"^configuration/credentials/[^/]+\.ya?ml$"), Tier.EXTERNAL),
]


def classify_tier_by_source_file(source_file):
    """Return the Tier for a given source-file path (repo-relative)."""
    for pattern, tier in _TIER_RULES:
        if pattern.match(source_file):
            return tier
    raise ValueError(f"unknown source-file path {source_file!r}; no tier match")


# ---- Shadow-platform heuristics ----

_PLATFORM_PATTERN = re.compile(
    r"^(dbaas|argocd|arango|cluster|consul|keycloak|maas|vault|k8s|kube)(?:[-_].+)?$",
    re.IGNORECASE,
)

_KEYWORDS = ("cluster", "admin", "dba", "root", "superuser", "bootstrap", "master")

_COMMENT_MARKERS = (
    "cloud passport",
    "platform",
    "script generated",
    "manual",
    "shared across envs",
)


def matches_platform_pattern(cred_id):
    """True if cred-id matches a known shadow-platform-service pattern."""
    return bool(_PLATFORM_PATTERN.match(cred_id))


def has_keyword_substring(cred_id):
    """True if cred-id contains a shared-scope keyword (case-insensitive)."""
    lowered = cred_id.lower()
    return any(keyword in lowered for keyword in _KEYWORDS)


def parse_comment_marker(comment):
    """Return the matched marker phrase if the comment contains one, else None."""
    if not comment:
        return None
    lowered = comment.lower()
    for marker in _COMMENT_MARKERS:
        if marker in lowered:
            return marker
    return None


def is_known_cloud_passport_cred(cred_id):
    """True if cred-id is in the registry of known Cloud Passport cred-ids.

    Registry sourced from real EnvGene instance repos (see known_creds.py).
    """
    return cred_id in KNOWN_CLOUD_PASSPORT_CRED_IDS


def build_signals(cred_id, comment):
    """Compose the list of shadow-platform signals fired for a cred entry.

    Empty list means the entry lands in `to_confirm`; non-empty routes it to `to_review`.
    """
    signals = []
    if is_known_cloud_passport_cred(cred_id):
        signals.append("cred-id in Cloud Passport registry")
    if matches_platform_pattern(cred_id):
        signals.append("cred-id matches platform pattern")
    if has_keyword_substring(cred_id):
        signals.append("cred-id contains shared-scope keyword")
    marker = parse_comment_marker(comment)
    if marker:
        signals.append(f"comment marker: {marker}")
    return signals
