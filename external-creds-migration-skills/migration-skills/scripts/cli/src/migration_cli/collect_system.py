"""Collect system credentials into an external-cred-provision context (no fill)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from migration_cli.decrypt import load_credential_document
from migration_cli.errors import MigrationCliError, ValidationError
from migration_cli.vals import (
    GLOBAL_PATH,
    build_normalized_secret_name,
    build_vals_uri,
    load_default_store,
)
from migration_cli.yaml_io import dump_yaml

logger = logging.getLogger(__name__)

_NULL = "envgeneNullValue"


def _is_null_placeholder(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, dict):
        return any(_is_null_placeholder(v) for v in value.values())
    if isinstance(value, str):
        return value.lower() == _NULL.lower()
    return False


def _extract_data(body: dict[str, Any]) -> dict[str, Any] | None:
    """Return plaintext field map for provision `data`, or None to skip."""
    cred_type = str(body.get("type") or "").strip()
    if cred_type.lower() == "external":
        return None

    data = body.get("data")
    if isinstance(data, dict) and data:
        if _is_null_placeholder(data):
            return None
        return {str(k): ("" if v is None else str(v)) for k, v in data.items()}

    # Flat usernamePassword / secret shapes
    if body.get("username") is not None or body.get("password") is not None:
        return {
            "username": "" if body.get("username") is None else str(body.get("username")),
            "password": "" if body.get("password") is None else str(body.get("password")),
        }
    if body.get("secret") is not None:
        if _is_null_placeholder(body.get("secret")):
            return None
        return {"secret": str(body.get("secret"))}
    if body.get("value") is not None:
        if _is_null_placeholder(body.get("value")):
            return None
        return {"value": str(body.get("value"))}
    return None


def _data_for_gcp_provision(data: dict[str, Any], store_type: str) -> dict[str, Any] | str:
    if store_type == "gcp" and set(data.keys()) == {"secret"}:
        return data["secret"]
    return data


class CollectSystemCredentials:
    """Scan configuration/credentials → provision context YAML (no fill step)."""

    def __init__(
        self,
        instance_root: Path,
        out: Path,
        *,
        strategy: str = "overwrite",
        secret_key: str | None = None,
        remote_ref_path: str = GLOBAL_PATH,
    ) -> None:
        self._instance_root = instance_root
        self._out = out
        self._strategy = strategy
        self._secret_key = secret_key
        self._remote_ref_path = remote_ref_path

    def run(self) -> None:
        self._validate()
        store = load_default_store(self._instance_root)
        store_type = (store.get("type") or "vault").lower()
        if store_type == "openbao":
            store_type = "vault"

        cred_dir = self._instance_root / "configuration" / "credentials"
        files = sorted(cred_dir.glob("*.yml")) + sorted(cred_dir.glob("*.yaml"))
        if not files:
            raise MigrationCliError(f"No credential YAML under {cred_dir}")

        credentials: dict[str, Any] = {}
        skipped: list[str] = []

        for path in files:
            try:
                raw = load_credential_document(path, secret_key=self._secret_key)
            except MigrationCliError:
                raise
            except OSError as exc:
                raise MigrationCliError(f"Failed to read {path}: {exc}") from exc

            body_root = raw.get("credentials") if isinstance(raw.get("credentials"), dict) else raw
            if not isinstance(body_root, dict):
                logger.warning("Skip non-mapping credentials file %s", path)
                continue

            for cred_id, body in body_root.items():
                if not isinstance(body, dict):
                    continue
                if body.get("type") == "external":
                    skipped.append(f"{cred_id} (already external)")
                    continue
                data = _extract_data(body)
                if data is None:
                    skipped.append(f"{cred_id} (no plaintext / envgeneNullValue)")
                    logger.warning(
                        "Skip %s from %s — no provisionable data",
                        cred_id,
                        path.name,
                    )
                    continue
                if cred_id in credentials:
                    raise MigrationCliError(
                        f"Duplicate system cred-id {cred_id!r} across credential files"
                    )
                try:
                    norm = build_normalized_secret_name(
                        self._remote_ref_path, str(cred_id), store_type
                    )
                    vals = build_vals_uri(store, norm)
                except ValueError as exc:
                    raise MigrationCliError(str(exc)) from exc
                credentials[str(cred_id)] = {
                    "vals": vals,
                    "strategy": self._strategy,
                    "data": _data_for_gcp_provision(data, store_type),
                }
                logger.info(
                    "Prepared system cred %s → %s (from %s)",
                    cred_id,
                    vals,
                    path.name,
                )

        if not credentials:
            raise MigrationCliError(
                "No system credentials with plaintext to provision "
                f"(skipped: {', '.join(skipped) or 'none'})"
            )

        dump_yaml(self._out, {"credentials": credentials})
        logger.info(
            "Wrote provision context %s (%s system credentials). "
            "Next: external-cred-provision %s",
            self._out,
            len(credentials),
            self._out,
        )
        if skipped:
            logger.info("Skipped: %s", "; ".join(skipped))

    def _validate(self) -> None:
        if not self._instance_root.is_dir():
            raise ValidationError(f"INSTANCE_ROOT is not a directory: {self._instance_root}")
        cred_dir = self._instance_root / "configuration" / "credentials"
        if not cred_dir.is_dir():
            raise ValidationError(
                f"Missing configuration/credentials/ under {self._instance_root}"
            )
        if self._strategy not in ("overwrite", "create_if_absent"):
            raise ValidationError(f"Unsupported strategy: {self._strategy}")
