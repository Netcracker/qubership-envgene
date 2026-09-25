# NAME-8: name the Cloud Passport passport

- [Scope](#scope)
- [Filename checks](#filename-checks)
- [Findings and verification](#findings-and-verification)

[NAME-8 in the configuration standard](/docs/configuration-standard.md#name-8---name-the-cloud-passport-passport-should)
requires the default Cloud Passport stem `passport` and its companion Credential file stem `passport-creds`.
The rule is enabled by default after NAME-4 and reports Warning / Fix.

## Scope

Check passports selected in `Connections.environment_passports`, including explicit references and automatic
cluster-name association. Unselected files and unresolved ambiguous lookups do not produce NAME-8 findings.
The exact stem `passport-infra` and its companion are excluded because their naming belongs to NAME-9.
Other names ending in `-infra` are not inferred to have the infra role.

The check applies to supported selected YAML passports at any lookup scope.
PLACE-9 checks placement separately. Passport contents do not determine filename validity.
Jinja files are excluded. Logical and physical paths must remain inside the repository and outside `.git`.
Broken or cyclic links are ignored. These guards do not alter failures in discovery before this rule runs.

## Filename checks

A selected passport must have the stem `passport`. Both `.yml` and `.yaml` are accepted.
Inspect its companion using the existing lookup priority:

1. `credentials/<passport-stem>.yml` beneath the passport's directory.
2. `<passport-stem>-creds.yml` beside the passport.

The first existing path or symlink occupies the slot. An invalid or unsafe first slot does not authorize using
another file as the companion. A selected companion must have the stem `passport-creds`.
The legacy `credentials/passport.yml` therefore produces a naming finding as well as any applicable placement finding.

The standard permits `.yaml`, but the generator's companion lookup uses `.yml` only.
NAME-8 preserves that lookup and does not infer use of adjacent `.yaml` Credential files.
No companion means no companion-name finding. Arbitrary nearby Credential files are not inspected.

## Findings and verification

Emit one finding per physical file, aggregating naming requirements and consuming environments.
If passport and companion aliases share one physical file, recommend separate files with the required names.
Report the logical filename at line 1, column 1. Recommend renaming and updating dependent references while keeping
passport and companion names consistent. Do not rename files automatically or disclose Credential IDs or values.
CLI findings retain exit code 0. Disabling NAME-8 bypasses its check and shows Disabled in reports.

The approved bounded design is recorded in the
[specification and design](/modules/envgene-linter/docs/superpowers/specs/2026-09-25-name8-design.md).
The implementation and executable examples are:

- [Rule implementation](/modules/envgene-linter/src/envgene_linter/rules/name8.py)
- [Tests](/modules/envgene-linter/tests/test_name8.py)
- [Examples](/modules/envgene-linter/testdata/rules/name8)

Tests cover canonical extensions, infra exclusion, explicit and automatic selection, unused and ambiguous passports,
companion priority, absent companions, file aliases, unsafe paths, report integration, and disablement.
