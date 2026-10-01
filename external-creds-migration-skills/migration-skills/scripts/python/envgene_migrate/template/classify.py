"""Classification signals → to_review / to_confirm + path/create suggestions."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# Prefix families → create:false / passport-shape in template_mode.
PLATFORM_SERVICE_RE = re.compile(
    r"^(dbaas|argocd|arango|cluster|consul|keycloak|maas|vault|k8s|kube|"
    r"webex|registry|gitlab|cmdb|atp|cloud|x_saas|"
    r"prometheus|harbor|aws|postgres|grafana|"
    r"kafka|zookeeper|elastic|elasticsearch|cassandra|rabbitmq|redis|opensearch"
    r")([-_].+)?$",
    re.IGNORECASE,
)

# Exact bare ids (no separator after the token) that still imply create:false.
BARE_CREATE_FALSE_IDS = frozenset(
    {
        "storage",
        "coreexternal",
        "maasexternal",
        "proxy",
        "smtp",
        "cdc",
        "apps",
        "cloud",
        "dbaas",
        "consul",
        "maas",
        "test",
    }
)

KEYWORD_SUBSTR = (
    "cluster",
    "admin",
    "dba",
    "root",
    "superuser",
    "bootstrap",
    "master",
)

COMMENT_MARKERS = (
    "cloud passport",
    "platform",
    "script generated",
    "manual",
    "shared across envs",
)


@dataclass
class Classification:
    tier: str  # passport | env | system | shared (location hint)
    remote_ref_path: str
    create: bool | None
    to_review: bool
    suggestions: list[str] = field(default_factory=list)
    write_to_store: bool = True


def _comment_hits(comment_text: str | None) -> list[str]:
    if not comment_text:
        return []
    lower = comment_text.lower()
    return [m for m in COMMENT_MARKERS if m in lower]


def classify_cred(
    cred_id: str,
    *,
    tier_from_location: str,
    default_path: str,
    default_create: bool | None,
    source_comment: str | None = None,
    template_mode: bool = False,
) -> Classification:
    """Combine signals. Any hit → to_review. Template + hit → passport-shape defaults."""
    suggestions: list[str] = []
    hit = False

    cid = cred_id or ""
    if cid.startswith("id_") or cid.startswith("ID_"):
        hit = True
        suggestions.append(
            "cred-id starts with id_/ID_ — suggest passport shape "
            "(remoteRefPath=<cluster>, create=false)"
        )

    if cid.lower() in BARE_CREATE_FALSE_IDS:
        hit = True
        suggestions.append(
            "cred-id is a known bare infra name — suggest passport shape "
            "(remoteRefPath=<cluster>, create=false)"
        )

    if PLATFORM_SERVICE_RE.match(cid):
        hit = True
        suggestions.append(
            "cred-id matches platform-service pattern — suggest passport shape "
            "(remoteRefPath=<cluster>, create=false)"
        )

    lower_id = (cred_id or "").lower()
    for kw in KEYWORD_SUBSTR:
        if kw in lower_id:
            hit = True
            suggestions.append(
                f"cred-id contains '{kw}' — shared-scope suspected; "
                "suggest remoteRefPath=<cluster>, create=false"
            )
            break

    for marker in _comment_hits(source_comment):
        hit = True
        suggestions.append(
            f"source comment mentions '{marker}' — classify accordingly"
        )

    # Signal 5 (cross-namespace consumer analysis): stub — do not fire.

    tier = tier_from_location
    path = default_path
    create = default_create

    if hit and template_mode:
        from .constants import TEMPLATE_PASSPORT_PATH

        tier = "passport"
        path = TEMPLATE_PASSPORT_PATH
        create = False
        suggestions.append(
            "looks like Cloud Passport cred; value comes from Instance Cloud Passport — "
            "remove from plan if EnvGene should not manage it, else keep passport shape"
        )

    return Classification(
        tier=tier,
        remote_ref_path=path,
        create=create,
        to_review=hit,
        suggestions=suggestions,
        write_to_store=True,
    )


def entry_fields(classification: Classification, *, instance: bool) -> dict[str, Any]:
    out: dict[str, Any] = {
        "remoteRefPath": classification.remote_ref_path,
    }
    if classification.create is not None:
        out["create"] = classification.create
    if instance:
        out["writeToStore"] = classification.write_to_store
    if classification.suggestions:
        out["suggestions"] = list(classification.suggestions)
    return out
