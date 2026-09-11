"""Shared helper for VALS URI construction and secret-name normalization.

Mirrors the Java contract in
`build_effective_set_generator/vals-reference-core/.../SecretNameBuilder.java`
and `commons/.../ExternalCredUtils.java::buildValsUriWithoutFragment`.

Both migration and future EnvGene Python callers consume this module.
"""

import hashlib
import math
import re

VAULT_PATTERN = re.compile(r"^[a-zA-Z0-9/_-]+$")
AZURE_PATTERN = re.compile(r"^[a-zA-Z0-9-]+$")
AWS_PATTERN = re.compile(r"^[a-zA-Z0-9\-/_+=.@!]+$")
GCP_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")

MAX_CRED_ID_LENGTH = 32
AZURE_SEGMENT_MAX = 20
AWS_SEGMENT_MAX = 119
GCP_SEGMENT_MAX = 53
AZURE_MAX_LENGTH = 127
AWS_MAX_LENGTH = 512
GCP_MAX_LENGTH = 255

# Per-store normalization + validation profiles for normalize_secret_name.
# Fields: segment_max, max_segments, delimiter, pattern, total_max.
_STORE_PROFILES = {
    "azure": (AZURE_SEGMENT_MAX, 4, "--", AZURE_PATTERN, AZURE_MAX_LENGTH),
    "aws": (AWS_SEGMENT_MAX, math.inf, "/", AWS_PATTERN, AWS_MAX_LENGTH),
    "gcp": (GCP_SEGMENT_MAX, math.inf, "--", GCP_PATTERN, GCP_MAX_LENGTH),
}


def _truncate_segment(segment, max_len):
    """Mirror of Java SecretNameBuilder.truncateSegment.

    If segment fits, return as-is. Otherwise return `<prefix>-<hash5>` where prefix is
    (max_len - 6) chars and hash5 is first 5 chars of sha256(segment) hex.
    """
    if len(segment) <= max_len:
        return segment
    prefix_len = max_len - 6
    if prefix_len <= 0:
        raise SecretReferenceError(f"invalid max_len for truncation: {max_len}")
    hash5 = hashlib.sha256(segment.encode()).hexdigest()[:5]
    return f"{segment[:prefix_len]}-{hash5}"


class SecretReferenceError(ValueError):
    """Raised when a secret reference violates store-specific constraints.

    Mirrors Java `SecretReferenceException`. Kept as a ValueError subclass so
    generic ValueError handlers still catch it, while callers wanting the
    specific class can catch this narrower type.
    """


def build_vals_uri(store_type, store_config, normalized_name, store_id, default_store_id):
    """Compose a VALS URI from store config + normalized secret name.

    Java parity target (initial): vault + default_store case only.
    Non-default-store and non-vault types raise NotImplementedError until
    subsequent TDD atoms extend the function.
    """
    if store_type == "vault":
        base = f"ref+vault://{store_config['mountPath']}/data/{normalized_name}"
    elif store_type == "azure":
        base = f"ref+azurekeyvault://{store_config['vaultName']}/{normalized_name}"
    elif store_type == "aws":
        base = f"ref+awssecrets://{normalized_name}?region={store_config['region']}"
    elif store_type == "gcp":
        base = f"ref+gcpsecrets://{store_config['projectId']}/{normalized_name}"
    else:
        raise NotImplementedError(f"store_type={store_type!r} not yet supported")

    if store_id == default_store_id:
        return base
    separator = "&" if store_type == "aws" else "?"
    return f"{base}{separator}secret_store_id={store_id}"


def normalize_secret_name(remote_ref_path, cred_id, store_type):
    """Mirror of Java SecretNameBuilder.buildNormalizedSecretName.

    Vault: concatenate `<remoteRefPath>/<credId>` (no per-store length cap on cred-id).
    Other store types: normalized per store (segment truncation, `--` or `/` delim, pattern +
    length validation) - added in subsequent atoms.
    """
    remote_ref_path = remote_ref_path.strip()
    cred_id = cred_id.strip()
    if store_type == "vault":
        result = f"{remote_ref_path}/{cred_id}"
        if not VAULT_PATTERN.match(result):
            raise SecretReferenceError(
                f"vault secret name {result!r} contains characters outside {VAULT_PATTERN.pattern}"
            )
        return result
    if store_type in _STORE_PROFILES:
        segment_max, max_segments, delim, pattern, total_max = _STORE_PROFILES[store_type]
        if len(cred_id) > MAX_CRED_ID_LENGTH:
            raise SecretReferenceError(
                f"Credential ID {cred_id!r} exceeds max length {MAX_CRED_ID_LENGTH} for {store_type}"
            )
        segments = remote_ref_path.split("/")
        if max_segments is not math.inf:
            segments = segments[: int(max_segments)]
        path_part = delim.join(_truncate_segment(seg, segment_max) for seg in segments)
        result = f"{path_part}{delim}{cred_id}"
        if not pattern.match(result):
            raise SecretReferenceError(
                f"{store_type} secret name {result!r} contains characters outside {pattern.pattern}"
            )
        if len(result) > total_max:
            raise SecretReferenceError(
                f"Final Normalized Secret Name {result!r} exceeds max length {total_max} for {store_type}"
            )
        return result
    raise NotImplementedError(f"store_type={store_type!r} not yet supported")
