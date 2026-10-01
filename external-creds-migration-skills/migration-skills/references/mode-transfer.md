# Mode: transfer

Optional path for moving plaintext into the Secret Store via Context +
`external-cred-provision`. Not a substitute for Template/Instance YAML cutover.

Commands and flags: [cli/README.md](../scripts/cli/README.md).  
When to use vs Instance apply Store write: [commands.md](../commands.md#when-to-write-the-secret-store-pick-one-path).  
Entry skill: [../SKILL.md](../SKILL.md).  
Progress UX / stops table: [SKILL.md](../SKILL.md).

## Preconditions (before any Transfer work)

STOP immediately if any item fails — name what is missing:

- [ ] Operator confirmed Transfer (not Instance `writeToStore`) per commands.md table
- [ ] Store auth env vars set for the target store type ([commands.md](../commands.md))
- [ ] Absolute `--out` / Context path chosen by the operator (not invented into Git)

## Hard rules

- Never print secret values. Never commit collect / export / fill outputs.
- Ask the user before running `external-cred-provision`.
- One command at a time; wait between steps. Safe to re-run the same `--out`.
- For Jenkins / Context-fill paths: do not run export/fill until the operator
  confirms ES/env-gen with `EXTERNAL_CREDENTIAL_PROVISIONING=skip` (or confirms
  the parameter is unavailable — then STOP).
- Transfer `fill` unmatched: show recommendations from the report (credId
  mismatch, remove macro / create cred / fix credId) - walk each unmatched
  credId with the operator (see checklist step 6).
- System Store seed (`collect-system`) is **Instance I0**, not this mode. Use
  Transfer only for non-system collect / export / fill paths per
  [commands.md](../commands.md).

## Checklist (show once at mode start)

- [ ] 1 — Confirm Store path (transfer vs apply)
- [ ] 2 — Install CLI
- [ ] 3 — Optional transfer-config
- [ ] 4 — ES / env-gen with EXTERNAL_CREDENTIAL_PROVISIONING=skip (Context only)
- [ ] 5 — Collect or export-credentials
- [ ] 6 — Fill unmatched walk
- [ ] 7 — Confirm → external-cred-provision
- [ ] 8 — Remind next pipeline / hand off + footer

Later turns: end every reply with the **Now / Next** sticky (English) from
[SKILL.md](../SKILL.md); do not reprint this list.

1. [ ] Confirm Store path: transfer (this mode) vs `envgene_migrate apply` Store write — see commands.md table.
2. [ ] Install: `pip install -e <kit>/scripts/cli` (+ `.[decrypt]` if Fernet) and
      `pip install -e <kit>/scripts/external-cred-provision`. See [commands.md](../commands.md).
3. [ ] Optional: copy [transfer-config.example.yml](../transfer-config.example.yml) → `transfer-config.yml` for the agent (do not commit).
4. [ ] **Pipeline first (Context without Store write).** Say this to the operator,
      then wait until they confirm the run finished:

> Before we match secrets into the Context, run **env-gen / Effective Set** on the
> migration branch with pipeline parameter
> **`EXTERNAL_CREDENTIAL_PROVISIONING=skip`**
> (enum: `apply` = default, writes/provisions per product rules; `skip` = build
> Context only, do **not** provision into the Secret Store).
>
> If your pipeline does not expose this parameter yet, stop and say so — we cannot
> safely assume Context exists.
>
> When the job finishes and the External Credential Context artifact is available,
> tell me the path (or that it is ready).

      Preconditions for this step: Instance YAML cutover already done for the creds
      you are filling (external + `create: false` → Context entries are
      `fail_if_absent`). System seed remains I0, not this mode.

5. [ ] Values source (only after step 4 is confirmed):
   - Instance Git still local → `migration-cli collect` (before Instance YAML cutover
     if using this path for values only; Context fill still needs step 4 first).
   - Jenkins → `migration-cli export-credentials`.
6. [ ] `migration-cli fill` into the Context (`fail_if_absent` only).
   - If `--partial` and unmatched report: walk each credId with recommendations
     (credId mismatch Template ↔ export; remove macro / create cred / fix credId).
7. [ ] Show `external-cred-provision` command; wait for user OK; run.
8. [ ] **After Store is seeded**, say this, then show the navigation footer:

> Secret values should now be in the Secret Store via provision.
> On the **next** normal env-gen / Effective Set run, use
> **`EXTERNAL_CREDENTIAL_PROVISIONING=apply`** (or leave the default `apply`)
> so the pipeline follows the usual provision path.
> Do **not** also set `writeToStore: true` on the same creds in Instance apply —
> one Store write path only.

`fill` skips `create_if_absent` entries (EnvGene / provision generates those).

## End of mode — navigation footer (required)

When step 8 is done (or the user stops Transfer here), the agent's **last reply in
this mode must end** with this footer. Fill `<source / tenant or out path>` from
context. Do not start Template/Instance until the user picks an option.

```text
---
You are here: Transfer → <source / tenant or out path> → done

What usually comes next:

1) Template — if Template YAML cutover is still outstanding
2) Instance — if Instance YAML cutover is still outstanding
3) Transfer again — another Jenkins tenant, collect scope, or Context file
4) Stop — nothing more right now

What do you choose? Reply with a number or in your own words.
---
```
