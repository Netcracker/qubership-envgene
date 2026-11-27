---
name: envgene-finish
description: EnvGene override of the component-finish slot. Runs the last two stages of a change in qubership-envgene - finish (an optional GitHub PR for code in this repository, merged first and built into an image; then the GitLab MR, which always exists and holds OpenSpec, with its evidence, green pipeline and the component owner's approval) and archive (the OpenSpec archive as the last commit of the GitLab MR, then a person merges). Use when a change has passed verify, review and docs, when someone says "finish", "ready to merge" or "archive", or after the person reports the merge.
---

# EnvGene finish and archive (override of component-finish)

Replaces `component-finish` in this repository. A change ends in a GitLab MR, always: it holds OpenSpec (the change
folder, the ledger, the archive) and either GitLab-only changes or a reference to the image built from this GitHub
repository. A GitHub PR exists only when the implementation touches this repository, and it is merged and built
before the GitLab MR goes on. It keeps the package gates: fresh evidence before a request is ready, green checks, the
owner's approval of the code, the archive as the last commit with its ledger, and the merge by a person. The agent
never merges and never approves.

## Entry check

For the current HEAD the verify, lint, review and docs gates are passed (Gate rows of
`envgene-orchestration/references/ledger.md`). Anything missing or stale: stop and go back to that stage. A change
already in `openspec/changes/archive/<date>-<id>/` resumes at **Archive**, step 3.

## Finish (stage 9)

### A. GitHub PR - only when the implementation touches this repository

1. **Sync with the base**: `git fetch origin`, then rebase on or merge `origin/main`, as the developer chooses. If the
   base moved, run `envgene-verification` again before going on.
2. **Push** after the developer's yes. Never force-push a branch others use; ask first if a rebase needs it.
3. **Make the PR ready**: take it out of draft and fill `.github/pull_request_template.md`: what changed and why (from
   `proposal.md`), the link to the GitLab MR, the `verify` rows and the docs gate result. Reviewer: the owner from
   `CODEOWNERS`.
4. **Wait for the checks** (GitHub Actions, super-linter among them). Red or missing: go to `component-debugging`;
   never ask for an approval or a merge on red checks.
5. **The owner approves, a person merges.** Comments go back to `envgene-review` and `envgene-implementation`, then
   verify, docs and this step again. Read the approval and the merge from GitHub.
6. **Wait for the image** built from the merge. Record its reference in the ledger:
   `| <time> | finish | - | - | PR #<n> merged by <person>, image <reference> |`.

The GitLab MR waits for this part to end.

### B. GitLab MR - always

1. **Sync with the base** of the GitLab repository, as in A.1. If part A ran, update the image reference in the MR to
   the one recorded in A.6.
2. **Push** after the developer's yes, as in A.2.
3. **Make the MR ready**: take it out of draft, with what changed and why (from `proposal.md`), the link to the change
   folder, the upstream spec or ticket, the GitHub PR and image when part A ran, the `verify` rows and the docs gate
   result. Reviewer: the component owner.
4. **Wait for the pipeline** of HEAD. Red or missing: go to `component-debugging`.
5. **The owner approves the code** in the MR. Comments go back as in A.5. Read the approval from GitLab, then append
   the finish gate row (format: Gate rows of `envgene-orchestration/references/ledger.md`).

## Archive (stage 10)

All of it happens in the GitLab MR.

1. Only after the code approval and a green pipeline for that commit: `openspec archive <id> --yes`. It merges the
   delta specs into `openspec/specs/` and moves the change folder (with `design.md`, `component-design.md`, `plan.md`
   and `ledger.md`) to `openspec/changes/archive/<date>-<id>/`.
2. `openspec validate --all --strict; echo "exit=$?"` must exit 0. Append both rows to the archived ledger, then the
   archive gate row (format: Gate rows of `envgene-orchestration/references/ledger.md`), and commit
   `docs: archive OpenSpec change <id>` (with the yes for commits) and push.

   The archive commit changes only `openspec/`, so it does not make the verify and docs rows stale.
3. **Ask the person to merge** once the pipeline of the archive commit is green. Post that evidence as an MR comment
   in the ledger row format: a commit for it would start the pipeline again.
4. **After the person says it is merged**: read the MR state from GitLab (merged, merge commit, merged by a person).
   That is the `merged` gate; record it in the MR comment. With the developer's yes, clean up: remove only a worktree
   this flow created, and delete the local branches.

A code change after the archive commit: `git revert <archive-commit>` (a new commit, never a rewrite of the shared
branch) reopens the change; make the change through implement, verify, docs and review, then archive again as the
last commit.

## If the change is abandoned

Only when the person asks: close the GitLab MR (and an open GitHub PR) with a comment that says why, keep the branches
unless they ask to delete them, and leave the change folder unarchived.

## Rules

- Never merge, never approve.
- The general rules of `envgene-orchestration` (section Rules) apply.
