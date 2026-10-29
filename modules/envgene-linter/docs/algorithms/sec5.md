# SEC-5

## Description

SEC-5 checks secret protection in connected inputs. A literal `data.username` in a `type: usernamePassword`
Credential produces **Warning / Fix**. Other literal secret candidates, unsupported encryption, and sources that
static inspection cannot establish produce **Information / Review**. Recognizable SOPS values with usable document
metadata, supported external Credentials, and EnvGene's documented automatic CI token fallback are accepted.

The check is local and deliberately limited. It does not decrypt values, verify cryptography, read process environment variables, query CI/CD or secret stores, or claim that every repository secret is covered. Every SEC-5 finding uses a generic key and message that omit values, Credential IDs, variable names, reference expressions, remote-store paths, and parser excerpts.

## Input parameters

| Input            | Purpose                                                                                                              |
|------------------|----------------------------------------------------------------------------------------------------------------------|
| `index`          | Repository root, discovered environments, loaded records and safe-path boundary                                      |
| `connections`    | Existing connected entities and per-environment bindings; computed when omitted                                      |
| Security sources | Whole Credential files selected specifically for SEC-5, with source kind and environment retained                    |
| Security bags    | Connected parameter or configuration mappings, their exact prefix, environment, allowed fields and reference catalog |
| Security issues  | Known consumers whose selected source cannot be resolved or inspected safely                                         |

Whole-file inputs include selected shared Credentials, Inventory generation credentials, and the first selected Cloud
Passport credentials companion. Entry-level consumers include selected deployer, system integration, registry, and
Artifact Definition fields, plus authored ParameterSet maps. Source selection follows the [authored configuration
scope](/modules/envgene-linter/docs/algorithms/source-scope.md).

Modern Artifact Definitions resolve registry references in the root `configuration/credentials/credentials.yml` catalog.
V2 selects only the authentication configuration named by `registry.mavenConfig.authConfig`, unless its method is
literal `anonymous`. See [INT-4 reference evidence](/modules/envgene-linter/docs/algorithms/int4.md#reference-evidence).
An unavailable catalog or Credential entry still produces no SEC-5 reference finding because no secret content
can be inspected. INT-2 checks target existence separately.

Generated `Credentials/credentials.yml` supplies reference context without receiving secret-protection findings.
Generated Cloud and Namespace maps are outside consumer selection.
Reference-shape checks can use generated targets. Protection findings use authored target locations.

## Processing flow

Resolve supported calls only in their documented context. System fields use `envgen.creds.get(...).field`, and runtime
ParameterSets use `${creds.get(...).field}`. A bare ID selects an entry only in a documented reference field.
Incompatible available shapes produce Review at the authored consumer. Inspect secret protection only at authored
target locations, deduplicate findings, and stop reference cycles. Generated targets remain context. Validate external
Credential shapes locally without accessing a secret store. Unavailable catalogs or entries provide no secret content
to classify and produce no SEC-5 reference finding.

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
