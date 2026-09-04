"""Decrypt Fernet- and SOPS-encrypted credential YAML before collect."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

import yaml

from migration_cli.errors import MigrationCliError

FERNET_PREFIX = "[encrypted:AES256_Fernet]"


def is_sops_file(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return any(line.startswith("sops:") for line in reversed(text.splitlines()))


def _decrypt_fernet_value(text: str, secret_key: str) -> str:
    if not text or FERNET_PREFIX not in text:
        return text
    try:
        from cryptography.fernet import Fernet
    except ImportError as exc:
        raise MigrationCliError(
            "Encrypted Fernet value found but 'cryptography' is not installed. "
            "Run: pip install cryptography"
        ) from exc
    token = text.replace(FERNET_PREFIX, "").encode("utf-8")
    return Fernet(secret_key.encode("utf-8")).decrypt(token).decode("utf-8")


def _decrypt_fernet_tree(node: Any, secret_key: str) -> Any:
    if isinstance(node, dict):
        return {k: _decrypt_fernet_tree(v, secret_key) for k, v in node.items()}
    if isinstance(node, list):
        return [_decrypt_fernet_tree(item, secret_key) for item in node]
    if isinstance(node, str):
        return _decrypt_fernet_value(node, secret_key)
    return node


def _has_fernet_values(node: Any) -> bool:
    if isinstance(node, dict):
        return any(_has_fernet_values(v) for v in node.values())
    if isinstance(node, str):
        return FERNET_PREFIX in node
    return False


def _decrypt_sops_file(path: Path) -> dict[str, Any]:
    sops_key = os.getenv("SOPS_AGE_KEY") or os.getenv("ENVGENE_AGE_PRIVATE_KEY")
    if not sops_key:
        raise MigrationCliError(
            f"File {path} is SOPS-encrypted. Set SOPS_AGE_KEY or ENVGENE_AGE_PRIVATE_KEY."
        )
    env = os.environ.copy()
    env.setdefault("SOPS_AGE_KEY", sops_key)
    try:
        result = subprocess.run(
            ["sops", "-d", str(path)],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
    except FileNotFoundError as exc:
        raise MigrationCliError(
            f"File {path} is SOPS-encrypted but 'sops' CLI is not on PATH."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise MigrationCliError(f"SOPS decryption failed for {path}: {exc.stderr.strip()}") from exc
    doc = yaml.safe_load(result.stdout)
    if not isinstance(doc, dict):
        raise MigrationCliError(f"SOPS decryption of {path} did not yield a YAML mapping.")
    return doc


def load_credential_document(path: Path, secret_key: str | None = None) -> dict[str, Any]:
    """Load and decrypt a credential YAML file when encryption is enabled."""
    if is_sops_file(path):
        return _decrypt_sops_file(path)

    with path.open(encoding="utf-8") as handle:
        doc = yaml.safe_load(handle)
    if not isinstance(doc, dict):
        return {}

    if not _has_fernet_values(doc):
        return doc

    key = secret_key or os.getenv("SECRET_KEY")
    if not key:
        raise MigrationCliError(
            f"File {path} contains Fernet-encrypted values. "
            "Set SECRET_KEY or pass --secret-key."
        )
    return _decrypt_fernet_tree(doc, key)
