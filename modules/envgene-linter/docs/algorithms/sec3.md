# SEC-3

## Description

Credential references must not occur in runtime parameters (`technicalConfigurationParameters`), which are applied through Consul. Keep secrets in deployment parameters, referenced through Credentials.

This implementation recognizes Credential references independently of the parameter's name. It does not add a second name-based plaintext-secret heuristic; direct literals remain within SEC-1's documented detection scope.

## Input parameters

| Input | Purpose |
| --- | --- |
| `index` | Discovered environments and loaded ParameterSets |
| `connections` | Actual selected files and their usage categories; computed if omitted |
| `parameters`, `applications[].parameters` | Selected ParameterSets with at least one `Category.TECHNICAL` use (`envSpecificTechnicalParamsets`) |
| `technicalConfigurationParameters` | Used `cloud.yml` and `Namespaces/<target>/namespace.yml` objects |

Cloud/Namespace selection is shared with SEC-1: a Cloud belongs to a discovered environment; a Namespace must be targeted by a resolved local ParameterSet or resource-profile binding. Presence of an arbitrary Namespace file or a missing binding does not establish usage.

## Processing flow

1. Compute or reuse connections. Select physical ParameterSets having at least one actual technical-category use. A deploy/E2E use alone does not qualify; an unresolved technical reference does not qualify another file.
2. Skip unreadable, Jinja, external and `.git` inputs. Inspect both root and application parameter maps of each eligible ParameterSet once, even if several environments use it.
3. Resolve used Cloud/Namespace paths with the shared selection helper. Deduplicate physical object files and inspect only their `technicalConfigurationParameters` maps. Ignore `deployParameters` and `e2eParameters` on those objects.
4. Walk nested maps and lists, protecting against recursive YAML aliases. Recognize:
   - A string containing a direct `${creds.get(` call, allowing whitespace around the macro opening, dot, method and opening parenthesis. It may occur inside a larger string and use either quote style for the ID.
   - A map with `$type: credRef`. Treat the reference map as one parameter value, not one finding per field.
5. Emit one finding per matching parameter occurrence, even if its string contains several Credential calls. Do not resolve, read or validate the referenced Credential.
6. Sort findings by path, parameter key and line. A source ParameterSet and its generated object can each have a finding at their own location.

## Result

Warning / Fix at the parameter's original YAML position. The key includes its section, nested path and list indices. The message says that the runtime parameter contains a Credential reference. The hint recommends moving the secret to deployment parameters while retaining the reference.

The reference text, Credential ID and secret value are omitted from SEC-3 findings. SEC-3 follows SEC-1; SEC-4, SEC-5 and INT-2 follow it before NAME-1; the console shows eighteen rule headings. HTML includes only sections with findings. CLI exit code remains `0` for findings. No new flags, automatic fixes, decryption or networking.

## Error handling

- Unused files, missing inputs and malformed/non-map Cloud/Namespace documents are skipped. SEC-3 does not emit YAML parser exception text, which can include source data.
- The detector recognizes direct Credential macro calls and explicit `credRef` nodes. It is not a Groovy/Jinja interpreter: indirect references, computed aliases and Credential access nested inside arbitrary other expressions are outside this implementation.
- Recognizing a call or `$type: credRef` does not validate its syntax or prove that the referenced Credential exists. Their placement in runtime parameters is the condition being reported.
- Plain text `creds.get(...)` outside a macro is not a reference. Other macros, ordinary literal values, empty values and unrelated structured values are not SEC-3 findings.
- Other existing rules and discovery diagnostics retain their own output behavior; omission of values in SEC-3 is not global report redaction.

## Example

```yaml
# Reported regardless of the name SOME_VALUE.
technicalConfigurationParameters:
  SOME_VALUE: ${creds.get("example-cred").password}
  nested:
    - value:
        $type: credRef
        credId: example-external-cred
        property: password

# No SEC-3 finding here.
deployParameters:
  SOME_VALUE: ${creds.get("example-cred").password}
```

A ParameterSet containing the same reference under `parameters.SOME_VALUE` also produces SEC-3 if selected through `envSpecificTechnicalParamsets`. If selected only through deploy or E2E bindings, it does not. A file used in both technical and deploy categories still receives SEC-3, independently of PLACE-7.

## Related documentation

- [Specification](../superpowers/specs/2026-09-16-sec3-design.md)

- [Connected entities](connections.md)
- [SEC-1](sec1.md)
- [Usage](../../README.md)
- [Implementation](../../src/envgene_linter/rules/sec3.py)
- [Shared object selection](../../src/envgene_linter/parameter_objects.py)
- [Tests](../../tests/test_sec3.py)
