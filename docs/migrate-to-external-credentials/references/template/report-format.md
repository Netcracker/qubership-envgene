# Analyze and preflight report format (Template Repository)

Use this format when presenting `preflight.py` or `inventory_credids.py` results to the user.
Scripts emit JSON - the agent **summarises** that JSON. Do not dump repository file contents.

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

## Template Repository (mode `template`)

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
| technical_paramset_sets | `.../b2b.yml.j2` | - | technical sets still contain creds.get | Move macros out of those sets |
| technical_macro | `.../cloud.yml.j2` | `app-db-cred` | creds.get in technicalConfigurationParameters | Move / remove / outside EnvGene / defer |

`technical_paramset_sets` is a **blocker only when the bound ParameterSet files still contain
`creds.get` / `#creds`**. If the list is non-empty but macros are already gone, that is a
**warning** - continue; do not stop the migration for the binding alone.

When severity is blocker and `kind` is `technical_paramset_sets` or `technical_macro`, show this
callout:

```markdown
> [!CAUTION]
> **Stop before External Credentials cutover**
>
> Credential macros remain under technical configuration (inline or via
> technicalConfigurationParameterSets). `$type: credRef` is not supported there.
>
> | kind | path | sets / credId |
> |------|------|---------------|
> | technical_paramset_sets | `templates/.../b2b.yml.j2` | `technical_B2B_configuration_R23.3` |
>
> Choose one:
> 1. **Move secrets** (`creds.get` / `#creds`) into deploy/e2e ParameterSets, then re-run
>    preflight (recommended). Clearing macros is enough; removing the
>    `technicalConfigurationParameterSets` binding is optional and separate.
> 2. **Remove** unused technical sets / macros
> 3. **Keep outside EnvGene** (not External Credentials)
> 4. **Defer** cutover until this is decided
>
> Reply with the option number (recommended: **1**).
```

Stop after this block until the user fixes blockers and preflight exits `0`.

### Block 3 - Credential inventory (analyze / preflight credentials list)

Do not surface `owner`/`confidence`/`evidence` field names or values to the user - those stay
internal to the JSON. The only choice the user makes per `credId` is the create state:

- **Keep as-is** - `create` is omitted from YAML; the secret already exists in the target store,
  EnvGene must not generate a new value.
- **Generate new** - `create: true`; EnvGene generates a fresh login/password on apply.

**Compact default (save tokens):**

1. Summary counts: total credIds, proposed "generate new" count, proposed "keep as-is" count,
   needs-a-decision count (structure conflict/unknown only).
2. Group credIds by proposal and print each group as **one comma-separated line**, not a table:

```text
Proposed "generate new" (N): env_admin_password, app_db_cred, ...
Proposed "keep as-is" (M): consul-token, id_dbaas_admin, ...
Needs a decision (K): id_nifi_sensitive_key
```

The "keep as-is" group comes from a name/marker match (known provider substrings or naming
patterns) - flag it as a signal to confirm, not proof: `Proposed "keep as-is" (M) - matched known
patterns, please confirm: ...`.

3. **Full table only** for the "needs a decision" group (structure conflict/unknown -
   no pattern matched either way):

| credId | why it needs a decision | your choice |
|--------|--------------------------|--------------|
| id_nifi_sensitive_key | no known pattern matched, structure is ambiguous | keep as-is / generate new |

Do **not** paste a full 40+ row table when most credIds fall into one of the two proposal groups.

**Accepted replies:**

- `accept` - apply every proposal shown above (both groups) as-is
- `keep all as-is` - set every remaining undecided credId to "keep as-is"
- `generate all new` - set every remaining undecided credId to "generate new" - **before
  applying, warn the user first**: this regenerates the login/password for every credId in the
  batch, including ones that may already be live in Vault or another store; only proceed after
  explicit confirmation
- Per-credId replies: `credId: keep as-is` or `credId: generate new`

Do **not** repeat `.username/.password` per macro - structure is only relevant for the "needs a
decision" table.

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
3. **Credentials needing a decision** (Block 3 "Needs a decision" group) - confirm per credId:
   keep as-is or generate new (see table row `id_nifi_sensitive_key`).
4. **Bulk replies** - remind the user they can reply `accept`, `keep all as-is`, or
   `generate all new` instead of answering per credId (the last one needs an explicit
   confirmation before it is applied - see Block 3).

Do not ask abstract questions ("are these Cloud Passport groups correct?") without tying them to
specific `credId` rows marked `review` or `ask`.

### Block 7 - Next step

```text
Next: after you confirm decisions 1-N, run draft_credential_template.py --plan for demo-b2b,
then --apply to write the keep-as-is/generate-new choices above as create/remoteRefPath in the
Credential Template.
```

---

## Anti-patterns (do not send to the user)

- Pasting full ParameterSet YAML to prove "no macros here"
- Listing every file as "File 11:", "File 12:" with contents
- One bullet per `.username` reference (41 lines for one credId)
- Asking the user to classify Cloud vs Shared vs Template without a credId column
- Inventing `create` or path for provider-marker credIds before confirmation
