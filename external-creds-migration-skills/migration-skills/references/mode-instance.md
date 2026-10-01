# Mode: Instance Repository

Stay until I7 handoff. Needs published Template from T4.  
Commands and Store env vars: [commands.md](../commands.md).  
Store path vs transfer: [Store table](../commands.md#when-to-write-the-secret-store-pick-one-path).  
Progress UX: [SKILL.md](../SKILL.md). Stops: [When the agent stops](../SKILL.md#when-the-agent-stops).

## Preconditions (before any Instance work)

Run **before I0 / I1 / plan**. STOP immediately if any check fails — list exactly
what is missing:

- [ ] Instance repo root is readable
- [ ] `environments/` exists (expected env tree)
- [ ] `configuration/secret-stores.yml` with `default_store` (create in I1 only if
      missing — still do not run plan/apply until it exists)
- [ ] Store auth env vars for that store type ([commands.md](../commands.md) table)
      when I0 or `writeToStore: true` will need them
- [ ] Template published for the credIds you rely on (T4), unless the user only
      wants Git-structure cutover of already-known Instance files

Do not start collect-system, plan, or apply until preconditions pass (or the user
explicitly waives a named item).

## Hard rules (Instance)

- One `default_store` - create via `envgene_migrate.secret_store.write_secret_stores`
  (skill passes JSON; no separate CLI). Ask type-specific fields only
  (`mountPath` / `projectId` / `region` / `vaultName`) - **do not** ask for Store
  `url` as the server address (Vault uses `VAULT_ADDR`; GCP uses `projectId` + ADC).
- **Values path (`operator_decisions.values_source`):** set after Welcome — mapping
  in [SKILL.md Welcome](../SKILL.md#welcome-say-this-first). After I3, branch
  Collect UX on that field (do not guess from chat).
- **Values in Git (`git`):** before I4, run `migration-cli collect` (or
  skip-collect if file exists). I0 `collect-system` does **not** replace that.
  I4 is **Git only** for non-system. Store later via Transfer
  (`EXTERNAL_CREDENTIAL_PROVISIONING=skip` → fill → provision).
- Deployer: ask delete yes/no; write `operator_decisions.deployer_delete`; apply
  blocks until set — full strip/`inventory.deployer` rules in
  [plan-review.md](plan-review.md) item 11.
- Unused shared: ask delete yes/no; write
  `operator_decisions.unused_shared_delete`; apply blocks until set — question
  and yaml in [plan-review.md](plan-review.md) item 12.
- Instance apply (CLI, not hand-edit): rewrite passport main + system consumers
  (`integration.yml` / `deployer.yml` / `registry.yml`) macros → credRef (including
  bare `envgen.creds.get`); scan `shared-credentials/` as well as `credentials/`;
  strip `.yml` from `sharedMasterCredentialFiles`; change consumers **surgically**
  (macro lines only - do not dump whole YAML files).
- Do not migrate `technicalConfigurationParameters` macros to credRef. GATE shows
  WARNING + A/B; waive with `operator_decisions.technical_macros_waive: true` on A.
- Do **not** bulk-edit `env_definition.yml` template artifact versions - operator
  updates `envTemplate.artifact`, then agent runs `check-template-version`.
- System creds (`configuration/credentials/`): seed Store first with
  `migration-cli collect-system` → `external-cred-provision` (no fill). In the
  Instance plan they are `create: false`, path `global`, `writeToStore: false`
  unless the operator skipped that step (I0 / I3).
- **CI/CD Secret Store variables (manual):** as soon as `default_store.type` is
  known, show the message in [CI/CD Secret Store variables](#manual-cicd-secret-store-variables-show-once)
  and **wait for operator "done"**. Do not run I0 provision, apply with
  `writeToStore: true`, or ask for I5 env-gen until they confirm. The skill does
  not create CI/CD variables.
- **Local auth (this machine):** before local I0 provision, show
  [Local auth](#manual-local-auth-show-once) and **wait for "ready"** (not `done`).

## Checklist (show once at mode start)

- [ ] I0 — System credentials into Store
- [ ] I1 — Secret Store config
- [ ] CI/CD — Secret Store variables in Instance CI/CD (manual; once)
- [ ] I2 — Plan + GATE
- [ ] I3 — Review plan
- [ ] Collect (Git values path) — before I4 when values are in Git
- [ ] I4 — Apply (Git only on Transfer path)
- [ ] Transfer — skip → fill → provision (Git values path)
- [ ] Template version check — before I5
- [ ] I5 — env-gen
- [ ] I6 — deploy test
- [ ] I7 — merge

Later turns: end every reply with the **Now / Next** sticky (English) from
[SKILL.md](../SKILL.md); do not reprint this list.

### Manual: CI/CD Secret Store variables (show once)

Show as soon as `default_store.type` is known (existing `secret-stores.yml` or after
I1). The first env-gen pipeline often fails without these. **Wait for "done"**
before I0 provision, before apply with Store write, and before I5.

Say this to the operator (pick the section that matches their store type; you may
show all sections):

```markdown
## Manual step: configure the external Secret Store in CI/CD

Before we write secrets to the Store (local provision or the env-gen pipeline),
set CI/CD variables on the **Instance** repository
(Settings → CI/CD → Variables). Mask / protect them per your policy.
This skill does **not** create CI/CD variables for you.

Use the row that matches your `default_store.type` in
`configuration/secret-stores.yml`:

### Vault / OpenBao (`type: vault` or `openbao`)
| Variable | Meaning |
|----------|---------|
| `VAULT_ADDR` | Vault/OpenBao server URL (HTTPS) |
| `VAULT_TOKEN` | Auth token |

If HTTPS uses a company CA, also trust that CA on the runner (or you may see
certificate verify errors). Public CA usually needs nothing extra.

### GCP Secret Manager (`type: gcp`)
| Variable | Meaning |
|----------|---------|
| `GOOGLE_APPLICATION_CREDENTIALS` | Path on the runner to the service-account JSON key file |

### AWS Secrets Manager (`type: aws`)
| Variable | Meaning |
|----------|---------|
| `AWS_ACCESS_KEY_ID` | Access key |
| `AWS_SECRET_ACCESS_KEY` | Secret key |
| `AWS_DEFAULT_REGION` | Region (e.g. `eu-central-1`) |

### Azure Key Vault (`type: azure`)
| Variable | Meaning |
|----------|---------|
| `AZURE_TENANT_ID` | Tenant ID |
| `AZURE_CLIENT_ID` | App (client) ID |
| `AZURE_CLIENT_SECRET` | Client secret |

When the variables for your store are set, reply **done** and we continue.
```

### Manual: Local auth (show once)

Show **after** CI/CD `done`, **before** local I0 `external-cred-provision`. Wait for
**ready**. Do not merge this into the CI/CD message. Do not ask for JSON/token
contents in chat. Pick the section for `default_store.type`.

```markdown
## Local auth (this machine only)

I0 will write system secrets to the Store from this computer.

### GCP (`type: gcp`)
1) Get a GCP service-account JSON key (ask your GCP/DevOps owner if needed).
2) Save it outside the Instance repo (not inside the Git checkout).
3) In the same terminal we use for commands:

   $env:GOOGLE_APPLICATION_CREDENTIALS = "C:\path\to\gcp-sa.json"

### Vault / OpenBao (`type: vault` or `openbao`)
Set `VAULT_ADDR` and `VAULT_TOKEN` in this terminal (same names as CI/CD).

### AWS (`type: aws`)
Set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION` in this terminal.

### Azure (`type: azure`)
Set `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET` in this terminal.

Reply **ready** when set.
Do not paste secret contents into chat.
```

### I0 — System credentials into Store (first)

Do this **before** Instance YAML apply (and ideally before relying on ES that needs
git/registry tokens).

- [ ] `configuration/secret-stores.yml` with `default_store`
- [ ] Operator confirmed CI/CD Secret Store variables (**done** on the message above)
- [ ] Operator confirmed Local auth (**ready** on the message above) before local provision
- [ ] **Ask the operator** for an absolute filesystem path for `--out` (provision
      context file with plaintext). Prefer a path **outside** the instance Git
      repo (Desktop / temp). Do **not** invent the path or default into the repo
      without asking.
- [ ] Build provision context (no fill):

```bash
migration-cli collect-system \
  --instance-root <instance-repo> \
  --out <operator-chosen-absolute-path>
```

- [ ] Confirm with user, then:

```bash
external-cred-provision <same-out-path>
# optional: --dry-run first
```

- [ ] Do not commit the `--out` file (contains plaintext); delete when done if desired

### I1 — Secret Store (operator)

- [ ] If missing: skill asks type + type-specific fields (`mountPath` /
      `projectId` / `region` / `vaultName`) - **not** Store `url` as server
      address (Vault host is `VAULT_ADDR`; GCP uses `projectId` + ADC) - then
      calls `envgene_migrate.secret_store.write_secret_stores` (Python - not a
      CLI command)
- [ ] `configuration/secret-stores.yml` with single `default_store`
- [ ] After type is known: show [CI/CD Secret Store variables](#manual-cicd-secret-store-variables-show-once)
      if not already shown; wait for **done**

### I2 — Plan

- [ ] Whole repo (default):  
      `python -m envgene_migrate plan --repo=instance --root <instance-repo>`
- [ ] One env only if the user explicitly asks (debug):  
      `python -m envgene_migrate plan --repo=instance --root <instance-repo> --env CLUSTER/ENV`
- [ ] Do not silently expand beyond what the user asked
- [ ] Show GATE (VERDICT / BLOCKERS / DECISIONS); `--verbose` for full lists
- [ ] If plan exits with PLAN ERRORS (Cyrillic paths, mixed local+external) — stop and fix

### I3 — Review plan

- [ ] [plan-review.md](plan-review.md) + [override-guide.md](override-guide.md) - GATE first
- [ ] Show create/path spot-check (plan-review); wait for **`checked`**
- [ ] Passport/system: auto (`create: false`; system path `global`,
      `writeToStore: false` after I0; set true only if I0 was skipped)
- [ ] Everything else: walk `to_review` in batches by `sourceFile` (minimal edit)
- [ ] Passport vs shared duplicate: ask authoritative source
- [ ] Runtime / technical macros: WARNING + Reply A/B (waive or operator deletes);
      not automatic CRITICAL
- [ ] Deployer creds: ask delete yes/no → `operator_decisions.deployer_delete`;
      if `true`, apply also strips `inventory.deployer` from related
      `env_definition.yml`
      (apply blocks until set; if false, warn pipeline may fail)
- [ ] Unused shared creds: ask A/B → `operator_decisions.unused_shared_delete`;
      apply blocks until set; if `false`, keep the files in Git
- [ ] Commit of `migration-plan.yaml` is **optional**

### Collect before I4 (branch on `operator_decisions.values_source`)

Read `values_source` from the plan. **Do not guess** from chat history. If missing,
ask once (`git` / `jenkins` / `store` / `apply_store`), write it, then continue.

#### `values_source: git`

```text
I3 done. Secret values are still in Git.
Next: save them outside the repo (migration-cli collect), then I4 Git-only
(writeToStore: false). Store later via Transfer (skip → fill → provision).

Reply: collect — run collect now (I will ask for absolute --out)
       skip-collect — values file already saved at <absolute path>
```

- [ ] Absolute `--out` outside the repo; do not invent it
- [ ] `migration-cli collect … --out <path>` (unless skip-collect)
- [ ] Do not commit the values file
- [ ] Non-system keep `writeToStore: false`

#### `values_source: jenkins`

```text
I3 done. Values are in Jenkins — skip Git collect.
I4 apply will be Git-only (writeToStore: false).
Store later: ES skip → export-credentials → fill → provision.
```

- [ ] Do **not** run `migration-cli collect`
- [ ] Non-system keep `writeToStore: false`

#### `values_source: store`

```text
I3 done. Values are already in the Secret Store — skip Git collect / Transfer fill.
I4 apply will be Git-only (writeToStore: false).
```

- [ ] Do **not** run collect or Transfer provision for those creds
- [ ] Non-system keep `writeToStore: false`

#### `values_source: apply_store` (rare)

```text
I3 done. You chose Store write during Instance apply.
I4 will use writeToStore: true for non-system (confirm before apply).
```

- [ ] Confirm Store auth; do **not** also Transfer-provision the same creds

### I4 — Apply

#### When values=Git / Jenkins / store (not apply_store)

```text
I3 done. Next is I4 apply (Git only).
Secret values for non-system creds will go to the Store later via Transfer
(skip → fill → provision) when values_source is git (or export path for jenkins).
System creds are already in the Store from I0.

Shall I run apply?
```

- [ ] Clean Git; `SOPS_AGE_KEY` if needed
- [ ] Non-system: `writeToStore: false` (no pre-apply Store-write question)
- [ ] `python -m envgene_migrate apply --repo=instance --root <instance-repo>`
- [ ] On CLI failure: quote error + file path; stop
- [ ] Show migration-report; user reviews `git diff` grouped by cluster/env/source
- [ ] Ask commit (English):

```text
I4 apply finished: <N> files changed, <S> Store writes.

Please review the changes (summary above / git status).

Commit these changes to the migration branch now?
Reply: y — commit | n — leave uncommitted | later — you commit yourself
```

Commit / `git add` **only** on `y`. Never stage collect/fill plaintext.

#### When `values_source: apply_store`

- [ ] Confirm Local auth (**ready**) before apply (show Local auth block if not yet)
- [ ] Confirm non-system entries have `writeToStore: true` (plan default when
      `values_source: apply_store`; per-cred override still allowed)
- [ ] Clean Git; `SOPS_AGE_KEY` if needed; Store auth env vars on this machine
- [ ] `python -m envgene_migrate apply --repo=instance --root <instance-repo>`
- [ ] On CLI failure: quote error + file path; stop
- [ ] Show migration-report; user reviews `git diff` grouped by cluster/env/source
- [ ] Ask commit with the same `Reply: y | n | later` block as above
- [ ] Do **not** also Transfer-provision the same creds

### After I4 Git-only → Transfer (values were in Git)

Do **not** jump to normal I5. Say:

```text
Step done: Git now has links to the Secret Store (not the secret values themselves).

Next, fill the Secret Store:

1) Run the Effective Set / env-gen pipeline on the migration branch.
2) Set job parameter:
   EXTERNAL_CREDENTIAL_PROVISIONING = skip
3) Wait until the job succeeds.
4) Update your local Instance checkout (git pull on this branch)
   and reply pulled.

Then I will match credentials and, with your confirmation, write secrets to the Store.
System credentials from I0 are already in the Store — we will not touch them.
```

Then Transfer: fill (existing collect file) → confirm → `external-cred-provision`.
Do **not** re-collect from Git as the default next step after I4.
Wait for **`pulled`** (not `ready` — that token is Local auth only).

### Before I5 — Template version check

- [ ] Ask: which Template version did you publish (T4)? Operator replies with the string.
- [ ] Run:

```bash
python -m envgene_migrate check-template-version \
  --repo=instance --root <instance-repo> \
  --expect <version-from-user>
```

- [ ] On fail: operator updates `envTemplate.artifact` in `env_definition.yml`;
      reply **`updated`** or re-run the check. Agent does not edit those files.
- [ ] On OK → continue I5

### I5–I7 (user)

- [ ] I5 env-gen on migration branch — only after CI/CD **done**, Template version
      check OK, and (on Git path) Transfer provision done
- [ ] I6 deploy test
- [ ] I7 merge Template branch, then Instance branch

## End of mode — navigation footer (required)

When I7 is done (or the user stops Instance here), the agent's **last reply in this
mode must end** with this footer. Fill `<cluster/env or whole repo>` from context.
Do not start another mode until the user picks an option.

```text
---
You are here: Instance → <cluster/env or whole repo> → done

What usually comes next:

1) Instance again — another environment or a wider plan scope (if you only did a subset)
2) Template — only if Template publish is still missing for the credIds you need
3) Transfer — when values were in Git: after I4 Git-only, or if Store is still empty
4) Stop — end of the usual Template → Instance chain

