# EnvGene Linter changelog

- [Unreleased](#unreleased)
- [0.0.7](#007)
- [0.0.6](#006)
- [0.0.5](#005)
- [0.0.4](#004)
- [0.0.3](#003)
- [0.0.2](#002)
- [0.0.1](#001)

## Unreleased

- Exclude generated instance objects and pipeline outputs from configuration findings and incomplete-check entries.
   Retain generated Credential catalogs and Cloud Credential references as context for authored inputs.

## 0.0.7

- Check explicit `inventory.cloudPassport` references in INT-2. Report definitely missing local targets as Fix
  and dynamic, unreadable, unsafe, or uncertain lookups as Review. Allow optional passport absence.
- Check only selected Cloud Passport paths in PLACE-3. Ignore unused aliases while retaining findings for
  selected misplaced paths that share a physical file.
- Continue independent checks after recoverable YAML, JSON, and Jinja read or parser failures and write fresh reports.
  Export affected checks as located Review entries in JSON. Keep incomplete merge inputs from confirming
  PLACE-1 promotion or PLACE-2 removal.
- Check connected nested YAML and JSON ParameterSets consistently across reference resolution, content rules,
  and Effective Set merging. Preserve relative-path replacement and generator application order.
  Keep unavailable replacements and incomplete scans from restoring shadowed inputs.
- Include nested YAML and JSON ParameterSets in INT-4's authored candidate and reference analysis.
- Preserve YAML value types in PLACE-1 and PLACE-2 comparisons, including nested collections.
  Treat booleans, integers, floating-point numbers, and numeric strings as distinct values.
- Confirm PLACE-2 removals against every known local selected consumer before reporting Fix.
  Keep necessary overrides silent and report incomplete or unsupported merge contexts as Review.
  Distinguish global, application, nested, and literal dotted source entries.
- Stop reporting `.j2` files based on their directory in TPL-1. Ignore YAML comments while retaining checks
  for Jinja in active values, including quoted strings and block scalars.
- Report literal `data.username` values in `usernamePassword` Credentials as Warning / Fix in SEC-5.
  Ignore exact `envgeneNullValue` placeholders. Unknown expressions and Fernet values remain Review.
- Limit rendered profile reference checks in INT-2 to `profile.name`. Ignore `baseline` and `override_name`.
- Allow same-named ParameterSet fragments across scopes without INT-3 findings.
- Report Shared Template Variable location mismatches as Review in PLACE-10, with generator lookup guidance.
- Suppress NAME-8 passport and companion naming findings when a cluster context contains multiple ordinary passports.
- Clarify SEC-4 Review guidance for intentionally separate user/password Credential IDs.
- Recognize protected EnvGene environment lookups in TPL-4 for YAML templates and guaranteed context fields
  in ordinary environment template descriptor scalars.
- Resolve selected Artifact Definition registry Credentials against the root catalog, including active V2
  authentication configurations. Keep anonymous and inactive configurations out of reference evidence.
- Show skipped checks in HTML and export skipped Jinja checks as located Review entries in JSON,
  so incomplete template checks cannot appear as clean reports.
- Allow all syntactically valid `raw` blocks in TPL-6, regardless of whether they contain Helm syntax.
- Allow all built-in and custom filters in TPL-6, including filter chains and filter blocks.
- Review unsupported or unconfirmed Ansible compatibility after modeling the applicable EnvGene renderer.
  Check legacy lookup forms, filter availability and arguments, and changes to literal raw or string content.
  Include potential legacy expressions in configuration YAML. Exclude root GSF/CI description templates.

## 0.0.6

- Add TPL-4, enabled by default, to review potentially optional Jinja references without recognized presence protection,
  such as `default` or an appropriate `is defined` check. Report candidates as Review without claiming that rendering fails.
- Add TPL-6, enabled by default, to report prohibited Jinja constructs as Fix and uncertain template logic as Review.
  Allow recognizable Helm passthrough in `raw` blocks and review other raw blocks.
  Both new rules check `.j2` files under `templates/` and supported descriptor fields in instance and template repositories.
- Generate `envgene-linter-report.json` alongside HTML on every check, with one object per finding and all related file locations.
  Include `rule_id`, `rule_title`, `files`, `issue`, `action`, and `fix_suggestion`. Write `[]` when there are no findings.
  Add the JSON report filename to `.gitignore` automatically.
- Print separate `HTML report saved here:` and `JSON report saved here:` messages with absolute report paths.

## 0.0.5

- Hide disabled rules in HTML and console reports. If every rule is disabled, show `No rules enabled`.
- Support template repositories containing `templates/` without requiring `environments/`.
  TPL-1 runs on these repositories. Other checks are not yet supported for template-only repositories.
- Add TPL-1, enabled by default, to check YAML and `.j2` placement under `templates/`, `environments/`, and `configuration/`.
  Allow generator-rendered descriptor fields and EnvGene macros. Report misplaced templates and EnvGene Jinja as Fix,
  and ambiguous Helm or application placeholders as Review. No automatic conversion or renaming is performed.
- Add VAL-4, enabled by default, to review JSON collections and YAML block collections encoded as strings
  in connected ParameterSets, including application parameters and nested values.
  Findings recommend native YAML after checking the consumer contract. No automatic conversion is performed.

## 0.0.4

- Add INT-3 to report used reference names defined at multiple environment, cluster, or repository scopes.
  Checks cover ParameterSets, shared Credential files, Resource Profile Overrides, and Shared Template Variables.
- Add INT-4 to flag authored entities for which no references were found in available local sources.
  Findings recommend Review and explain uncertainty, including external templates and rendered references.
  The rule does not establish that removal is safe or delete entities automatically.
- Add NAME-8 to check that selected default Cloud Passports use the filename stem `passport`
  and their selected companion Credential files use `passport-creds`.
  The `passport-infra` file and its companion are excluded.
- Enable INT-3, INT-4, and NAME-8 by default.
- Remove the Type row and its colored chips from HTML findings.
  Cards retain File, Issue, Action, and Fix suggestion. Console severity remains unchanged.
- Show the repository's root folder name below the HTML report heading and in the browser tab title.
  Escape special characters and show the name even when there are no findings.

## 0.0.3

No functional changes from `0.0.2`.

## 0.0.2

- Allow `envgene-linter check` without a repository argument to check the current directory.
  Explicit repository paths remain supported.
- Create or update `envgene-linter-report.html` by default and print its absolute path.
- Add `--console` to also print findings in the terminal. Errors and parsing diagnostics remain visible by default.
- Remove `--html`. HTML reports are generated automatically, including when `--console` is used.

To migrate from `0.0.1`, remove `--html` from existing commands.
Add `--console` to commands that need findings on stdout, including shell redirection and CI log collection.
Each successful check now writes the report and adds it to the checked repository's `.gitignore` if needed.
The report location must be writable. Findings still return exit code `0`, and operational errors return `2`.

## 0.0.1

- Initial PyPI release of `qubership-envgene-linter`.
- Check local instance repositories for placement, naming, secret handling, and reference integrity.
- Print findings in the terminal, with optional HTML output through `--html`.
- Support rule switches configured when the package is built.
