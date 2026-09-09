"""Fill External Credential Context from a local values or Jenkins export file."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from migration_cli.errors import MatchError, MigrationCliError, ValidationError
from migration_cli.models import CredValue, HierarchicalValuesStore
from migration_cli.repo_paths import find_context_files, scope_from_context_path
from migration_cli.values_loader import load_instance_values_source, load_jenkins_index
from migration_cli.yaml_io import dump_yaml, load_yaml

logger = logging.getLogger(__name__)

_FAIL_IF_ABSENT = "fail_if_absent"
_DEFAULT_SEED_STRATEGY = "create_if_absent"


@dataclass
class _EnvFillOutcome:
    cluster: str
    env: str
    credentials: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    unmatched: list[dict[str, Any]] = field(default_factory=list)


class FillExternalCredentialContext:
    """Fill one External Credential Context file (single environment)."""

    def __init__(
        self,
        context: Path,
        values_format: str,
        out: Path,
        values: Path | None = None,
        values_dir: Path | None = None,
        tenant: str | None = None,
        cloud: str | None = None,
        seed_strategy: str | None = None,
        partial: bool = False,
        report: Path | None = None,
    ) -> None:
        self._context = context
        self._values = values
        self._values_dir = values_dir
        self._values_format = values_format
        self._out = out
        self._tenant = tenant
        self._cloud = cloud
        self._seed_strategy = seed_strategy or _DEFAULT_SEED_STRATEGY
        self._partial = partial
        self._report = report

    def run(self) -> None:
        _validate_values_source(self._values, self._values_dir)
        if not self._context.is_file():
            raise ValidationError(f"Context file not found: {self._context}")
        _validate_fill_options(
            values_format=self._values_format,
            seed_strategy=self._seed_strategy,
            tenant=self._tenant,
            cloud=self._cloud,
            values_dir=self._values_dir,
        )
        try:
            context_doc = load_yaml(self._context)
        except (OSError, yaml.YAMLError) as exc:
            raise MigrationCliError(f"Failed to load context: {exc}") from exc
        if not isinstance(context_doc, dict):
            raise MigrationCliError("Context must be a YAML mapping")

        cluster, env = scope_from_context_path(self._context)
        lookup = _build_lookup(
            values_format=self._values_format,
            values=self._values,
            values_dir=self._values_dir,
            cluster=cluster,
            env=env,
            scope_key=f"{cluster}/{env}",
            tenant=self._tenant,
            cloud=self._cloud,
        )
        outcome = _fill_context_document(
            context_doc=context_doc,
            cluster=cluster,
            env=env,
            lookup=lookup,
            seed_strategy=self._seed_strategy,
            values_format=self._values_format,
        )
        if outcome.errors and not self._partial:
            raise MatchError(outcome.errors[0])
        dump_yaml(self._out, {"credentials": outcome.credentials})
        logger.info(
            "Wrote filled context %s (%s matched; %s unmatched; create_if_absent omitted)",
            self._out,
            len(outcome.credentials),
            len(outcome.unmatched),
        )
        if outcome.unmatched:
            report_path = self._report or _default_report_path(self._out)
            dump_yaml(
                report_path,
                {
                    "unmatched": outcome.unmatched,
                    "summary": {
                        "matched": len(outcome.credentials),
                        "unmatched": len(outcome.unmatched),
                    },
                },
            )
            logger.warning("Wrote unmatched report %s (%s items)", report_path, len(outcome.unmatched))
            for err in outcome.errors:
                logger.error("%s", err)
            if self._partial:
                raise MigrationCliError(
                    f"Partial fill: {len(outcome.credentials)} matched, "
                    f"{len(outcome.unmatched)} unmatched; see {report_path}"
                )
            raise MatchError(outcome.errors[0])


class FillRepositoryContexts:
    """Fill all External Credential Context files under an Instance Repository."""

    def __init__(
        self,
        repo_root: Path,
        values_format: str,
        out: Path,
        values: Path | None = None,
        values_dir: Path | None = None,
        tenant: str | None = None,
        cloud: str | None = None,
        seed_strategy: str | None = None,
        env_filter: str | None = None,
        continue_on_error: bool = False,
        partial: bool = False,
        report: Path | None = None,
    ) -> None:
        self._repo_root = repo_root
        self._values = values
        self._values_dir = values_dir
        self._values_format = values_format
        self._out = out
        self._tenant = tenant
        self._cloud = cloud
        self._seed_strategy = seed_strategy or _DEFAULT_SEED_STRATEGY
        self._env_filter = _parse_env_filter(env_filter)
        self._continue_on_error = continue_on_error
        self._partial = partial
        self._report = report

    def run(self) -> None:
        _validate_values_source(self._values, self._values_dir)
        if not self._repo_root.is_dir():
            raise ValidationError(f"repo-root is not a directory: {self._repo_root}")
        _validate_fill_options(
            values_format=self._values_format,
            seed_strategy=self._seed_strategy,
            tenant=self._tenant,
            cloud=self._cloud,
            values_dir=self._values_dir,
        )

        context_paths = find_context_files(self._repo_root)
        if self._env_filter is not None:
            context_paths = [
                path
                for path in context_paths
                if f"{scope_from_context_path(path)[0]}/{scope_from_context_path(path)[1]}"
                in self._env_filter
            ]
        if not context_paths:
            raise MigrationCliError("No external-credentials context files found under repo-root")

        flat_credentials: dict[str, Any] = {}
        env_ok = 0
        env_failed = 0
        env_partial = 0
        cred_count = 0
        all_errors: list[str] = []
        all_unmatched: list[dict[str, Any]] = []

        for context_path in context_paths:
            cluster, env = scope_from_context_path(context_path)
            scope_key = f"{cluster}/{env}"
            try:
                context_doc = load_yaml(context_path)
            except (OSError, yaml.YAMLError) as exc:
                message = f"{scope_key}: failed to load context: {exc}"
                if self._continue_on_error or self._partial:
                    all_errors.append(message)
                    env_failed += 1
                    continue
                raise MigrationCliError(message) from exc
            if not isinstance(context_doc, dict):
                message = f"{scope_key}: context must be a YAML mapping"
                if self._continue_on_error or self._partial:
                    all_errors.append(message)
                    env_failed += 1
                    continue
                raise MigrationCliError(message)

            lookup = _build_lookup(
                values_format=self._values_format,
                values=self._values,
                values_dir=self._values_dir,
                cluster=cluster,
                env=env,
                scope_key=scope_key,
                tenant=self._tenant,
                cloud=self._cloud,
            )
            outcome = _fill_context_document(
                context_doc=context_doc,
                cluster=cluster,
                env=env,
                lookup=lookup,
                seed_strategy=self._seed_strategy,
                values_format=self._values_format,
            )
            if outcome.errors and not self._partial:
                env_failed += 1
                all_errors.extend(f"{scope_key}: {err}" for err in outcome.errors)
                if not self._continue_on_error:
                    raise MatchError(outcome.errors[0])
                continue

            if outcome.credentials:
                for cred_id, entry in outcome.credentials.items():
                    flat_key = _repo_credential_key(cluster, env, cred_id)
                    if flat_key in flat_credentials:
                        raise MigrationCliError(
                            f"Duplicate filled credential key {flat_key!r} while processing {scope_key}"
                        )
                    flat_credentials[flat_key] = entry
                cred_count += len(outcome.credentials)

            if outcome.unmatched:
                all_unmatched.extend(outcome.unmatched)
                all_errors.extend(f"{scope_key}: {err}" for err in outcome.errors)
                env_partial += 1
                logger.warning(
                    "%s: partial fill (%s matched, %s unmatched)",
                    scope_key,
                    len(outcome.credentials),
                    len(outcome.unmatched),
                )
            else:
                env_ok += 1
            logger.debug("Filled %s credentials for %s", len(outcome.credentials), scope_key)

        dump_yaml(self._out, {"credentials": flat_credentials})
        logger.info(
            "Wrote filled repository context %s (%s env ok, %s env partial, %s env failed, %s credentials)",
            self._out,
            env_ok,
            env_partial,
            env_failed,
            cred_count,
        )
        report_path = self._report or _default_report_path(self._out)
        if all_unmatched:
            dump_yaml(
                report_path,
                {
                    "unmatched": all_unmatched,
                    "summary": {
                        "matched": cred_count,
                        "unmatched": len(all_unmatched),
                        "env_ok": env_ok,
                        "env_partial": env_partial,
                        "env_failed": env_failed,
                    },
                },
            )
            logger.warning("Wrote unmatched report %s (%s items)", report_path, len(all_unmatched))
        for err in all_errors:
            logger.error("%s", err)
        if env_failed and not self._partial:
            raise MigrationCliError(
                f"Fill completed with {env_failed} failed environment(s); see log above"
            )
        if all_unmatched or (env_failed and self._partial):
            raise MigrationCliError(
                f"Partial fill: {cred_count} matched, {len(all_unmatched)} unmatched, "
                f"{env_failed} env failed; see log"
                + (f" and {report_path}" if all_unmatched else "")
            )


def _validate_values_source(values: Path | None, values_dir: Path | None) -> None:
    if values is None and values_dir is None:
        raise ValidationError("Provide --values or --values-dir")
    if values is not None and values_dir is not None:
        raise ValidationError("Use either --values or --values-dir, not both")
    if values is not None and not values.is_file():
        raise ValidationError(f"Values file not found: {values}")


def _validate_fill_options(
    *,
    values_format: str,
    seed_strategy: str,
    tenant: str | None,
    cloud: str | None,
    values_dir: Path | None,
) -> None:
    if values_format not in {"instance_scoped", "jenkins_export"}:
        raise ValidationError(
            f"Unsupported values_format={values_format!r}; use instance_scoped or jenkins_export"
        )
    if seed_strategy not in {"create_if_absent", "overwrite"}:
        raise ValidationError(f"Unsupported seed_strategy={seed_strategy!r}")
    if values_format == "jenkins_export" and values_dir is None:
        if not tenant or not cloud:
            raise ValidationError(
                "tenant and cloud are required for jenkins_export with --values; "
                "omit them only when using --values-dir (suffix match across all exports)"
            )


def _fill_context_document(
    *,
    context_doc: dict[str, Any],
    cluster: str,
    env: str,
    lookup: _InstanceLookup | _JenkinsLookup,
    seed_strategy: str,
    values_format: str,
) -> _EnvFillOutcome:
    scope_key = f"{cluster}/{env}"
    credentials = context_doc.get("credentials")
    if not isinstance(credentials, dict):
        return _EnvFillOutcome(
            cluster=cluster,
            env=env,
            errors=[f"Context must contain a top-level 'credentials' mapping for {scope_key}"],
        )

    output_credentials: dict[str, Any] = {}
    errors: list[str] = []
    unmatched: list[dict[str, Any]] = []

    for cred_id, entry in credentials.items():
        if not isinstance(entry, dict):
            continue
        if entry.get("strategy") != _FAIL_IF_ABSENT:
            logger.debug("Skip credId=%s strategy=%s", cred_id, entry.get("strategy"))
            continue
        try:
            value = lookup.get(str(cred_id))
        except MatchError as exc:
            message = str(exc)
            errors.append(message)
            unmatched.append(
                {
                    "scope": scope_key,
                    "credId": str(cred_id),
                    "reason": message,
                    "tried": (
                        lookup.all_candidate_ids(str(cred_id))
                        if values_format == "jenkins_export"
                        and isinstance(lookup, _JenkinsLookup)
                        else []
                    ),
                }
            )
            continue
        if value is None:
            tried_ids: list[str] = []
            if values_format == "jenkins_export" and isinstance(lookup, _JenkinsLookup):
                tried_ids = lookup.all_candidate_ids(str(cred_id))
            message = (
                f"No plaintext for credId={cred_id!r} scope={scope_key!r}."
                f" tried={tried_ids!r}"
            )
            errors.append(message)
            unmatched.append(
                {
                    "scope": scope_key,
                    "credId": str(cred_id),
                    "reason": "no_plaintext",
                    "tried": tried_ids,
                }
            )
            continue
        if not any(str(v).strip() for v in value.fields.values()):
            message = f"Empty plaintext for credId={cred_id!r} scope={scope_key!r}"
            errors.append(message)
            unmatched.append(
                {
                    "scope": scope_key,
                    "credId": str(cred_id),
                    "reason": "empty_plaintext",
                    "tried": [],
                }
            )
            continue

        filled_entry = dict(entry)
        filled_entry["data"] = _data_for_context(value)
        filled_entry["strategy"] = seed_strategy
        output_credentials[str(cred_id)] = filled_entry
        logger.debug("Filled credId=%s scope=%s strategy=%s", cred_id, scope_key, seed_strategy)

    return _EnvFillOutcome(
        cluster=cluster,
        env=env,
        credentials=output_credentials,
        errors=errors,
        unmatched=unmatched,
    )


def _default_report_path(out: Path) -> Path:
    return out.with_name(f"{out.stem}-unmatched{out.suffix}")


def _build_lookup(
    *,
    values_format: str,
    values: Path | None,
    values_dir: Path | None,
    cluster: str,
    env: str,
    scope_key: str,
    tenant: str | None,
    cloud: str | None,
) -> _InstanceLookup | _JenkinsLookup:
    if values_format == "instance_scoped":
        values_doc = load_instance_values_source(values=values, values_dir=values_dir)
        store = HierarchicalValuesStore.from_yaml_dict(values_doc)
        return _InstanceLookup(store=store, cluster=cluster, env=env, scope_key=scope_key)

    by_id = load_jenkins_index(values=values, values_dir=values_dir)
    return _JenkinsLookup(
        by_id=by_id,
        tenant=tenant or "",
        cloud=cloud or "",
        env=env,
        cluster=cluster,
    )


def _repo_credential_key(cluster: str, env: str, cred_id: str) -> str:
    """Unique map key for repo-wide output compatible with external-cred-provision."""
    return f"{cluster}/{env}/{cred_id}"


def _parse_env_filter(env_filter: str | None) -> set[str] | None:
    if not env_filter or not env_filter.strip():
        return None
    return {part.strip() for part in env_filter.split(",") if part.strip()}


class _InstanceLookup:
    """Resolve credId via env -> shared -> cloud -> repository.shared -> cross-cluster shared."""

    def __init__(
        self, store: HierarchicalValuesStore, cluster: str, env: str, scope_key: str
    ) -> None:
        self._store = store
        self._cluster = cluster
        self._env = env
        self._scope_key = scope_key

    def get(self, cred_id: str, default: Any = None) -> CredValue | None:
        try:
            hit = self._store.lookup_with_tier(self._cluster, self._env, cred_id)
        except ValueError as exc:
            raise MatchError(str(exc)) from exc
        if hit is None:
            return default
        value, tier, source_cluster = hit
        if tier == "cross_cluster_shared":
            logger.info(
                "Matched credId=%s scope=%s via cross-cluster shared from %s",
                cred_id,
                self._scope_key,
                source_cluster,
            )
        else:
            logger.debug(
                "Matched credId=%s scope=%s tier=%s",
                cred_id,
                self._scope_key,
                tier,
            )
        return value


class _JenkinsLookup:
    """Resolve credId via Jenkins full id: env, cluster, then suffix fallback."""

    def __init__(
        self, by_id: dict[str, Any], tenant: str, cloud: str, env: str, cluster: str
    ) -> None:
        self._by_id = by_id
        self._tenant = tenant
        self._cloud = cloud
        self._env = env
        self._cluster = cluster

    def candidate_ids(self, cred_id: str) -> list[tuple[str, str]]:
        if not self._tenant or not self._cloud:
            return []
        pairs: list[tuple[str, str]] = []
        for name_segment, level in ((self._env, "env"), (self._cluster, "cluster")):
            if not name_segment:
                continue
            if level == "cluster" and name_segment == self._env:
                continue
            pairs.append((f"{self._tenant}-{self._cloud}-{name_segment}-{cred_id}", level))
            pairs.append((f"{self._tenant}-{self._cloud}-{name_segment}_{cred_id}", level))
        seen: set[str] = set()
        ordered: list[tuple[str, str]] = []
        for jenkins_id, level in pairs:
            if jenkins_id in seen:
                continue
            seen.add(jenkins_id)
            ordered.append((jenkins_id, level))
        return ordered

    def suffix_ids(self, cred_id: str) -> list[str]:
        explicit = {jenkins_id for jenkins_id, _level in self.candidate_ids(cred_id)}
        prefix = f"{self._tenant}-{self._cloud}-" if self._tenant and self._cloud else ""
        matches: list[str] = []
        for jenkins_id in self._by_id:
            if jenkins_id in explicit:
                continue
            if prefix and not jenkins_id.startswith(prefix):
                continue
            if jenkins_id.endswith(f"-{cred_id}") or jenkins_id.endswith(f"_{cred_id}"):
                matches.append(jenkins_id)
        return sorted(matches)

    def all_candidate_ids(self, cred_id: str) -> list[str]:
        ordered = [jenkins_id for jenkins_id, _level in self.candidate_ids(cred_id)]
        ordered.extend(self.suffix_ids(cred_id))
        return ordered

    def get(self, cred_id: str, default: Any = None) -> CredValue | None:
        for jenkins_id, level in self.candidate_ids(cred_id):
            payload = self._by_id.get(jenkins_id)
            if payload is None:
                logger.debug("Jenkins miss credId=%s level=%s id=%s", cred_id, level, jenkins_id)
                continue
            logger.info(
                "Matched credId=%s via %s-level Jenkins id=%s",
                cred_id,
                level,
                jenkins_id,
            )
            return _payload_to_cred(cred_id, payload)

        suffix_matches = self.suffix_ids(cred_id)
        if not suffix_matches:
            return default
        if len(suffix_matches) == 1:
            jenkins_id = suffix_matches[0]
            logger.info(
                "Matched credId=%s via suffix-level Jenkins id=%s",
                cred_id,
                jenkins_id,
            )
            return _payload_to_cred(cred_id, self._by_id[jenkins_id])

        creds = [_payload_to_cred(cred_id, self._by_id[jenkins_id]) for jenkins_id in suffix_matches]
        if all(cred.fields == creds[0].fields for cred in creds[1:]):
            logger.info(
                "Matched credId=%s via suffix-level Jenkins id=%s (%s equivalent ids)",
                cred_id,
                suffix_matches[0],
                len(suffix_matches),
            )
            return creds[0]
        raise MatchError(
            f"Ambiguous Jenkins credId={cred_id!r}; suffix ids={suffix_matches!r}"
        )


def _payload_to_cred(cred_id: str, payload: dict[str, Any]) -> CredValue:
    body = payload
    nested = payload.get("data")
    if isinstance(nested, dict):
        body = {**{k: v for k, v in payload.items() if k != "data"}, **nested}

    cred_type = str(body.get("type") or "")
    fields = {
        str(k): "" if v is None else str(v)
        for k, v in body.items()
        if k != "type"
    }
    if not cred_type:
        cred_type = "usernamePassword" if "username" in fields or "password" in fields else "secret"
    return CredValue(cred_id=cred_id, cred_type=cred_type, fields=fields)


def _data_for_context(value: CredValue) -> Any:
    fields = value.fields
    if "username" in fields or "password" in fields:
        return {
            "username": fields.get("username", ""),
            "password": fields.get("password", ""),
        }
    if "secret" in fields and len(fields) == 1:
        return {"value": fields["secret"]}
    if "value" in fields and len(fields) == 1:
        return fields["value"] if value.cred_type == "secret" else {"value": fields["value"]}
    return dict(fields)
