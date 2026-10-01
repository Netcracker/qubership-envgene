---
name: external-creds-migration-skills
description: >-
  End-to-end EnvGene External Credentials migration. Guides Template Repository
  cutover (T1–T4), Instance Repository cutover (I1–I7), or secret transfer
  (collect / export / fill). Invokes envgene_migrate and migration-cli. Use when
  starting external-creds migration or when the user asks which phase to run.
triggers:
  - /external-creds-migration
  - external credentials migration
  - migrate external creds
  - envgene migrate external creds
disable-model-invocation: true
---

# External Credentials migration

Prefer kit CLIs. Do not invent `remoteRefPath`, `create`, or secret values.
Commands live in [commands.md](commands.md) — do not paste long install blocks here.

- [Welcome (say this first)](#welcome-say-this-first)
- [Modes](#modes)
- [Assumptions](#assumptions)
- [Hard constraints](#hard-constraints)
- [When the agent stops](#when-the-agent-stops)
- [CLI layout](#cli-layout)
- [After the mode ends](#after-the-mode-ends)

## Welcome (say this first)

```markdown
## External Credentials migration

Today secrets often live in Git. After migration, Git keeps only links to secrets;
the real values live in your Secret Store.

**Before we start (you):**
1. Clone the Template and/or Instance repo(s) you will migrate
2. Create a feature branch in each (do not run this migration on main / master)
3. Use Python 3.12.x for the kit CLIs (a 3.12 venv is fine; other versions are unsupported)
4. Tell me the full folder paths on your PC to those repos

**How to answer later:** short replies are OK — for example y / n, done, ready —
when I show Reply: …

**I will:** scan your repos, prepare a change plan, explain what will change, and
apply it after you confirm.
**You will:** answer a few questions, confirm the plan, commit when you choose to,
and run pipelines when a step needs you to.

I will not show secret values, invent secret paths, silently edit your credential
files, or commit/push unless you ask.

### Where should we start?

Answer what you can. If you don't know, say so.

1. Do you have a Template Repository to update? If yes — full folder path on the feature branch.
2. Do you have an Instance Repository to update? If yes — full folder path on the feature branch.
3. Where are the secret values today — in Git, only in Jenkins, or already in a Secret Store?
   (Rare: if you want Instance apply to write non-system secrets into the Store
   during cutover, say so — that is `apply_store`, not the default.)

I will choose the order. You do not need to pick a mode.
```

After the operator answers question **3**, **before** Instance I2 plan, write (or
merge into) `migration-plan.yaml` under the Instance repo root:

```yaml
operator_decisions:
  values_source: git          # or jenkins | store | apply_store
```

| Answer | `values_source` | Effect |
|--------|-----------------|--------|
| In Git | `git` | Non-system `writeToStore: false`; Collect step before I4 |
| Only in Jenkins | `jenkins` | Non-system `writeToStore: false`; **skip** Git collect |
| Already in Secret Store | `store` | Non-system `writeToStore: false`; skip Collect / Transfer values |
| Explicitly write Store **during** Instance apply | `apply_store` | Non-system `writeToStore: true` (rare; not the Git default) |

Re-plan **carries** `operator_decisions` (including `values_source`). Do not invent
the value — if missing after Welcome, ask once and write it before I2.

Load the matching mode file and stay on it until that mode ends.  
If both Template and Instance are in scope, finish Template (through publish) before Instance apply.

**Do not** silently widen scope: Instance plan defaults to the **whole repo**. Use
`plan --repo=instance --env CLUSTER/ENV` only when the user explicitly asks for one env (debug).

**Values in Git (order):** Template T1–T4 → Instance I0–I3 → `migration-cli collect`
(values file outside the repo) → I4 apply Git-only → Transfer (ES
`EXTERNAL_CREDENTIAL_PROVISIONING=skip` → fill → provision) → Template version
check → I5–I7. See [mode-instance.md](references/mode-instance.md).

**Progress UX (every mode):** on the **first** turn in a mode, show that mode’s full
checklist once (`- [ ]` steps). On later turns, do **not** reprint the whole list.
End **every** in-mode reply with this sticky block only (English):

```text
---
Now: <Mode> → <step id and short name> · step k of N
Next: <next concrete checklist step>
---
```

Do **not** put the full navigation footer (1/2/3/4) in mid-mode replies. Full
footer remains end-of-mode (or when the user asks to change mode). Details stay
in the mode file.

## Modes

| Mode | When | Load next |
|------|------|-----------|
| `template` | Template YAML phase | [references/mode-template.md](references/mode-template.md) |
| `instance` | Instance YAML phase | [references/mode-instance.md](references/mode-instance.md) |
| `transfer` | Values → Store via Context | [references/mode-transfer.md](references/mode-transfer.md) |

Also: [plan-review.md](references/plan-review.md), [override-guide.md](references/override-guide.md).

## Assumptions

Background facts the agent should not re-derive or fight — not
operator-facing rules (see Hard constraints for those).

- One Secret Store per repository (`default_store`). Every rewritten `type:
  external` entry sets `secretStore: default_store` (schema / env-build
  require the field; not left empty).
- No-CMDB assumed already in place. Deployer credentials are out of
  migration scope entirely — delete only, never migrated to `type:
  external`.
- Migration processes SOURCE credential files only. Generated
  `<env>/Credentials/credentials.yml` go to `to_delete` and are regenerated
  by env-gen after migration.
- Git-tracked credential values do not change between `plan` and `apply` —
  Collect happens once, before apply, not re-read at apply time.
- Runtime/technical macros: pipeline fails if references remain after
  cutover — the operator must remove them (Template) or waive knowingly
  (Instance); the skill never auto-removes them. ParameterSets bound only
  via `technicalConfigurationParameterSets` follow the same rule.
- Template Credential Template is built only from Template Descriptor
  closure (YAML parse plus text scan, so Jinja `{% if %}` list items and
  Built-in `credentialsId` still count as bound). A descriptor with **0**
  reachable object files is a plan STOP. Unbound ParameterSets are reported
  only — never rewritten, deleted, or added to the CT.

### Known gaps (name them; do not invent a fix)

- **`<ns>` in env-tier `remoteRefPath`:** Template default is
  `{{ current_env.cloud }}/{{ current_env.name }}` (no namespace). Operator
  may append `/{{ current_env.namespace }}` (or a literal ns) via override
  when per-namespace granularity is required.
- **`create` vs 3-value enum:** target wants `create` / `verify` / `skip`.
  Today only boolean `create`. Provider-generated creds: use `create: false`
  + `writeToStore: false` and capture out-of-band.

### Open items (product / follow-ups)

- `envgene provision-cp-creds` — post-migration BAU for passport `create:
  true` (not in this kit)
- Classification signal engine completion (cross-env hashing, cross-ns
  analysis)
- Post-provider capture conventions — guidance only
- `known_creds.py` registry still empty (populate from real-repo snapshot
  when available)
- Cloud Passport lookup when not listed in `env_definition` — deferred

## Hard constraints

Universal and cross-mode rules only. Mode-specific rules live in the mode file
loaded for that phase - do not rely on this section alone for Template / Instance /
Transfer detail.

- Never invent `create` or `remoteRefPath`. Stop and ask.
- Always invoke `envgene_migrate` / `migration-cli` for scan and rewrite. Do **not**
  decide migration by reading YAML yourself and hand-editing source credentials,
  Credential Templates, or consumers as a substitute for plan/apply. Edit only
  `migration-plan.yaml` (with the operator) before apply.
- **Minimal edit:** when fixing one `migration-plan.yaml` entry or one credRef /
  macro line, change **only** those lines (or that entry). Do not rewrite the whole
  file and do not touch already-agreed neighbor entries. Prefer the CLI surgical
  apply for consumers; do not dump YAML by hand.
- Never print secrets. Never commit collect / export / fill / collect-system outputs.
  Before `collect-system`, **ask** for absolute `--out` path (prefer outside the
  instance repo); do not invent it or silently write inside the Git tree.
- Never commit, push, merge, publish, or run pipelines unless asked.
- After Template or Instance **apply** (any bulk Git rewrite): show a short summary,
  let the operator review, then ask commit with `Reply: y | n | later`. Run
  `git add` / `git commit` **only** on `y`. Never silent commit. Do not
  `git add -A` blindly; never stage collect/export/fill/provision plaintext.
- `plan` before `apply`. Commit of `migration-plan.yaml` is **optional** (apply
  reads the local file).
- Do not append `credId` to `remoteRefPath`. Paths have **no leading `/`**
  (`global`, `<cluster>`, `<cluster>/<env>`) — same shape as EnvGene samples.
- **Runtime / technical macros (Instance):** plan lists `runtime_credential_macros`.
  Show WARNING + Questions A/B (see plan-review Instance). Reply **A** → set
  `operator_decisions.technical_macros_waive: true` (apply may continue; pipeline
  may still fail until Template regenerate). Reply **B** → operator removes macros,
  then re-plan. Agent does not hand-edit Instance technical macros. Never run
  `strip-technical-macros` on Instance.
- **Runtime / technical macros (Template):** GATE STOP + Questions A/B (see
  plan-review Template). Reply **A** → operator deletes macros, then **`done`** →
  re-plan. Reply **B** → `strip-technical-macros --repo=template` → commit ask →
  re-plan. No waive in Template.
- Template rules - see [mode-template.md](references/mode-template.md).
- Instance rules - see [mode-instance.md](references/mode-instance.md).
- Transfer rules - see [mode-transfer.md](references/mode-transfer.md).
- System creds seed before Instance plan (collect-system → provision; plan keeps
  `create: false`, `global`, `writeToStore: false` unless I0 skipped) - see
  [mode-instance.md](references/mode-instance.md) I0 / I3.
- Never open Store sockets from the skill. Store writes (pick one path per cred):
  1. `migration-cli collect-system` → `external-cred-provision` (system),
  2. `envgene_migrate apply --repo=instance` when `writeToStore: true`,
  3. `migration-cli fill` → `external-cred-provision` (transfer) -
  not two of these for the same creds without an explicit reason (see commands.md).
- When Welcome said values are in **Git**: default Store path is Transfer after
  Git-only apply — do **not** ask writeToStore before I4; set non-system
  `writeToStore: false`. Collect all Git values **before** I4.
- Confirm before `external-cred-provision`.
- On CLI failure: stop; do not hand-edit migration logic. Quote the **file path**
  from the CLI error when present.
- **Batch review (docs-only):** walk `to_review` in batches by `sourceFile`, then
  write those answers into `migration-plan.yaml` once per batch. After `apply`,
  show `git diff` grouped by cluster / env / source - not one chatter line per file.
  The CLI validates at end of apply; do **not** claim mid-apply stop per file group
  unless the CLI itself failed and named a file.
- Keep user-facing talk short. Pass `--verbose` on CLI only when the user wants detail.
  **Operator-facing skill text is English only.**
- After every `plan`: lead with CLI **VERDICT / BLOCKERS / DECISIONS /
  Questions for you** (short). Then show the create/path spot-check block from
  [plan-review.md](references/plan-review.md); wait for **`checked`**. Copy CLI
  questions; map answers into `migration-plan.yaml`. Do **not** invent Group A/B/C
  or dump credId lists. Unbound ParameterSets are **INFO only** (not DECISIONS).
  STOP → do not apply.
- Do not use terms like `external-tier` or `shadow` with the user - say passport /
  system / shared / env-scoped.
- **Navigation:** if the user asks “where am I” / “what’s next” / change mode, show
  the **Now/Next** sticky mid-mode, or the **navigation footer** at mode end from
  the mode file. No separate “mode menu” command.

## When the agent stops

Single table for operator decisions. Reasons use **plan / GATE fields**, not code
names. Details: [plan-review.md](references/plan-review.md), mode preconditions.

| Situation | What the agent says | What the operator does |
|-----------|---------------------|------------------------|
| GATE `to_review` open | DECISIONS: confirm `create` / `remoteRefPath` (and Template `includeInCredentialTemplate` if asked) | Answer; agent writes only those plan entries |
| After plan (T or I) | Spot-check create/path block; wait **`checked`** | Open `migration-plan.yaml`; reply `checked` |
| Same credId in passport and shared | Ask which source is authoritative | Pick one; drop or `writeToStore: false` on the other |
| Template: `runtime_credential_macros` non-empty | STOP + Reply **A** or **B** | A → operator deletes + `done` + re-plan; B → `strip-technical-macros` + re-plan |
| Instance: `runtime_credential_macros` non-empty (no waive) | WARNING + Reply **A** or **B** | A → waive in plan; B → remove macros + re-plan |
| `to_delete.deployer_credentials` set, no `operator_decisions.deployer_delete` | STOP — deployer delete undecided | Set `operator_decisions.deployer_delete: true` or `false` (`true` also strips `inventory.deployer` from related `env_definition.yml`) |
| `to_delete.unused_shared_credentials` set, no `operator_decisions.unused_shared_delete` | STOP — unused shared delete undecided | Set `operator_decisions.unused_shared_delete: true` (delete) or `false` (keep files in Git) |
| Mode precondition failed (missing Store, auth env, `environments/`, Template not published when required) | STOP before any work — list what is missing | Fix paths / Store / publish, then restart mode |
| Python is not 3.12.x | STOP — kit CLIs need 3.12; do not upgrade Python for the user | Operator installs/uses 3.12 (venv OK), then re-run Set up in [commands.md](commands.md) |
| Store/provision TLS / certificate verify error | STOP — quote the error; warn that a company CA may be required (not always) | Operator installs CA / sets TLS trust env; see [commands.md](commands.md) Store auth section |
| Instance: CI/CD Secret Store variables not confirmed | STOP — show mode-instance CI/CD message; wait for **done** | Operator sets Store vars in Instance CI/CD, then continues |
| Instance: before local I0 provision | STOP — show Local auth block; wait for **ready** | Operator sets Store auth on this machine |
| Before I5 | Ask published Template version; run `check-template-version --expect …` | Fix `envTemplate.artifact` if fail; reply **`updated`** or re-run check |
| After apply | Ask commit `y` / `n` / `later` | Explicit `y` only if agent should commit |
| `plan_errors` / mixed local+external / Cyrillic paths | STOP — plan invalid | Fix repo / types, re-plan |
| CLI apply / provision failure | STOP — quote CLI error and file if named | Fix cause; do not hand-edit migration logic |
| Out of skill (CMDB import, multi-store map, inventing secret values, autonomous content decisions) | Say this skill does not automate that | Operator handles outside the kit |

## CLI layout

| Piece | Path |
|-------|------|
| Commands (canonical) | [commands.md](commands.md) |
| YAML plan/apply | [scripts/python/envgene_migrate/](scripts/python/envgene_migrate/) |
| Transfer | [scripts/cli/](scripts/cli/) (`migration-cli`) |
| Transfer flags/examples | [scripts/cli/README.md](scripts/cli/README.md) |
| Secret Store writes | [scripts/external-cred-provision/](scripts/external-cred-provision/) (`external-cred-provision`) |

## After the mode ends

End the last reply with the **navigation footer** from the mode file
([mode-template](references/mode-template.md), [mode-instance](references/mode-instance.md),
or [mode-transfer](references/mode-transfer.md)). Do **not** start the next mode
unless the user chooses an option from that footer (or clearly asks for it).
