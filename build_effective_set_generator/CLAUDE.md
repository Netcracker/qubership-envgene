# build_effective_set_generator — Effective Set Generator (Java/Maven)

Pure Java/Maven multi-module project (Quarkus). Builds the Calculator CLI that resolves parameter macros (jinjava/groovy) and merges layered parameters into the final Effective Set. **No Python in this directory** in this branch — the Python orchestration layer that calls this CLI lives under `scripts/effective_set/` and `scripts/utils/` at the repository root (see `scripts/CLAUDE.md`).

## Maven Modules

| Module | Purpose |
|--------|---------|
| `commons` | Shared POJOs/DTOs (`pojo/credentials`, `pojo/extcreds`, `pojo/bom`, `pojo/namespaces`), exceptions, `utils/` (crypt, parameter, credential helpers) |
| `parameters-processor` | Parameter resolution engine: `ParametersCalculationServiceV1`/`V2`, expression binding (`CloudMap`, `NamespaceMap`, `DynamicMap`), `ParameterBundle` |
| `gstring-to-jinjava-translator` | Translates Groovy GString macros to Jinjava templates |
| `parameter-calculator-bom` | Maven BOM (dependency version alignment) |
| `effective-set-generator` | The CLI itself (Quarkus/Picocli): `CmdbCli` entry point, `CliParameterParser` (main orchestration), repository/converter implementations |

## Entry Point

`org.qubership.cloud.devops.cli.CmdbCli` (Picocli `@TopCommand`) → `CliParameterParser.generateEffectiveSet()` → `processAndSaveParameters()`, which per-app fans out to `generateOutput()`/`getParameterBundleByESVer()` (V1 or V2 depending on `--effective-set-version`), then `generateE2EOutput()`, `createExtContextFile()` (external creds), and `generateCleanedNamespacesOutput()` (removed-namespace cleanup) for `EffectiveSetVersion.V2_0`.

Output layout: `effective-set/{topology,pipeline,deployment,runtime,cleanup}/`, plus `mapping.yaml` per section (deployment/runtime mapping is written for every processed namespace; cleanup mapping/content is written **only** for namespaces marked `isCleaned()` — see `generateCleanedNamespacesOutput`, not for every deploy).

## Build & Test

```bash
cd build_effective_set_generator
./mvnw package          # full build + tests, all modules
./mvnw -pl effective-set-generator -am test -Dtest=CmdbCliTest   # single test class
```

Requires JDK 17 + Maven. Main tests: `CmdbCliTest` (end-to-end via `FileTestUtils.compareFolders` against fixtures in `effective-set-generator/src/test/resources/environments/`).
