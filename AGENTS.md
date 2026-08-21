# AI Agent Rules for qubership-envgene Repository

This document contains guidelines and rules for AI coding assistants working with this repository.

## Writing documentation and text

All rules for how text is written in this repository - documentation under `docs/`, the readme files,
and prose for issues, change requests, and pull requests - live in the `writing-docs` skill at
`.claude/skills/writing-docs/`. Read that skill before you write or edit any `.md` file, any doc under
`docs/`, or any issue, CR, or PR prose for this repository. Its `SKILL.md` routes to the reference file
for the task: prose style, Markdown formatting, document structure, content integrity, object examples,
sample files, and use-case design.

This file keeps only the process rules that sit outside the text: code style below, and the commit and
pull-request conventions at the end.

---

## Code Style

### YAML

- Use 2-space indentation
- Quote string values consistently
- Add comments for complex logic
- Use meaningful key names

## Commits and pull requests

### Commit messages

Use Conventional Commits format: `<type>: <description>`. Types in use here: `feat`, `fix`,
`docs`, `chore`, `refactor`, `test`, `ci`, `perf`, `style`. The repository convention is no
scope prefix.

Subject line:

- Imperative mood (`Add X`, not `Added X` or `Adds X`).
- Under 72 characters.
- No trailing period.

Body (when needed):

- Empty line before body.
- Explain WHY the change is needed and trade-offs, not WHAT (the diff already shows what).
- Wrap at 72 characters.
- Reference issues in a footer (`Closes #123`, `Refs #456`).

### Secret scanning

A pre-commit hook runs a secret scanner (CyberFerret) on every commit. Never bypass it. Do not add a
skip token to the commit message (`@cf_skip`, `@cf_ignore`, `@ignore_cf`, `@skip_cf`), do not pass
`git commit --no-verify`, and do not sidestep the hook by committing through the GitHub API or web
editor. If the hook blocks a commit, resolve the finding or make the scan runnable, for example by
setting the scanner's dictionary password. A blocked commit is a signal to investigate, not to skip.

### Commit type for docs-only changes

If a commit touches only documentation files (`*.md`, `AGENTS.md`, `CLAUDE.md`, files under `docs/`), use
`docs:` as the commit type. The post-merge build workflow skips Docker image rebuilds for commit types
other than `feat:`, `fix:`, and `BREAKING CHANGE`. A doc-only change marked `feat:` or `fix:` triggers
unnecessary image builds.

Tests and linters run on every PR regardless of commit type.

### Pull request description for docs-only changes

Documentation PRs omit the "Test plan" section by default. The doc-quality gates (super-linter,
textlint, link-checker, markdownlint) cover correctness. Include a Test plan section only when
explicitly requested or when the change has runtime implications beyond text.

### Commit granularity

**One logical change per commit.** A commit should be a single coherent unit that a reviewer
can read in one pass.

Split into separate commits when:

- A rule, convention, or schema is added (AGENTS.md, lint config) along with content that
  follows it - put the rule change in its own commit so the rule can be reviewed separately
  from its application.
- Mechanical changes (mass rename, formatting sweep) are mixed with semantic changes - put
  the mechanical change in its own commit so the semantic diff is readable.
- A pre-existing issue is fixed in passing - put the fix in its own commit so it can be
  backported or reverted independently.

Keep in the same commit:

- Test with the code or doc it covers.
- Migration script with the schema change that requires it.
- Anchor renames with the heading change that triggered them.

### Pull request scope

**One focused goal per PR.**

- PR description states the problem, the decision, and trade-offs.
- Target size: under 500 lines of changed prose for docs PRs, under 400 lines for code PRs.
  Larger changes belong in a stack of dependent PRs (mention the order in each description).
- Refactor PRs go separately from feature PRs. Rule additions go separately from
  rule-application PRs.
- Do not include unrelated cleanup. File a follow-up issue instead.

### Change requests

A change request (CR) is the implementation-phase issue. It hands a settled design to a
developer for implementation, not for design discussion or investigation. CRs follow a
six-section structure. For the body template, the convention, and good and bad examples, see
[docs/dev/creating-cr.md](/docs/dev/creating-cr.md).
