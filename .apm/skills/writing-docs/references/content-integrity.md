# Content integrity

Document-level accuracy rules: keep internal-analysis wording out of user-facing docs, and run the
pre-flight linters and final checks before a doc change is declared done. The universal accuracy and
vocabulary rules - verify identifiers, use existing vocabulary, define every term, do not re-gloss, and
link in-repo with repo-root paths - live in the `writing-style` skill (`references/integrity.md`).

- [No internal-analysis wording in user-facing docs](#no-internal-analysis-wording-in-user-facing-docs)
- [Pre-flight linter checks](#pre-flight-linter-checks)
- [Testing documentation changes](#testing-documentation-changes)

## No internal-analysis wording in user-facing docs

User-facing docs (how-to, feature, use-cases, tutorial) describe observable behavior. Keep internal
analysis and tooling artifacts out of them: a validation corpus, a scan result, an internal SBOM lookup, a
debugging note. These belong in design or technical-design docs. State the behavior the reader observes,
not the evidence or the internal plumbing behind it.

❌ **INCORRECT:**

- A how-to that says a value is safe because the corpus showed no divergence.
- A feature doc that explains behavior in terms of an internal SBOM scan.

✅ **CORRECT:**

- State the observable rule, and leave the corpus or scan evidence in the design or technical-design doc.

**Scope:** Applies to **new and modified content only**.

**Why:** Internal-analysis wording leaks detail that ages out and means nothing to a user, who only sees
observable behavior.

---

## Pre-flight linter checks

Before declaring documentation changes done, run the same linters that CI will run.

**Markdown structure (`markdownlint`):**

```bash
npx --yes markdownlint-cli@latest --config .github/linters/.markdown-lint.yml <changed-files>
```

The project config (`.github/linters/.markdown-lint.yml`) relaxes `MD013` line length to 1000,
and disables `MD012`, `MD033`, `MD051`. Running markdownlint without `--config` uses the
default settings (line length 80) which produces many false positives unrelated to the project
rules and may hide real issues like `MD009` (trailing spaces) or `MD040` (fenced block missing
language).

**Natural-language terminology (`textlint` with `textlint-rule-terminology`):**

CI runs textlint on prose to flag terminology preferences (for example, em dashes should be
hyphens, `repo` should be `repository`, `READMEs` should be `readmes`, `Blank line` should be
`Empty line`). The textlint config lives in the shared `netcracker/.github` repository and is
pulled in at CI time. There is no local config file to reference. To preview locally:

```bash
npx --yes textlint --rule terminology <changed-files>
```

This runs the default terminology rule set. CI may flag a few additional terms layered on top
by the shared config. Treat the CI report as authoritative.

**Why:** The CI super-linter runs both linters. Running locally gives a true preview of the CI
result, catches real issues, and avoids distraction from false positives that arise when
running linters with default (non-project) settings.

---

## Testing documentation changes

Before committing documentation:

1. Check Markdown syntax
2. Verify all links work
3. Ensure tables are aligned
4. Review for clarity and accuracy
