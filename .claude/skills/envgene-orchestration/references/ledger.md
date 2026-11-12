# The run ledger

`openspec/changes/<id>/ledger.md` is the evidence of one change. It is committed with the change and moves with it into
`openspec/changes/archive/<date>-<id>/` on archive. It is the package format
(`component-orchestration/references/ledger.md`) with the EnvGene gate rows described below.

## Format

```markdown
# Ledger: <id>

| time (UTC) | stage | command | exit | result |
|---|---|---|---|---|
| 2026-11-12 09:10 | propose | `git rev-parse --short HEAD` | 0 | start at propose; base master @ aea89fcad |
| 2026-11-12 09:11 | propose | - | - | permissions: commit yes, push no, MR yes (<developer>, chat) |
| 2026-11-12 09:12 | propose | - | - | owner: <owner> from CODEOWNERS; order change approved by <owner> (MR !n) |
| 2026-11-12 10:00 | propose | `openspec validate <id> --strict --no-interactive` | 0 | valid @ 3f2a9c1 |
| 2026-11-12 14:30 | propose | - | - | gate: proposal approved by <owner> on MR !n @ 3f2a9c1 |
| 2026-11-12 15:00 | design | - | - | gate: approach B accepted by <developer> (dev-design.md @ 9b0e4d2) |
| 2026-11-12 15:20 | implement | `python -m pytest modules/envgene/envgenehelper -k X` | 1 | red: 2 failures, function missing |
| 2026-11-12 15:41 | implement | `python -m pytest modules/envgene/envgenehelper -k X` | 0 | green: 2 tests @ 9b0e4d2 |
| 2026-11-12 17:10 | verify | `cd modules/envgene/envgenehelper && python -m pytest` | 0 | 412 passed, baseline 405 @ 7c01d2e |
```

| column | what goes in |
|---|---|
| time (UTC) | when the command finished or the decision was read |
| stage | `propose`, `design`, `plan`, `implement`, `debug`, `verify`, `review`, `docs`, `finish`, `archive`; the rows that orchestration collects before the first stage (permissions, owner, start) get the stage that writes them, `propose` |
| command | exactly what ran, in backticks, without secrets; `-` for a decision |
| exit | the exit code you saw; `-` when nothing ran |
| result | counts and the short commit it applies to; for a decision: who, and where (chat, MR, issue) |

## Gate rows

A gate is passed by a row with the gate word `gate:` in the result column. Each EnvGene gate:

| Gate | Written by | Row | Passed when |
|---|---|---|---|
| propose | `envgene-propose` | `gate: proposal approved by <owner> on MR !n @ <sha>` | owner merged or approved the proposal MR; `proposal.md`, `design.md`, `specs/` unchanged since `<sha>` |
| design | `envgene-design` | `gate: approach <x> accepted by <developer> (dev-design.md @ <sha>)` | developer accepted the decision; every contract id of `design.md` covered |
| verify | `envgene-verification` | one `verify` row per command, at HEAD: `<passed>/<total> @ <sha> (baseline <counts>)` | every command exit 0, or no new failure against its `baseline:` row |
| lint | `envgene-verification` | a `verify` row for the lint command at HEAD: `<n> errors @ <sha>` | exit 0 |
| review | `envgene-review` | `gate: review <verdict> by envgene-reviewer @ <sha>, <n> critical, <n> important` | verdict `ready` or `ready with fixes`, no open critical or important |
| docs | `envgene-documentation` | `gate: docs check passes @ <sha>` | no new findings against the base branch |
| finish | `envgene-finish` | `gate: code approved by <owner> on PR #<n> @ <sha>, checks green` | owner approval read from the PR; GitHub Actions checks green for that commit |
| archive | `envgene-finish` | `gate: archived as the last commit, openspec validate --all --strict exit 0 @ <sha>` | archive commit is the last commit; the merge by a person is read from the PR and posted as a PR comment |

## Rules

- **Append only.** Never edit or delete a row. A correction is a new row: `correction: row 14 named the wrong commit; it was 9b0e4d2`.
- **Named source or nothing.** Each value comes from a command you ran, a file or page you read, or a person's words.
  An unknown stays `unknown`.
- **Evidence is per commit.** A row about commit X says nothing about commit Y. A new commit makes the verify, lint,
  review and docs rows stale until re-run. A commit that changes only `ledger.md`, and the archive commit, do not.
- **Check the sha.** Before a row is used, `git merge-base --is-ancestor <sha> HEAD` must succeed.
- **The ledger rides along.** Commit it with the next commit of the stage; do not create commits just for it.
- **After the archive commit** the ledger moves into the archive folder and is not edited again. Evidence after it goes
  into the MR comment.
- **Never** tokens, passwords, cookies, full logs or personal data beyond a name. Point to a log file or a job URL.
- Permissions and owners are rows too: who said yes to what, and where.
