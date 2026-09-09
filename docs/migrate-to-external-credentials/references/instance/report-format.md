# Analyze and preflight report format (Instance Repository)

Use this format when presenting `preflight.py`, `inventory.py`, or `classify_credentials.py`
results to the user. Scripts emit JSON - the agent **summarises** that JSON. Do not dump
repository file contents.

Policy: [credential-policy.md](credential-policy.md).

## Global rules

- **Do not paste file contents** the user can open in the repository. Give repo-root paths only.
- **Do not paste full preflight / inventory JSON** into the chat. Summarise from the script
  output (or from a saved `--out` file). Tool JSON stays in the tool result - do not echo it.
- **Compact inventory (default):** full cred table only for rows that need a decision
  (`ask` / `review: yes` / structure conflict). Batch the rest in one line.
- **One table row per `credId`**, not per macro occurrence or per file - and only for rows you
  show in full.
- **Skipped files:** one summary line with count and example paths - no YAML excerpts.
- **Blockers and warnings:** `kind`, repo path, `credId` (if any), one-line message. Link to
  `suggested_action` when the script provides it.
- **Questions:** numbered list with a recommended option first. Ask only open decisions - do not
  re-ask what the script already resolved.
- **Never print** `data` values or actual passwords or tokens.
- **Built-in string fields** (`credentialsId`, `tokenSecret`, `defaultCredentialsId`,
  `credential`, plain strings like `GIT_CREDS_ID: github-cred`): one skip summary - do not list
  every field value.
- After the report, state the **single next command** (for example re-run preflight, or
  `draft_credential_template.py --plan` after confirmations).
- Do not re-run preflight unless blockers were fixed or the user asked. After a re-run, show
  **delta only** (new/resolved blockers), not a full repeat of the previous inventory table.

---

## Instance Repository (mode `instance`)

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
