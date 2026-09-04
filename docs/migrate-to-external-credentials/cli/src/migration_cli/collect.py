"""Collect local Credential plaintext from an Instance Repository."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from migration_cli.decrypt import load_credential_document
from migration_cli.errors import MigrationCliError, ValidationError
from migration_cli.models import ClusterBucket, CredValue, HierarchicalValuesStore
from migration_cli.repo_paths import (
    bucket_kind,
    find_env_definitions,
    load_env_definition,
    normalize_shared_stem,
    parse_cluster_env,
    resolve_passport_creds,
    resolve_shared_file,
)
from migration_cli.yaml_io import dump_yaml

logger = logging.getLogger(__name__)


@dataclass
class _PathBinding:
    path: Path
    kind: str
    cluster: str
    env: str | None = None


@dataclass
class _BindingIndex:
    bindings: list[_PathBinding] = field(default_factory=list)
    seen_paths: set[Path] = field(default_factory=set)

    def add(self, path: Path, kind: str, cluster: str, env: str | None = None) -> None:
        if kind == "skip" or not path.is_file():
            return
        if path in self.seen_paths:
            return
        self.seen_paths.add(path)
        self.bindings.append(_PathBinding(path=path, kind=kind, cluster=cluster, env=env))


class CollectCredentialValues:
    """Scan Instance Repository local Credentials into a tiered values file."""

    def __init__(
        self,
        instance_root: Path,
        out: Path,
        env_filter: str | None = None,
        secret_key: str | None = None,
    ) -> None:
        self._instance_root = instance_root
        self._out = out
        self._env_filter = self._parse_filter(env_filter)
        self._secret_key = secret_key

    def run(self) -> None:
        self._validate()
        self._execute()

    def _validate(self) -> None:
        if not self._instance_root.is_dir():
            raise ValidationError(f"INSTANCE_ROOT is not a directory: {self._instance_root}")
        environments = self._instance_root / "environments"
        if not environments.is_dir():
            raise ValidationError(f"Missing environments/ under {self._instance_root}")

    def _execute(self) -> None:
        env_defs = find_env_definitions(self._instance_root)
        if not env_defs:
            raise MigrationCliError("No Environment Instance found under environments/")

        index = self._build_bindings(env_defs)
        if not index.bindings:
            raise MigrationCliError("No credential YAML files bound for collection")

        store = HierarchicalValuesStore()
        parsed_cache: dict[Path, dict[str, Any]] = {}
        for binding in index.bindings:
            self._ingest_binding(store, binding, parsed_cache)

        dump_yaml(self._out, store.to_yaml_dict())
        cluster_count = len(store.clusters)
        logger.info(
            "Wrote values file %s (%s clusters, %s bound files)",
            self._out,
            cluster_count,
            len(index.bindings),
        )

    def _build_bindings(self, env_defs: list[Path]) -> _BindingIndex:
        index = _BindingIndex()
        matched_envs = 0
        for env_def in env_defs:
            cluster, env = parse_cluster_env(env_def, self._instance_root)
            scope_key = f"{cluster}/{env}"
            if self._env_filter is not None and scope_key not in self._env_filter:
                continue
            matched_envs += 1
            doc = load_env_definition(env_def)
            inventory = doc.get("inventory") or {}
            env_template = doc.get("envTemplate") or {}

            passport = inventory.get("cloudPassport")
            if passport:
                creds_path = resolve_passport_creds(self._instance_root, cluster, str(passport))
                if creds_path is not None:
                    index.add(creds_path, "cloud", cluster)

            shared_raw = env_template.get("sharedMasterCredentialFiles") or []
            if isinstance(shared_raw, str):
                shared_raw = [shared_raw]
            for raw in shared_raw:
                stem, _has_ext = normalize_shared_stem(str(raw))
                resolved = resolve_shared_file(self._instance_root, cluster, env, stem)
                if resolved is None:
                    logger.warning(
                        "Shared credential file %r referenced by %s not found",
                        stem,
                        scope_key,
                    )
                    continue
                kind = bucket_kind(resolved, self._instance_root)
                index.add(resolved, kind, cluster, env if kind == "env" else None)

            env_dir = (
                self._instance_root
                / "environments"
                / cluster
                / env
                / "Inventory"
                / "credentials"
            )
            if env_dir.is_dir():
                for path in sorted(env_dir.glob("*.yml")) + sorted(env_dir.glob("*.yaml")):
                    index.add(path, "env", cluster, env)

        if matched_envs == 0 and self._env_filter is not None:
            raise MigrationCliError(f"No environments matched env_filter={self._env_filter!r}")
        return index

    def _ingest_binding(
        self,
        store: HierarchicalValuesStore,
        binding: _PathBinding,
        parsed_cache: dict[Path, dict[str, Any]],
    ) -> None:
        raw = parsed_cache.get(binding.path)
        if raw is None:
            try:
                raw = load_credential_document(binding.path, secret_key=self._secret_key)
            except MigrationCliError:
                raise
            except OSError as exc:
                raise MigrationCliError(f"Failed to read {binding.path}: {exc}") from exc
            parsed_cache[binding.path] = raw

        credentials = raw.get("credentials") if isinstance(raw.get("credentials"), dict) else raw
        if not isinstance(credentials, dict):
            logger.debug("Skip non-mapping credentials in %s", binding.path)
            return

        bucket = store.cluster(binding.cluster)
        source = str(binding.path.relative_to(self._instance_root))
        for cred_id, body in credentials.items():
            if not isinstance(body, dict):
                continue
            value = _extract_local_value(str(cred_id), body)
            if value is None:
                continue
            try:
                self._put_value(bucket, store, binding, value, source=source)
            except ValueError as exc:
                raise MigrationCliError(f"{exc} (file={binding.path})") from exc
            logger.debug(
                "Collected %s tier=%s cluster=%s env=%s from %s",
                cred_id,
                binding.kind,
                binding.cluster,
                binding.env,
                binding.path,
            )

    @staticmethod
    def _put_value(
        bucket: ClusterBucket,
        store: HierarchicalValuesStore,
        binding: _PathBinding,
        value: CredValue,
        *,
        source: str,
    ) -> None:
        if binding.kind == "cloud":
            bucket.put_cloud(value, source=source)
        elif binding.kind == "shared":
            bucket.put_shared(value, source=source)
        elif binding.kind == "repository_shared":
            store.put_repository_shared(value, source=source)
        elif binding.kind == "env":
            if not binding.env:
                raise ValueError(f"Env binding missing env name for {source}")
            bucket.put_env(binding.env, value, source=source)
        else:
            logger.debug("Skip bucket kind=%s for %s", binding.kind, source)

    @staticmethod
    def _parse_filter(env_filter: str | None) -> set[str] | None:
        if not env_filter or not env_filter.strip():
            return None
        return {part.strip() for part in env_filter.split(",") if part.strip()}


def _extract_local_value(cred_id: str, body: dict[str, Any]) -> CredValue | None:
    cred_type = str(body.get("type") or "").strip()
    if cred_type.lower() == "external":
        return None

    if body.get("username") is not None or body.get("password") is not None:
        return CredValue(
            cred_id=cred_id,
            cred_type=cred_type or "usernamePassword",
            fields={
                "username": "" if body.get("username") is None else str(body.get("username")),
                "password": "" if body.get("password") is None else str(body.get("password")),
            },
        )

    if body.get("secret") is not None:
        return CredValue(
            cred_id=cred_id,
            cred_type=cred_type or "secret",
            fields={"secret": str(body.get("secret"))},
        )

    if body.get("value") is not None:
        return CredValue(
            cred_id=cred_id,
            cred_type=cred_type or "secret",
            fields={"value": str(body.get("value"))},
        )

    data = body.get("data")
    if isinstance(data, dict) and data:
        nested = {str(k): str(v) for k, v in data.items() if v is not None}
        inferred = "usernamePassword" if "username" in nested else "secret"
        return CredValue(cred_id=cred_id, cred_type=cred_type or inferred, fields=nested)
    return None
