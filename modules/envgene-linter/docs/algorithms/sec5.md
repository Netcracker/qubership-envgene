# SEC-5

## Description

SEC-5 checks secret protection in connected inputs. A literal `data.username` in a `type: usernamePassword`
Credential produces **Warning / Fix**. Other literal secret candidates, unsupported encryption, and sources that
static inspection cannot establish produce **Information / Review**. Recognizable SOPS values with usable document
metadata, supported external Credentials, and EnvGene's documented automatic CI token fallback are accepted.

The check is local and deliberately limited. It does not decrypt values, verify cryptography, read process environment variables, query CI/CD or secret stores, or claim that every repository secret is covered. Every SEC-5 finding uses a generic key and message that omit values, Credential IDs, variable names, reference expressions, remote-store paths, and parser excerpts.

## Input parameters

| Input | Purpose |
| --- | --- |
| `index` | Repository root, discovered environments, loaded records and safe-path boundary |
| `connections` | Existing connected entities and per-environment bindings; computed when omitted |
| Security sources | Whole Credential files selected specifically for SEC-5, with source kind and environment retained |
| Security bags | Connected parameter or configuration mappings, their exact prefix, environment, allowed fields and reference catalog |
| Security issues | Known consumers whose selected source cannot be resolved or inspected safely |

SEC-5 expands source selection without adding those files to the legacy `Connections` credential sets used by other rules.
Whole-file inputs include selected shared Credentials, `Inventory/credentials/inventory_generation_creds.yml`,
generated environment `Credentials/credentials.yml`, and the first selected Cloud Passport credentials companion.
Entry-level consumers include a bound deployer and its selected companion, system integration/root-credentials
references, active legacy registry consumers, selected Artifact Definition registry references, and ordinary connected
ParameterSet and Cloud/Namespace parameter maps.

