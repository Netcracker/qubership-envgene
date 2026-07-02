# artifact-searcher — Async Maven Artifact Resolver

Resolves `application:version` notation to download-ready Maven artifact URLs. Supports Nexus, Artifactory, AWS CodeArtifact, GCP Artifact Registry, and Azure Artifacts. Uses `aiohttp` for parallel resolution across multiple repos.

## File Reference

| File | Responsibility |
|------|---------------|
| `artifact_searcher/artifact.py` | Main async resolution logic: `check_artifact_async` fans out per-repo tasks; `resolve_snapshot_version_async` fetches `maven-metadata.xml`; `check_artifacts_by_aql` for Artifactory AQL search; `download_all_async` groups by auth headers for parallel download |
| `artifact_searcher/auth_resolver.py` | `resolve_v2_auth_headers(registry, env_creds)` dispatches to provider+authMethod handler; AWS (CodeArtifact token), GCP (service account key), basic auth (base64) |
| `artifact_searcher/utils/models.py` | Pydantic models: `Registry` (V1), `RegistryV2` (V2), `Application`, `MavenConfig`, `AuthConfig`, `Provider` enum, `ArtifactInfo`; `parse_registry` auto-detects V1 vs V2 |
| `artifact_searcher/utils/constants.py` | `DEFAULT_REQUEST_TIMEOUT`, `TCP_CONNECTION_LIMIT`, `METADATA_XML` |

## Registry V1 vs V2

- **V1**: `credentialsId` string → basic auth username:password
- **V2**: `version: "2.0"` + `authConfig` map → multi-cloud auth (AWS/GCP/Azure/Nexus/Artifactory)
- Detection: `parse_registry(data)` checks `data.get("version") == "2.0"` or `"authConfig" in data`

## Auth Methods (V2)

| Provider | authMethod | Notes |
|----------|-----------|-------|
| `aws` | `secret` | `AWSCodeArtifactHelper.get_authorization_token` |
| `gcp` | `service_account` | `GcpCredentialsProvider().with_service_account_key(...)` |
| `nexus`, `artifactory` | `user_pass` | base64 `username:password` |
| any | `anonymous` | no auth header |
| `aws` | `assume_role` | `NotImplementedError` (not yet implemented) |
| `gcp` | `federation` | `NotImplementedError` |
| `azure` | `oauth2` | `NotImplementedError` |

## Tests

```bash
cd python/artifact-searcher
python -m pytest artifact_searcher/
```
