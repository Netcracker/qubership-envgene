# PLACE-12 artifact name grouping design

- [Decision](#decision)
- [Grouping contract](#grouping-contract)
- [Evidence and reports](#evidence-and-reports)
- [Verification](#verification)

## Decision

PLACE-12 compares environments by template name and artifact name, ignoring the artifact version.
The user requested the part of `envTemplate.artifact` before the first colon on November 9, 2026.
This matches `getTemplateArtifactName()` in
[EnvGene business helpers](/modules/envgene/envgenehelper/business_helper.py).
Exact full-reference grouping would prevent comparisons the user wants across template artifact versions.

## Grouping contract

- Derive the group key from the exact `envTemplate.name` and `envTemplate.artifact.split(":", 1)[0]`.
- Preserve case and whitespace in both group-key components. Require a nonempty artifact name after a whitespace check.
- Use the whole artifact string when it contains no colon.
- Retain discovery's literal-string, expression, and custom-tag exclusions for the complete original fields.
- Keep complete artifact references in `EnvModel.template_identity`. Other consumers retain their existing inputs.
- Include every bound target/category/application consumer across the merged version group.
- Keep source completeness, typed equality, physical ownership, distinct-entry, passport, and sensitive-value guards.
- Retain at least two environments, Information / Review, and the existing six-field JSON schema.

For example, `example-env-templates:1.0.0`, `example-env-templates:2.0.0`, and
`example-env-templates:release-SNAPSHOT` share an artifact name. Different template names or artifact names remain
separate.
A missing key, different value, or incomplete selected input in another version still blocks the affected candidate.

## Evidence and reports

Issue messages, finding scopes, and local template recommendations identify the artifact name without its version.
Related evidence retains each environment's complete artifact reference beside its parameter provenance.
All source positions remain available. Values remain confined to the recommendation.
The rule does not compare version order or prove that a proposed default works in every artifact version.
Local template source remains advisory, and inherited or unresolved contexts keep their existing Review behavior.

## Verification

Tests exercise different release and SNAPSHOT versions, versionless references, first-colon splitting,
empty artifact names, separate artifacts and templates, complete cross-version membership, and original-reference
retention.
CLI tests verify the HTML and JSON grouping and preserve all locations and the six-field schema.
Run the complete suite, documentation checks, distribution allowlist, and installed CLI verification.
Customer configuration remains local. Leave changes uncommitted for review.