Modern Artifact Definitions resolve registry references in the root `configuration/credentials/credentials.yml` catalog.
V2 selects only the authentication configuration named by `registry.mavenConfig.authConfig`, unless its method is
literal `anonymous`. See [INT-4 reference evidence](/modules/envgene-linter/docs/algorithms/int4.md#reference-evidence).
An unavailable catalog or Credential entry still produces no SEC-5 reference finding because no secret content
can be inspected. INT-2 checks target existence separately.

## Processing flow

1. Collect SEC-5 security records alongside the existing connection graph. Preserve physical path, source kind, environment, consumer prefix and the exact Credential catalog used to resolve a reference. Do not mutate or widen the legacy connection sets.
2. Apply generator selection order. For passport credentials, try `credentials/<passport-stem>.yml` before `<passport-stem>-creds.yml`. For a deployer required by `inventory.deployer`, search cluster before environment, `app-deployer` before `cloud-deployer`, and `deployer` before `app-deployer`; use `configuration/deployer.yml` only when the selected definition lacks the requested entry. Resolve its references against the selected companion beside the definition's safe logical location. A first-priority unsafe or unreadable candidate blocks fallback.
3. Traverse every local Credential entry's nonempty leaves under `data`. For parameter bags, use SEC-1's secret-name heuristic while recognizing complete Credential references regardless of parameter name. For system consumers, inspect only the documented fields selected by the source resolver. Guard recursive YAML aliases.
4. Treat an exact `ENC[AES256_GCM,...]` token as protected only when the same document has usable SOPS metadata: a nonblank version, an encrypted MAC and at least one supported recipient with both identity and nonblank encrypted key data. Metadata does not exempt plaintext values elsewhere in the document. Fernet is unsupported; malformed SOPS-looking values and composite strings receive Review.
5. Resolve a complete supported call only in its documented context: system/deployer fields use
   `envgen.creds.get(...).field`, while runtime parameter maps use `${creds.get(...).field}`; the field must be
   `username`, `password` or `secret`. A bare literal ID is accepted only in a documented Credential-reference field and
   selects the whole target entry. An expression kind used in the wrong context receives Review even if its target is
   encrypted. Inspect the referenced local value, deduplicate repeated physical findings, and stop reference cycles with
   an unknown-source Review. A structured external reference is accepted only when its target matches the local
   external-Credential schema: `type: external`, optional literal `secretStore` (defaulting to `default_store`), no
   `data`, and no unsupported keys or property shape. Never access the external store. A recognized reference, including
   `credentialsId`, is not itself secret material. If its catalog or Credential entry is unavailable, skip the reference
   without a finding; when available, inspect the target content.
6. Classify nonempty literal secret candidates as unprotected and unknown expressions, incompatible available targets, unsupported structures and unreadable selected inputs as source/protection unknown. Expressions stored inside Credential `data` are unknown rather than recursively evaluated because the generator returns stored data verbatim. A bare `${NAME}` does not prove CI/CD protection. An absent integration `self_token` uses EnvGene's automatic `GITHUB_TOKEN` or `GITLAB_TOKEN` fallback and is silent; an explicit `self_token` is inspected.
7. Ignore null, empty, and exact `envgeneNullValue` data values. Emit Warning / Fix only for a literal `data.username`
   in a `type: usernamePassword` Credential. Unknown expressions and Fernet remain Information / Review.
   Deduplicate by physical value and reason, skip unavailable reference targets, and sort by path, line, column,
   and message. Findings keep CLI exit code `0`.

## Result

SEC-5 reports one of three generic conditions: an unprotected literal candidate, unsupported encryption, or unknown
source or protection. Only the confirmed literal username case receives Fix, with a hint to protect the stored value.
Literal passwords and other secret candidates retain Review. Protected, empty, and exact `envgeneNullValue` values
produce no secret-material finding. The marker is case-sensitive and does not exempt substrings or invalid Credential
types.

The console contains eighteen rule headings, with SEC-5 after SEC-4 and before INT-2, followed by NAME-1. HTML includes SEC-5 only when findings exist. SEC-5 redacts secret-bearing identifiers and expressions from its output; this guarantee does not change the output contract of other rules.

## Error handling

- Inputs must resolve inside the repository and outside `.git`, including symlink targets. Unsafe selected paths become a generic Review and do not trigger lower-priority fallback.
- A selected unreadable, Jinja or structurally unsupported file receives one generic file-level Review. This includes a present, nonempty parameter section with the wrong container shape. Parser exception text is not reported.
- Missing unselected files, inactive registries, unused deployers, unrelated passport companions, arbitrary CI workflow files and historical copies are outside the scan.
- Generated Credentials are the catalog for runtime parameter references when present. If that catalog is unavailable, SEC-5 does not guess merge precedence across shared inputs.
- Effective Set outputs are not covered. Their flat secret maps and artifact-consumption relationships require a separate connection contract.
- `crypt` and `crypt_backend` do not prove that a stored value is protected and do not alter classification.

## Example

This selected Credential value is accepted only when the document also contains usable SOPS metadata:

```yaml
service-token:
  type: secret
  data:
    secret: ENC[AES256_GCM,data:YWJj,iv:YWJj,tag:YWJj,type:str]
sops:
  age:
    - recipient: age1example
      enc: encrypted-recipient-data
  mac: ENC[AES256_GCM,data:YWJj,iv:YWJj,tag:YWJj,type:str]
  version: 3.9.0
```

The token is checked structurally; SEC-5 does not decrypt it or authenticate the ciphertext. Replacing the value with a literal produces Information / Review even if the file still has `sops` metadata. A complete supported reference is resolved in its selected catalog; `${SERVICE_TOKEN}` alone receives unknown-source Review rather than being assumed safe because CI/CD might define it.

## Related documentation

- [Specification](../superpowers/specs/2026-09-18-sec5-design.md)
- [Connected entities](connections.md)
- [Usage](../../README.md)
- [Implementation](../../src/envgene_linter/rules/sec5.py)
- [Value classifier](../../src/envgene_linter/security_values.py)
- [Source selection](../../src/envgene_linter/security_sources.py)
- [Tests](../../tests/test_sec5.py)
