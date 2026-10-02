# Plan review (T2 / I3)

Never invent values. Never print secret `data`. Keep the chat short; point at the
plan file. Do not hand-edit source credential files or Credential Templates —
only `migration-plan.yaml`, then CLI apply. Operator-facing text is **English**.

## How to present (GATE first)

1. Copy the CLI **VERDICT / BLOCKERS / DECISIONS / Questions for you** block into
   chat (short). Do **not** invent Group A/B/C, do **not** list cred ID inventories.
2. Unbound ParameterSets are **INFO only** — not bound to any template → migration
   does **nothing** to those files (no leave/include/delete). Do not ask the
   operator to choose actions on them.
3. If the user asks for details — expand one section, or re-run plan with `--verbose`.
4. Use the CLI **Questions for you** letters when present (e.g. runtime macros).
5. **Spot-check create / path** (Template and Instance): after GATE, show the
   block below; wait for **`checked`** before continuing review/apply.
   Covers **to_review and AUTO**.
6. Walk open `to_review` in **batches by `sourceFile`**: confirm that batch, then
   write only those plan entries (minimal edit — do not rewrite the whole plan).
   Use A/B choices when needed; put recommended first. After apply, show
   `git diff` grouped by cluster / env / source — not one chatter line per file.
7. Passport/system autos: still require the spot-check (not “count only”).
8. Template: reachable creds default to `includeInCredentialTemplate: true`. Set
   `false` only to keep an id out of the CT.
9. Bound technical / runtime macros (`runtime_credential_macros`): WARNING + A/B
   (see below). Not CRITICAL by default.
10. Same cred-id in passport and shared: ask who is authoritative; do not guess.
11. Deployer creds (`environments/<cluster>/app-deployer/*-creds.yml` or env-level):
    ask delete yes/no; write into plan:

    ```yaml
    operator_decisions:
      deployer_delete: true   # or false
    ```

    If `true`, apply deletes those `*-creds.yml` **and** removes `inventory.deployer`
    from related `env_definition.yml` (cluster-level → all envs in cluster;
    env-level → that env). Leaves `noCmdbVersion` and `deployer.yml` alone.
    If `false`, warn pipeline may fail. Apply refuses until the key is set.
12. Unused shared credential files (`to_delete.unused_shared_credentials`):
    copy the paths from the plan into chat; ask A/B; write into plan:

    ```text
    [DECISION] Unused shared credential files

    These shared files are not referenced by any Environment Instance we scanned.
    Apply will delete them unless you choose to keep them.

      <paths from to_delete.unused_shared_credentials>

    A - Delete these files on apply
    B - Keep the files (they stay in Git)

    Reply: A or B
    ```

    ```yaml
    operator_decisions:
      unused_shared_delete: true    # A
      # unused_shared_delete: false # B
    ```

    If `true`, apply deletes those files. If `false`, keep them in Git.
    Apply refuses until the key is set. Skip this question when the list is empty.
13. If VERDICT is STOP — do **not** run apply.
14. **Store write before apply:** read `operator_decisions.values_source`. For
    `git` / `jenkins` / `store`, do **not** ask writeToStore; keep non-system
    `writeToStore: false`. Ask Store-write on apply only when `apply_store`.
    If `values_source` is missing, ask once and write it before Collect / I4.
15. Do not bulk-change `envTemplate.artifact` / template version in
    `env_definition.yml` — operator edits; then `check-template-version`.

## Spot-check create / path (wait for `checked`)

```text
Open migration-plan.yaml and check create / remoteRefPath (Template: also
includeInCredentialTemplate). Look at both to_review and AUTO.

create: true
  EnvGene may create the secret in the Store and generate values if missing.

create: false
  EnvGene does not generate it — only a link (remoteRefPath).
  The secret must be in the Store before env-gen: already there, or written by
  a migration Store step (I0 / writeToStore apply / Transfer provision).

Note: Cloud Passport and system credentials are often create: false on purpose.

You own these choices. Reply: checked
```