What do you choose? Reply with a number or in your own words.
---
```

## Notes

- Deployer creds: delete only after `operator_decisions.deployer_delete: true`
  (cluster or env `app-deployer/*-creds.yml`). Apply blocks until
  `operator_decisions.deployer_delete` is set; if `true`, also strip
  `inventory.deployer` from related `env_definition.yml` (not `noCmdbVersion`,
  not `deployer.yml`); if false, warn pipeline may fail.
  Generated env `Credentials/credentials.yml`: delete.
- Unused shared credential files
  (`to_delete.unused_shared_credentials`): delete only after
  `operator_decisions.unused_shared_delete: true`. Apply blocks until the key
  is set; if `false`, keep the files in Git.
- Do not migrate `technicalConfigurationParameters` macros.
- Apply (CLI): rewrite passport main + system consumers (`integration.yml` /
  `deployer.yml` / `registry.yml`) including bare `envgen.creds.get`; scan
  `shared-credentials/` as well as `credentials/`; strip `.yml` from
  `sharedMasterCredentialFiles`; change consumers surgically (macro lines only).
- Do **not** bulk-edit `env_definition.yml` template artifact versions - operator
  (or CI) updates Template version / regenerate.
- `envgeneNullValue`: Git rewrite still; Store skipped with warning.
