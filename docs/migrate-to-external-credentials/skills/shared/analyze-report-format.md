# Analyze and preflight report format

Use this format when presenting `preflight.py`, `inventory_credids.py`, `inventory.py`, or
`classify_credentials.py` results to the user. Scripts emit JSON - the agent **summarises** that
JSON. Do not dump repository file contents.

Policy: [../template-repository/references/credential-policy.md](../template-repository/references/credential-policy.md),
[../instance-repository/references/credential-policy.md](../instance-repository/references/credential-policy.md).

## Global rules

- **Do not paste file contents** the user can open in the repository. Give repo-root paths only.
- **One table row per `credId`**, not per macro occurrence or per file.
- **Skipped files:** one summary line with count and example paths - no YAML excerpts.
- **Blockers and warnings:** `kind`, repo path, `credId` (if any), one-line message. Link to
  `suggested_action` when the script provides it.
- **Questions:** numbered list with a recommended option first. Ask only open decisions - do not
  re-ask what the script already resolved.
- **Never print** `data` values or actual passwords and tokens.
- **Built-in string fields** (`credentialsId`, `tokenSecret`, `defaultCredentialsId`,
  `credential`, plain strings like `GIT_CREDS_ID: github-cred`): one skip summary - do not list
  every field value.
- After the report, state the **single next command** (for example re-run preflight, or
  `draft_credential_template.py --plan` after confirmations).

---

## Template Repository (`migrate-template-repository`)

### When to use which block

| Script | Report title | Exit `0` | Exit `2` |
|--------|--------------|----------|----------|
| `preflight.py` | Preflight report | Summary + warnings (if any) + "Continue to inventory" | Summary + **Blockers** table - stop |
| `inventory_credids.py` | Analyze report | N/A (always `NEEDS_INPUT` until user confirms) | Summary + cred table + **Decisions** |

### Block 1 - Summary (required)

```markdown
## Preflight report | Analyze report

- Repository: current repo (--repo .)
- Descriptor(s): `templates/env_templates/demo-b2b.yaml`, ...
- Status: ok | NEEDS_INPUT
- Scanned: N template/ParameterSet files; M credId(s) with credential macros
- Skipped: K files without cred macros; Cloud/Tenant/Namespace built-in string fields only
- Blockers: count | Warnings: count | Decisions needed: count
```

### Block 2 - Blockers (preflight exit `2` only)

| kind | path | credId | message | suggested action |
|------|------|--------|---------|------------------|
| composite_macro | `templates/parameters/foo.yml` | `ID_X` | Composite credential macro... | Split into separate parameters |

Stop after this block until the user fixes blockers and preflight exits `0`.

### Block 3 - Credential inventory (analyze / preflight credentials list)

**One row per `credId`:**

| credId | structure | in Credential Template? | owner (proposal) | create (proposal) | remoteRefPath (proposal) | review |
|--------|-----------|-------------------------|------------------|-------------------|--------------------------|--------|
| app-client-creds | multi_field | yes | envgene | true | `{{ current_env.cloud }}/{{ current_env.name }}` | no |
| id_dbaas_admin | multi_field | **ask** | unknown | null | null | **yes** - marker `dbaas` |
| id_rabbitmq... | multi_field | **no** | - | - | - | **technical_only** |

Column **in Credential Template?**

- `yes` - template-owned env-tier; macro in bound deploy/e2e ParameterSets or template parameters
- `no` - passport/shared/instance handoff only; record for Instance migration
- `ask` - user must confirm tier before draft

For `review: yes` rows only, add a sub-line with **paths** (no file body):

```text
  locations: templates/parameters/bss_credentials_b2b.yml (open in repo)
```

Do **not** repeat `.username/.password` per macro - structure column covers that.

### Block 4 - Skipped (one line)

```text
Skipped (no migration action): 12 ParameterSet files without creds.get/credRef; Cloud/Tenant/Namespace templates use built-in credential string fields only (not converted to credRef).
```

### Block 5 - Warnings (non-blocking)

| kind | path | credId | message |
|------|------|--------|---------|
| technical_macro | `templates/parameters/technical_....yml` | `id_rabbitmq` | Out of migration scope |

### Block 6 - Decisions (numbered questions only)

Ask **only** what blocks draft. Example:

1. **Descriptor scope:** migrate `demo-b2b` first (recommended), `demo-b2c`, or both?
2. **Secret Store:** write `secretStore: default_store` on each Credential Template entry
   (recommended)? Schema default exists, but the Effective Set calculator has no runtime fallback.
3. **Rows marked review** - confirm per credId or batch by rule (see table row `id_dbaas_admin`).
4. **Secrets already in external store?** For confirmed template-owned creds: omit `create`
   (recommended when transferring from Jenkins) vs `create: true` for EnvGene-generated creds.

Do not ask abstract questions ("are these Cloud Passport groups correct?") without tying them to
specific `credId` rows marked `review` or `ask`.

### Block 7 - Next step

```text
Next: after you confirm decisions 1-N, run draft_credential_template.py --plan for demo-b2b.
```

---

## Instance Repository (`migrate-instance-repository`)

### Block 1 - Summary

```markdown
## Preflight report | Classify report

- Repository: current repo (--repo .)
- Status: ok | NEEDS_INPUT
- Environments: N | Credential files: M | Unique credIds: K
- Blockers: count | Warnings: count | needsReview: count
```

### Block 2 - Blockers (preflight)

| kind | path | credId | message |
|------|------|--------|---------|
| shared_ref_has_extension | `.../env_definition.yml` | - | sharedMasterCredentialFiles includes `.yml` |

### Block 3 - Classify inventory

**One row per `credId`:**

| credId | tier | scope | source file(s) | owner (proposal) | create | remoteRefPath (proposal) | writeToStore (plan) | review |
|--------|------|-------|----------------|------------------|--------|------------------------|---------------------|--------|
| ID_CLOUD_ONLY | passport-tier | cluster | `.../cluster-creds.yml` | pre-existing | omit | `cluster` | true | no |
| consul | system-tier | system | `configuration/credentials/...` | provider | omit | `external` | false | **yes** |

`writeToStore` is **plan-only** - never written to YAML. Flag `true` when passwords and tokens must
be copied
from Jenkins or Git during migration.

Locations: repo path only, no `data` preview.

### Block 4 - Skipped / out of scope

```text
Out of scope: deployer credentials (delete, do not convert); generated Credentials/credentials.yml (cleanup phase).
```

### Block 5 - Decisions

Numbered questions tied to rows with `review: yes` or `needsReview: true` in classify JSON.

### Block 6 - Next step

```text
Next: record confirmed decisions JSON, then convert_credential_files.py --plan for passport-tier files.
```

---

## Anti-patterns (do not send to the user)

- Pasting full ParameterSet YAML to prove "no macros here"
- Listing every file as "File 11:", "File 12:" with contents
- One bullet per `.username` reference (41 lines for one credId)
- Asking the user to classify Cloud vs Shared vs Template without a credId column
- Inventing `create` or path for provider-marker credIds before confirmation
