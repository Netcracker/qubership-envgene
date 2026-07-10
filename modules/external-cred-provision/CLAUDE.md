# external-cred-provision — External Credential Provisioning CLI

Pip-installable package (`external-cred-provision`, v0.1.0 — version is a setuptools formality, not published anywhere; see root `CLAUDE.md` "Python module layout"). Provisions credentials defined in a declarative YAML context file into secret stores (Vault, OpenBao, etc. via `qubership-pipelines-common-library`'s `MultiStoreProvider`/`SecretManager`). Installs a console script: `external-cred-provision <context-file>`.

## File Reference

| File | Responsibility |
|------|---------------|
| `main.py` | `cli()` — click entry point (`context_file`, `--dry-run`, `--log-level`); `setup_logging()` configures console + `module.log` (module-level) + `full.log` (always DEBUG) handlers |
| `provisioner.py` | `ExternalCredProvisioner.run()` — orchestrates load → pre-flight → processing/dry-run → summary; `PasswordGenerator` (`_generateValue` marker resolution); `Strategy` enum (`fail_if_absent`, `create_if_absent`, `overwrite`); `CredentialEntry`/`ProvisioningResult` dataclasses |

## Flow (`ExternalCredProvisioner.run`)

1. **Load context** (`_load_context`) — parses the YAML context file; if SOPS-encrypted (`SopsClient.is_encrypted`), decrypts using `SOPS_AGE_KEY` env var first. Parses each `credentials.<id>` entry into a `CredentialEntry` (`vals` path, `strategy`, `data`, provider type/store ID from `MultiStoreProvider.parse_provider_type`).
2. **Pre-flight phase** — authenticates to every distinct (provider_type, store) pair referenced by the context before touching anything.
3. **Processing phase** (or **dry-run phase**) — applies each credential per its `Strategy`: `fail_if_absent` requires the secret to already exist; `create_if_absent` only writes if missing; `overwrite` always writes. Dry-run only checks existence/connectivity, never writes.
4. **Summary** — logs aggregate counts (`created`/`overwritten`/`skipped`/`verified`/`failed` or `dry_run_ok`/`dry_run_fail`); `run()` exit code is non-zero if anything failed.

## Important Conventions

- `data` value `_generateValue` (the `GENERATE_MARKER`) is resolved to a random password (`PasswordGenerator`, 16 chars by default) instead of being taken literally — per-field for dict `data`, or for the whole value if `data` is a plain string.
- `vault`/`openbao` stores (`_DICT_ONLY_STORES`) reject plain-string `data` — must use named fields (a dict).

## Tests

```bash
pip install -e modules/external-cred-provision
cd modules/external-cred-provision
python -m pytest external_cred_provision/
```
