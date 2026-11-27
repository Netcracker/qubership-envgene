# Ledger: app-reg-defs-placement-env

| time (UTC) | stage | command | exit | result |
| --- | --- | --- | --- | --- |
| 2026-11-26 14:44 | docs | `npx markdownlint-cli --config .github/linters/.markdown-lint.yml <5 changed docs>` | 0 | clean; checker proven against a probe file reporting MD009 and MD047 |
| 2026-11-26 14:44 | docs | `npx textlint --rule terminology <5 changed docs>` | 0 | clean |
| 2026-11-26 14:44 | docs | - | - | writing-docs audit: two findings fixed, an invented marker word in `envgene-configs.md` and change-narration wording in `features/app-reg-defs.md` |
| 2026-11-26 14:44 | docs | - | - | lint: super-linter not run, no Docker on this machine; textlint, markdownlint and link-checker run in CI |
| 2026-11-26 14:44 | docs | - | - | note: UC-ARD-PM-3 added to `docs/use-cases/app-reg-defs.md`; writing-docs excludes use cases as a deprecated type, developer approved keeping the scenario in the actively-maintained file |
| 2026-11-26 14:44 | docs | - | - | gate: docs check passes, committed as a19c8c58 `docs: Issues #1971 Extend app_reg_defs_placement with an env mode` (5 files, 127 insertions) |
| 2026-11-26 14:46 | propose | `git rev-parse --short HEAD` | 0 | start at propose; base main @ c02bb812, HEAD a19c8c58 is the docs commit of this change on branch `app_reg_defs_placement` |
| 2026-11-26 14:46 | propose | - | - | source: Jira PDPLDEVOPS-27393 (parent PDPLDEVOPS-27325): add `env` placement mode, change default `dual` to `root` |
| 2026-11-26 14:46 | propose | - | - | decision Q1 (developer, chat): implement placement-aware resolution next to the write side, so `root`, `env`, `dual` all work end-to-end; the locked test asserting the opposite is rewritten |
| 2026-11-26 14:46 | propose | - | - | decision Q2 (developer, chat): declare `app_reg_defs_placement` in `schemas/config.schema.json`, strict enum, `root` default, case-sensitive; audit found no in-repo `config.yml` with an affected value |
| 2026-11-26 14:46 | propose | - | - | decision Q3 F1 (developer, chat): pin `app_reg_defs_placement: dual` in the 59 BDD fixtures carrying per-environment definitions (7 amended, 52 created) |
| 2026-11-26 14:46 | propose | `git ls-files cucumber_tests/test_data/e2e` | 0 | fixture `configuration/config.yml` files are tracked and not gitignored (`git check-ignore` exit 1), so the 52 new fixture files will be committed |
| 2026-11-26 14:46 | propose | - | - | capability `app-reg-defs-placement` is new; `openspec/specs/` holds only `.gitkeep`, so there is no modified capability |
| 2026-11-26 14:46 | propose | - | - | no ADR: rationale lives in proposal.md; the option set is bounded and recorded in component-design.md Approaches |
| 2026-11-26 14:46 | propose | - | - | gate pending: no proposal approval, no MR opened for the change folder; the docs half is already committed at a19c8c58 |
| 2026-11-26 14:52 | design | `git ls-files <work-map targets>` | 0 | every work-map row verified `tracked` at a19c8c58; only `scripts/utils/app_reg_defs_placement.py` is `new-in-repo`; no `not-in-repo` row, design not blocked |
| 2026-11-26 14:52 | design | - | - | fact from code: `appregdef_render.py:78` lower-cases the configured value, so the exact-match requirement holds only through the schema; `.lower()` is removed (constraint) |
| 2026-11-26 14:52 | design | - | - | fact from code: the write side already removes the per-environment pair in every mode (`appregdef_render.py:17-18`) and never cleans the root pair (line 16); that is the C-7 asymmetry the specs state |
| 2026-11-26 14:52 | design | - | - | fact from code: consumers are split today, `process_sd.py:224-225` reads the root pair while `LOCAL_APPDEFS_PATH` and `LOCAL_REGDEFS_PATH` point at the per-environment pair (`resolve_env_names.py:50-51`); this is why Q1 could not be settled on the write side alone |
| 2026-11-26 14:52 | design | - | - | approach A chosen by toma0422 (chat): shared resolver in `scripts/utils/app_reg_defs_placement.py` owning write targets C-2 and lookup order C-3 |
| 2026-11-26 14:52 | design | `npx @fission-ai/openspec validate app-reg-defs-placement-env --strict --no-interactive` | 0 | valid @ uncommitted (on a19c8c58) |
| 2026-11-26 14:52 | design | - | - | gate: approach A accepted by toma0422; component-design.md uncommitted, sha pending the author's commit |
| 2026-11-26 14:52 | design | - | - | open: test work is a sibling ticket, so tasks 1.1, 2.1, 3.1, 4.1, 4.4, 5.1, 6.1 and 6.4 run under that ticket rather than the implementation ticket alone |
