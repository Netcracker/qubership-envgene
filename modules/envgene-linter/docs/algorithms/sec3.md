# SEC-3

## Description

Credential references must not occur in runtime parameters (`technicalConfigurationParameters`), which are applied through Consul. Keep secrets in deployment parameters, referenced through Credentials.

This implementation recognizes Credential references independently of the parameter's name. It does not add a second name-based plaintext-secret heuristic; direct literals remain within SEC-1's documented detection scope.

## Input parameters

| Input                                     | Purpose                                                                                             |
|-------------------------------------------|-----------------------------------------------------------------------------------------------------|
| `index`                                   | Discovered environments and loaded ParameterSets                                                    |
| `connections`                             | Actual selected files and their usage categories; computed if omitted                               |
| `parameters`, `applications[].parameters` | Selected ParameterSets with at least one `Category.TECHNICAL` use (`envSpecificTechnicalParamsets`) |

SEC-3 follows the [authored configuration scope](/modules/envgene-linter/docs/algorithms/source-scope.md). Generated
Cloud and Namespace parameter maps are outside its inputs.

## Processing flow

1. Select authored ParameterSets with at least one technical-category use through `envSpecificTechnicalParamsets`.
   Deploy or end-to-end use alone does not qualify.
2. Skip unreadable, Jinja, external, and `.git` inputs. Inspect each eligible physical file once.
3. Walk root and application parameter maps, protecting against recursive aliases.
   Recognize strings containing a direct `${creds.get(` call and maps with `$type: credRef`.
4. Emit one finding per matching parameter occurrence, even when its string contains several Credential calls.
   Reference contents and target existence are outside this rule.
5. Sort findings by source path, parameter key, and line.

## Result

Warning / Fix at the parameter's original YAML position. The key includes its section, nested path and list indices. The message says that the runtime parameter contains a Credential reference. The hint recommends moving the secret to deployment parameters while retaining the reference.

The reference text, Credential ID and secret value are omitted from SEC-3 findings. SEC-3 follows SEC-1; SEC-4, SEC-5 and INT-2 follow it before NAME-1; the console shows eighteen rule headings. HTML includes only sections with findings. CLI exit code remains `0` for findings. No new flags, automatic fixes, decryption or networking.

## Error handling

- Unused files and generated objects produce no SEC-3 findings.
   Unavailable authored ParameterSets follow the shared source-read diagnostic contract.
- The detector recognizes direct Credential macro calls and explicit `credRef` nodes. It is not a Groovy/Jinja interpreter: indirect references, computed aliases and Credential access nested inside arbitrary other expressions are outside this implementation.
- Recognizing a call or `$type: credRef` does not validate its syntax or prove that the referenced Credential exists. Their placement in runtime parameters is the condition being reported.
- Plain text `creds.get(...)` outside a macro is not a reference. Other macros, ordinary literal values, empty values and unrelated structured values are not SEC-3 findings.
- Other existing rules and discovery diagnostics retain their own output behavior; omission of values in SEC-3 is not global report redaction.

## Example

A ParameterSet selected through `envSpecificTechnicalParamsets` contains:

```yaml
name: application-runtime
parameters:
  SOME_VALUE: ${creds.get("example-cred").password}
  nested:
    - value:
        $type: credRef
        credId: example-external-cred
        property: password
```

Both references produce SEC-3 findings. Selecting the file only through deploy or end-to-end bindings is silent.
A file used in both technical and deploy categories still receives SEC-3, independently of PLACE-7.

## Related documentation

- [Specification](../superpowers/specs/2026-09-16-sec3-design.md)

- [Connected entities](connections.md)
- [SEC-1](sec1.md)
- [Usage](../../README.md)
- [Implementation](../../src/envgene_linter/rules/sec3.py)
- [Shared object selection](../../src/envgene_linter/parameter_objects.py)
- [Tests](../../tests/test_sec3.py)
