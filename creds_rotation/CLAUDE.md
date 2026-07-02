# creds_rotation — Credential Rotation Pipeline Job

Implements the `credential_rotation` pipeline job. Given a JSON payload (via `CRED_ROTATION_PAYLOAD`) describing which parameters to rotate and their new values, it locates the affected credential and instance files, updates them, and writes an `affected-sensitive-parameters.yaml` report.

## Scripts (`scripts/`)

| File | Responsibility |
|------|---------------|
| `creds_rotation_handler.py` | Entry point `cred_rotation()`: validates env vars, reads all files, iterates payload entries via `process_entry_in_payload`, optionally writes updates |
| `core_rotation.py` | `process_entry_in_payload`: resolves namespace/app file, extracts the `${creds.get(...)}` macro, finds all credential files that contain the cred ID, searches for all parameters referencing that cred |
| `models.py` | Dataclasses: `PayloadEntry`, `RotationResult`, `AffectedParameter`, `CredMap`, `EnvConfig` |
| `utils/cred_utils.py` | Decrypt files, read env/shared cred files, update cred content, write back |
| `utils/search_utils.py` | `get_ns_content`, `get_app_content`, `resolve_param` (context → YAML key), `search_yaml_files` (finds all parameters using a cred value) |
| `utils/file_utils.py` | `scan_and_get_yaml_files` — scans cluster path for all namespace/app/cred YAML files |
| `utils/yaml_utils.py` | `convert_json_to_yaml`, `write_yaml_to_file` |
| `utils/error_constants.py` | `ErrorMessages` and `ErrorCodes` constants |

## Required Environment Variables

| Variable | Description |
|----------|-------------|
| `ENV_NAME` | Target environment name |
| `CLUSTER_NAME` | Target cluster name |
| `CI_PROJECT_DIR` | Instance repository root |
| `CRED_ROTATION_PAYLOAD` | JSON or base64-encoded JSON with `rotation_items` list |
| `CRED_ROTATION_FORCE` | `"true"` to actually write file updates; `"false"` for dry-run (report only) |

## Payload Format

```json
{
  "rotation_items": [
    {
      "namespace": "my-namespace",
      "parameter_key": "SOME_PARAM",
      "context": "deployParameters",
      "parameter_value": "new-secret-value",
      "application": "my-app"  // optional; omit for namespace-level param
    }
  ]
}
```

Payload may be raw JSON or base64-encoded JSON. If `crypt_backend == SOPS` and the file is encrypted, it is decrypted before parsing. Fernet-encrypted payloads are rejected.

## Limitation

External credentials (`type: external`) are not supported — rotation must be performed at the Secret Store directly. Attempting to rotate an external credential fails validation.

## Tests

```bash
cd creds_rotation/scripts
python -m pytest
```
Test file: `test_creds_rotation_handler.py`.
