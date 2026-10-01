# Mode: Template Repository

Stay until T4 handoff. Commands: [commands.md](../commands.md).  
Progress UX: [SKILL.md](../SKILL.md) (full checklist once, then `Step k of n` only).  
Stops table: [SKILL.md — When the agent stops](../SKILL.md#when-the-agent-stops).

## Preconditions (before any Template work)

STOP immediately if any item fails — name what is missing:

- [ ] Template repo root is readable
- [ ] `templates/env_templates/` (or equivalent descriptor location) exists

## Hard rules (Template)

- **No Store writes** in Template mode. Never call `external-cred-provision` or
  open Store sockets here.

### CT formation

Credential Template for a descriptor contains **only** creds reachable from that
descriptor's closure (YAML + text scan so Jinja `{% if %}` list items still bind):

descriptor → tenant / cloud / composite / namespaces → bound ParameterSets  
(`deployParameterSets`, `e2eParameterSets`, `technicalConfigurationParameterSets`).

Paths in the descriptor may use `{{ templates_dir }}` (resolved to `templates/`).
If a descriptor resolves to **0** object files, plan VERDICT is STOP.

- Unbound ParameterSets (name never referenced in YAML **or** text, including
  Jinja `{% if %}` branches) → plan `unbound_parameter_sets` as **INFO only**;
  apply never rewrites / deletes / adds them to CT.
- Technical-bound ParameterSet names: **verbose INFO only** (not a decision).
- Passport-like creds → `to_review` for create/path; `includeInCredentialTemplate: true`
  by default (all reachable ids go into the CT unless the operator sets `false`).
- Existing CT ids outside closure → `stale_credential_template_entries`; dropped on apply.
- Macro rewrite: **not** inside `technicalConfigurationParameters`; technical-only
  paramsets not rewritten to credRef.
- Template consumers (cloud / ns / tenant, bound ParamSets): **surgical**
  macro→credRef only when the file parses as YAML; unparseable Jinja → warn, do
  not rewrite. Credential Template file may still be written as a whole (target
  artifact).
- CT `properties`: when consumers use `.username` / `.password` (or
  `credRef.property`), apply writes `properties: [username, password]`. Pure
  single-value (`.secret` / no property) stays without `properties`. Existing
  `properties` on an already-`external` entry are never removed.
- Descriptor: append `external_credential_template` only if missing (no whole-file
  dump). Value uses `{{ templates_dir }}/external-credentials/<stem>.yml.j2`
  (not a bare `templates/...` path — env-build resolves `templates_dir`).
- Runtime macros (`runtime_credential_macros`): GATE **STOP** until cleared.
  Reply **A** → operator deletes macros in Template files, then `done` → re-plan.
  Reply **B** → run `strip-technical-macros` (Template-only CLI), commit ask, re-plan.
  No waive in Template. Instance waive is separate (see mode-instance / SKILL).

## Checklist (show once at mode start)

- [ ] T1 — Plan + GATE
- [ ] T2 — Review plan (`to_review` / Questions)
- [ ] T3 — Apply
- [ ] T4 — Publish

Later turns: end every reply with the **Now / Next** sticky (English) from
[SKILL.md](../SKILL.md); do not reprint this list.

### T1 — Plan

- [ ] `python -m envgene_migrate plan --repo=template --root <template-repo>`
- [ ] Show GATE (VERDICT / BLOCKERS / DECISIONS / Questions); details only with `--verbose`
- [ ] Unbound = INFO only (ignored)
- [ ] If `runtime_credential_macros` STOP: wait **A** or **B** (plan-review Template Tech)
  - **A** → wait **`done`** → re-plan
  - **B** → `strip-technical-macros --repo=template` → commit ask → re-plan
- [ ] If STOP — do not apply

### T2 — Review plan

- [ ] [plan-review.md](plan-review.md): GATE + Template spot-check create/path; wait **`checked`**
- [ ] Confirm `to_review` in batches by `sourceFile` (minimal edit)
- [ ] Commit of `migration-plan.yaml` is **optional**

### T3 — Apply

- [ ] Clean tracked Git tree
- [ ] `python -m envgene_migrate apply --repo=template --root <template-repo>`
- [ ] On CLI failure: quote error + file path; stop
- [ ] Review `git diff` grouped by path prefix (no secret dumps)
- [ ] Ask commit: `Reply: y | n | later` (commit only on `y`)
- [ ] Optional `--verbose` for per-file progress

### T4 — Publish (user)

- [ ] Commit / MR; publish version; do not merge until Instance succeeds

## End of mode — navigation footer (required)

When T4 is done (or the user stops Template here), the agent's **last reply in this
mode must end** with this footer. Fill `<template / descriptor>` from context.
Do not start another mode until the user picks an option.

```text
---
You are here: Template → <template / descriptor> → done

What usually comes next:

1) Instance — move the same credIds into environment repos (usual next step after publish)
2) Template again — another template / descriptor in this or another Template repo
3) Transfer — only if secret values are not in Git and need Store fill outside apply
4) Stop — nothing more right now

What do you choose? Reply with a number or in your own words.
---
```
