"""Data models for migration-cli."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class EnvScope:
    """One Environment Instance location under environments/."""

    cluster: str
    env: str

    @property
    def key(self) -> str:
        return f"{self.cluster}/{self.env}"


@dataclass
class CredValue:
    """Plaintext credential payload keyed later by credId."""

    cred_id: str
    cred_type: str
    fields: dict[str, str] = field(default_factory=dict)

    def to_yaml_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"type": self.cred_type}
        payload.update(self.fields)
        return payload


def _cred_from_payload(cred_id: str, payload: Any) -> CredValue:
    if not isinstance(payload, dict):
        raise ValueError(f"Credential {cred_id!r} payload must be a mapping")
    cred_type = str(payload.get("type") or _infer_type(payload))
    fields = {
        str(k): "" if v is None else str(v)
        for k, v in payload.items()
        if k != "type" and v is not None
    }
    return CredValue(cred_id=cred_id, cred_type=cred_type, fields=fields)


def _infer_type(payload: dict[str, Any]) -> str:
    if "username" in payload or "password" in payload:
        return "usernamePassword"
    if "secret" in payload or "value" in payload:
        return "secret"
    return "unknown"


def _credentials_block(body: dict[str, Any]) -> dict[str, CredValue]:
    credentials = body.get("credentials") or {}
    if not isinstance(credentials, dict):
        return {}
    return {str(cred_id): _cred_from_payload(str(cred_id), payload) for cred_id, payload in credentials.items()}


@dataclass
class ClusterBucket:
    cloud: dict[str, CredValue] = field(default_factory=dict)
    shared: dict[str, CredValue] = field(default_factory=dict)
    environments: dict[str, dict[str, CredValue]] = field(default_factory=dict)

    def put_cloud(self, value: CredValue, *, source: str) -> None:
        _put_unique(self.cloud, value, bucket_name="cloud", source=source)

    def put_shared(self, value: CredValue, *, source: str) -> None:
        _put_unique(self.shared, value, bucket_name="shared", source=source)

    def put_env(self, env: str, value: CredValue, *, source: str) -> None:
        bucket = self.environments.setdefault(env, {})
        _put_unique(bucket, value, bucket_name=f"environments/{env}", source=source)


def _put_unique(
    target: dict[str, CredValue], value: CredValue, *, bucket_name: str, source: str
) -> None:
    existing = target.get(value.cred_id)
    if existing is not None and existing.fields != value.fields:
        raise ValueError(
            f"Conflicting plaintext for credId={value.cred_id!r} in {bucket_name!r} (source={source})"
        )
    target[value.cred_id] = value


@dataclass
class HierarchicalValuesStore:
    """Tiered credential values without per-env duplication of cluster scope."""

    repository_shared: dict[str, CredValue] = field(default_factory=dict)
    clusters: dict[str, ClusterBucket] = field(default_factory=dict)

    def cluster(self, name: str) -> ClusterBucket:
        return self.clusters.setdefault(name, ClusterBucket())

    def put_repository_shared(self, value: CredValue, *, source: str) -> None:
        _put_unique(self.repository_shared, value, bucket_name="repository.shared", source=source)

    def lookup(self, cluster: str, env: str, cred_id: str) -> CredValue | None:
        """Resolve credId: env -> shared -> cloud -> repository.shared -> cross-cluster shared."""
        hit = self.lookup_with_tier(cluster, env, cred_id)
        return hit[0] if hit is not None else None

    def lookup_with_tier(self, cluster: str, env: str, cred_id: str) -> tuple[CredValue, str, str | None] | None:
        """Return (value, tier, source_cluster) for a matched credId."""
        cluster_bucket = self.clusters.get(cluster)
        if cluster_bucket is not None:
            env_bucket = cluster_bucket.environments.get(env, {})
            if cred_id in env_bucket:
                return env_bucket[cred_id], "env", cluster
            if cred_id in cluster_bucket.shared:
                return cluster_bucket.shared[cred_id], "shared", cluster
            if cred_id in cluster_bucket.cloud:
                return cluster_bucket.cloud[cred_id], "cloud", cluster
        if cred_id in self.repository_shared:
            return self.repository_shared[cred_id], "repository_shared", None
        cross_cluster = self._lookup_cross_cluster_shared(cred_id, exclude_cluster=cluster)
        if cross_cluster is not None:
            source_cluster, value = cross_cluster
            return value, "cross_cluster_shared", source_cluster
        return None

    def _lookup_cross_cluster_shared(
        self, cred_id: str, *, exclude_cluster: str
    ) -> tuple[str, CredValue] | None:
        matches: list[tuple[str, CredValue]] = []
        for cluster_name, bucket in self.clusters.items():
            if cluster_name == exclude_cluster:
                continue
            if cred_id in bucket.shared:
                matches.append((cluster_name, bucket.shared[cred_id]))
        if not matches:
            return None
        if len(matches) == 1:
            return matches[0]
        first_cluster, first_value = matches[0]
        if all(value.fields == first_value.fields for _, value in matches[1:]):
            return first_cluster, first_value
        clusters = ", ".join(sorted(name for name, _ in matches))
        raise ValueError(
            f"Ambiguous shared credId={cred_id!r} across clusters: {clusters}"
        )

    def to_yaml_dict(self) -> dict[str, Any]:
        doc: dict[str, Any] = {}
        if self.repository_shared:
            doc["repository"] = {
                "shared": {
                    "credentials": {
                        cred_id: cred.to_yaml_dict()
                        for cred_id, cred in sorted(self.repository_shared.items())
                    }
                }
            }
        clusters_doc: dict[str, Any] = {}
        for cluster_name, bucket in sorted(self.clusters.items()):
            cluster_doc: dict[str, Any] = {}
            if bucket.cloud:
                cluster_doc["cloud"] = {
                    "credentials": {
                        cred_id: cred.to_yaml_dict()
                        for cred_id, cred in sorted(bucket.cloud.items())
                    }
                }
            if bucket.shared:
                cluster_doc["shared"] = {
                    "credentials": {
                        cred_id: cred.to_yaml_dict()
                        for cred_id, cred in sorted(bucket.shared.items())
                    }
                }
            if bucket.environments:
                envs: dict[str, Any] = {}
                for env_name, creds in sorted(bucket.environments.items()):
                    envs[env_name] = {
                        "credentials": {
                            cred_id: cred.to_yaml_dict()
                            for cred_id, cred in sorted(creds.items())
                        }
                    }
                cluster_doc["environments"] = envs
            if cluster_doc:
                clusters_doc[cluster_name] = cluster_doc
        if clusters_doc:
            doc["clusters"] = clusters_doc
        return doc

    @classmethod
    def from_yaml_dict(cls, data: dict[str, Any]) -> HierarchicalValuesStore:
        if "clusters" in data or "repository" in data:
            return cls._from_hierarchical(data)
        if "environments" in data:
            return cls._from_legacy_flat(data)
        return cls()

    @classmethod
    def _from_hierarchical(cls, data: dict[str, Any]) -> HierarchicalValuesStore:
        store = cls()
        repository = data.get("repository") or {}
        if isinstance(repository, dict):
            shared = repository.get("shared") or {}
            if isinstance(shared, dict):
                for cred_id, payload in _credentials_block(shared).items():
                    store.put_repository_shared(payload, source="values file")

        clusters = data.get("clusters") or {}
        if not isinstance(clusters, dict):
            raise ValueError("values file: 'clusters' must be a mapping")
        for cluster_name, body in clusters.items():
            if not isinstance(body, dict):
                continue
            bucket = store.cluster(str(cluster_name))
            cloud = body.get("cloud") or {}
            if isinstance(cloud, dict):
                for cred_id, payload in _credentials_block(cloud).items():
                    bucket.put_cloud(payload, source="values file")
            shared = body.get("shared") or {}
            if isinstance(shared, dict):
                for cred_id, payload in _credentials_block(shared).items():
                    bucket.put_shared(payload, source="values file")
            environments = body.get("environments") or {}
            if isinstance(environments, dict):
                for env_name, env_body in environments.items():
                    if not isinstance(env_body, dict):
                        continue
                    for cred_id, payload in _credentials_block(env_body).items():
                        bucket.put_env(str(env_name), payload, source="values file")
        return store

    @classmethod
    def _from_legacy_flat(cls, data: dict[str, Any]) -> HierarchicalValuesStore:
        """Support old flat environments.<cluster/env> collect output."""
        store = cls()
        environments = data.get("environments") or {}
        if not isinstance(environments, dict):
            raise ValueError("values file: 'environments' must be a mapping")
        for scope_key, body in environments.items():
            if not isinstance(body, dict):
                continue
            cluster, _, env = str(scope_key).partition("/")
            if not cluster or not env:
                raise ValueError(f"Invalid scope key {scope_key!r}; expected cluster/env")
            bucket = store.cluster(cluster)
            for cred_id, payload in _credentials_block(body).items():
                bucket.put_env(env, payload, source="values file")
        return store
