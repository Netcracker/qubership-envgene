# Ledger: cluster-macros-passport-fallback

| time (UTC) | stage | command | exit | result |
|---|---|---|---|---|
| 2026-11-18 17:01 | propose | `git rev-parse --short HEAD` | 0 | start at propose; base main @ c0771dd70 |
| 2026-11-18 17:01 | propose | - | - | permissions: commit yes, push yes, PR yes (popoveugene, chat) |
| 2026-11-18 17:01 | propose | - | - | owner: @miyamuraga from CODEOWNERS (/openspec/changes/); docs/ owner @popoveugene |
| 2026-11-18 17:01 | propose | - | - | decision: repo runs propose → design → plan order (orchestration convention) |
| 2026-11-18 17:01 | propose | - | - | no ADR: bounded change, rationale in proposal.md |
| 2026-11-18 17:01 | propose | - | - | note: change reopens prior owner decision (param deprecated / not propagated from Cloud Passport); re-litigated at owner approval of PR #1960 |
| 2026-11-18 17:02 | propose | `openspec validate cluster-macros-passport-fallback --strict --no-interactive` | 0 | valid @ c0771dd70 |
| 2026-11-18 17:02 | propose | - | - | review: team's own change (no upstream hand-off); proposal + specs fit envgene env-build; capability `cluster-connection-macros` kebab-case and unique; no findings |
| 2026-11-18 17:02 | propose | - | - | tasks.md written (uncommitted on c0771dd70) |
| 2026-11-18 17:02 | propose | - | - | PR #1960 opened into main, reviewer @miyamuraga |
| 2026-11-18 17:02 | propose | - | - | gate pending: awaiting proposal approval by @miyamuraga on PR #1960 @ c0771dd70 |
| 2026-11-18 17:10 | propose | - | - | decision: developer popoveugene directs proceeding to design/implement ahead of the propose gate (chat); owner approval of #1960 still required before merge |
| 2026-11-18 17:05 | design | - | - | open question resolved: render-context cloud_passport is a fresh full load of the passport file (set_cloud_passport), independent of the cloud.yml deletion path; all 4 CLOUD_* keys present at render |
| 2026-11-18 17:06 | design | - | - | approach A chosen by popoveugene (chat): elif passport-fallback branch, per-field default(''), protocol upper-cased for parity |
| 2026-11-18 17:07 | design | `openspec validate cluster-macros-passport-fallback --strict --no-interactive` | 0 | valid @ 9c6e5edb1 |
| 2026-11-18 17:07 | design | - | - | gate: approach A accepted by popoveugene (design.md @ acfea8a50) |
| 2026-11-18 17:09 | plan | `openspec validate cluster-macros-passport-fallback --strict --no-interactive` | 0 | valid @ acfea8a50 |
| 2026-11-18 17:09 | plan | - | - | plan.md: 3 steps for 6 tasks, contracts 3/3 covered @ acfea8a50 |
| 2026-11-18 17:15 | implement | `PYTHONPATH=".:./scripts" python -m pytest scripts/tests/env-build/ -q` | 1 | baseline: 117 passed, 29 failed @ e48f85e4c (29 pre-existing, unrelated: missing native dep and other env issues) |
| 2026-11-18 17:16 | implement | `PYTHONPATH=".:./scripts" python -m pytest scripts/tests/env-build/test_cluster_macros_passport_fallback.py -q` | 1 | red: 2 passport-fallback tests fail (cluster macros empty today) |
| 2026-11-18 17:17 | implement | - | - | regression test_render_envs[cluster01-env03-test-template-1] is an expected golden update: env03 uses cloudPassport and no clusterUrl, so cloud.yml maas/dbaas/consul hosts now render the passport domain; reference cloud.yml corrected |
| 2026-11-18 17:18 | implement | `PYTHONPATH=".:./scripts" python -m pytest scripts/tests/env-build/ -q` | 1 | green: 5 new tests pass; 29 failed == baseline, no new failure @ uncommitted (on e48f85e4c) |
| 2026-11-18 17:18 | implement | - | - | task 2.2 covered by the env03 full-render integration test; no separate cucumber fixture |
| 2026-11-18 17:22 | implement | `docker run ghcr.io/igorshubovych/markdownlint-cli --config .github/linters/.markdown-lint.yml docs/template-macros.md` | 0 | 4 macro entries reworded to fallback; markdownlint clean |
| 2026-11-18 17:23 | implement | - | - | all tasks ticked (1.1-1.3, 2.1, 2.2, 3.1); doc-vs-code reconciled for the four cluster macros |
| 2026-11-18 17:24 | verify | `PYTHONPATH=".:./scripts" python -m pytest scripts/tests/env-build/ -q` | 1 | 122 passed, 29 failed @ 28d749f8a (baseline 117 passed, 29 failed; +5 new, no new failure) |
| 2026-11-18 17:24 | verify | - | - | env limit: full scripts/tests, per-module pytest, Maven and cucumber suites not runnable here (missing native dep ruamel.yaml.clib blocks artifact_searcher install); cross-suite verify deferred to CI on PR #1960 |
| 2026-11-18 17:26 | review | - | - | gate: review ready with fixes by envgene-reviewer @ 28d749f8a, 0 critical, 1 important, 3 minor |
| 2026-11-18 17:27 | review | - | - | important fixed: proposal.md/tasks.md/plan.md claimed a deprecated note on cloud_public_url was removed; base doc had none; reworded to describe the four-entry reword only |
| 2026-11-18 17:27 | review | - | - | minor fixed: FULL_PASSPORT given distinct hosts (api.passport-host.cloud:7443) so FROM_PASSPORT differs from FROM_CLUSTER_URL and proves passport sourcing |
| 2026-11-18 17:27 | review | - | - | minor answered (not changed): red row count 2 is correct; the red run was `2 failed, 3 passed` (full_passport, missing_port failed; absent_no_passport passed pre-fix) |
| 2026-11-18 17:27 | review | - | - | minor noted: `in in the` typo fix at template-macros.md:498 is within a fully reworded sentence, acceptable |
| 2026-11-18 17:28 | verify | `PYTHONPATH=".:./scripts" python -m pytest scripts/tests/env-build/ -q` | 1 | re-verify after review fixes: 5 new pass, 29 failed == baseline, no new failure @ pending commit |
| 2026-11-18 17:31 | review | - | - | extra docs fix (developer-directed): cloud_public_url Basic usage showed apiPort copy-paste; corrected to publicUrl macro in a yaml block matching siblings; separate commit |