## Questions → plan edits

### Template — technical / runtime macros

```text
Questions for you:
1) technical/runtime credential macros
   A — I will remove these macros myself from the Template files, then reply done for re-plan
   B — Run strip-technical-macros (CLI removes hits), then re-plan
Reply like: 1A or 1B
```

| Reply | What to do |
|-------|------------|
| Tech `1A` | Wait for operator to edit Template YAML; on **`done`**, re-run `plan --repo=template`. Do not waive. |
| Tech `1B` | Run `python -m envgene_migrate strip-technical-macros --repo=template --root <template-repo>`. Show result; ask commit `y/n/later`; re-run `plan`. On CLI error (composite macro, bad YAML), quote the path and fall back to **A**. |

### Instance — technical / runtime macros

```text
Questions for you:
1) technical/runtime credential macros
   A — Already updated in the Template (continue; do not block apply on these hits)
   B — Delete now (you remove the macros from the listed Instance files, then we re-plan)
Reply like: 1A or 1B
```

| Reply | What to do |
|-------|------------|
| Tech `1A` | Set `operator_decisions.technical_macros_waive: true`. Warn: pipeline may still fail until Template regenerate. Do not hand-edit macros. Do **not** run `strip-technical-macros` (Template-only). |
| Tech `1B` | Operator removes macros in cited Instance files; skill re-runs `plan`. Do **not** mass-edit `namespace.yml` or bump `env_definition` artifact yourself. |
| Deployer | Set `operator_decisions.deployer_delete: true\|false`; if `true`, apply also strips `inventory.deployer` |
| Unused shared `A` | Set `operator_decisions.unused_shared_delete: true` (apply deletes the listed files) |
| Unused shared `B` | Set `operator_decisions.unused_shared_delete: false` (keep the files in Git) |

There is **no** leave/include/delete/bind for unbound ParameterSets.

## Instance create / path (do not invent)

| Source | create | remoteRefPath | Plan bucket |
|--------|--------|---------------|-------------|
| Cloud Passport (`*-creds.yml`) | `false` | `<cluster>` | auto (`to_confirm`) |
| System (`configuration/credentials/`) | `false` | `global` | auto (`to_confirm`); `writeToStore: false` after `collect-system` |
| Env / env-scoped shared | ask (suggestion `true`) | ask (suggestion `<cluster>/<env>`) | `to_review` |
| Cluster-level shared (not env-scoped) | ask (suggestion `false`) | ask (suggestion `<cluster>`) | `to_review` |
| Repo-level shared (`environments/shared-credentials`) | ask (suggestion `false`) | ask (suggestion `global`) | `to_review` |

System Store seed is **I0**: `migration-cli collect-system` → `external-cred-provision`
(no fill). `create: false` means EnvGene will not create the secret later at
generation time.

Non-Jinja `remoteRefPath` values use **no leading `/`** (`global`, `<cluster>`,
`<cluster>/<env>`).

## What the operator may edit

| Field | Template | Instance |
|-------|----------|----------|
| `remoteRefPath` | yes (Jinja string) | yes |
| `create` | yes | yes |
| `writeToStore` | n/a (ignored) | yes |
| `includeInCredentialTemplate` | yes (set `false` to exclude from CT) | n/a |

Cred-id keys are not editable in the plan (rename in the source file instead).
Cred type and `properties` are not in the plan; apply derives them from source.

## After edits

- [ ] Commit of `migration-plan.yaml` is **optional** (apply reads the local file)
- [ ] After apply: ask commit of Git results with `Reply: y | n | later` (only `y`
      → agent commits). Never silent commit.
- [ ] Proceed to apply (`T3` or `I4`) only if VERDICT allows (waive / decisions done)

STOP situations (GATE, deployer, preconditions, CLI failure): see
[When the agent stops](../SKILL.md#when-the-agent-stops).
