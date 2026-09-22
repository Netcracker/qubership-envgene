# EnvGene Linter

EnvGene Linter checks local **EnvGene instance repositories** for configuration placement, naming and empty connected entities. It prints findings in the terminal and can generate a standalone HTML report.

The linter checks files selected by supported local references or known generator usage. It does not generate environments, render Jinja templates or automatically fix configuration files. Checks run locally without network calls.

## Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Quick start](#quick-start)
- [Choosing the repository to check](#choosing-the-repository-to-check)
- [Command reference](#command-reference)
- [Reading findings](#reading-findings)
- [HTML reports](#html-reports)
- [Implemented rules](#implemented-rules)
- [What is checked](#what-is-checked)
- [Exit codes and CI](#exit-codes-and-ci)
- [Troubleshooting](#troubleshooting)
- [Development and further documentation](#development-and-further-documentation)

## Requirements

- Python **3.12 or newer**, with `pip` and virtual environment support.
- A local checkout of this project.
- A local EnvGene instance repository containing an `environments/` directory.

The installation commands below use a POSIX shell, such as Bash on Linux or macOS. Python dependencies are declared in [pyproject.toml](pyproject.toml) and installed by `pip`; installation may require access to your configured package index.

## Installation

From the root of your **envgene-linter checkout**:

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
envgene-linter --help
```

Ensure the version printed by the first command is at least 3.12. If your system's `python3` is older, use a suitable executable, such as `python3.12`, to create the virtual environment.

Activate the same virtual environment in each new shell before using `envgene-linter`. Alternatively, invoke its executable directly from the project root:

```bash
.venv/bin/envgene-linter --help
```

On Windows, activate the environment with `.venv\Scripts\Activate.ps1` in PowerShell instead of `source .venv/bin/activate`; its executable is `.venv\Scripts\envgene-linter.exe`.

To update a regular installation after updating this checkout, run `python -m pip install .` again from the project root with the environment activated. For an editable development installation, see [Development](#development-and-further-documentation).

## Quick start

With the virtual environment activated, pass the root of the instance repository you want to inspect:

```bash
envgene-linter check /path/to/instance-repository
```

For a terminal report and an HTML report:

```bash
envgene-linter check /path/to/instance-repository --html
```

Open `/path/to/instance-repository/envgene-linter-report.html` in a browser. HTML generation writes this file and updates the **checked repository's** `.gitignore`; see [HTML reports](#html-reports).

To try the linter on the bundled synthetic examples, run this from the linter project root:

```bash
envgene-linter check testdata/place8/not-ok
```

This fixture includes three connected empty entities that produce PLACE-8 findings. Other rules also run and may report findings. The `ok` and `not-ok` fixture names refer to the particular rule being demonstrated, not to the absence or presence of all linter findings.

## Choosing the repository to check

The argument is the **instance repository root**, not its `environments/` directory, an individual environment or a template repository. Paths may be absolute or relative to your current working directory. Quote paths containing spaces.

A typical layout is:

```text
instance-repository/
└── environments/
    ├── parameters/
    │   └── shared-deploy.yml
    └── cluster-a/
        ├── cloud-passport/
        │   └── passport.yml
        ├── parameters/
        │   └── cluster-deploy.yml
        └── env-a/
            └── Inventory/
                ├── env_definition.yml
                └── parameters/
                    └── service-deploy.yml
```

Environments are discovered through `<cluster>/<environment>/Inventory/env_definition.yml`. Directory names identify clusters and environments. The root must contain `environments/`; individual entity directories are optional when not used.

Merely placing a file in `parameters/` does not make it eligible for rule findings. For example, this fragment in `Inventory/env_definition.yml` connects a ParameterSet by filename stem:

```yaml
envTemplate:
  envSpecificParamsets:
    cloud:
      - service-deploy
```

Here `service-deploy` refers to a supported file such as `service-deploy.yml`. The resolver applies the supported repository, cluster and environment lookup and merge rules; it does not select a file solely because its internal `name` field matches.

## Command reference

```text
envgene-linter check [OPTIONS] REPO
```

| Argument or option | Meaning |
| --- | --- |
| `REPO` | Existing instance repository directory containing `environments/` |
| `--html` | Also write `envgene-linter-report.html` in `REPO` and ensure an ignore entry exists |
| `--help` | Show command help and exit |

```bash
envgene-linter --help
envgene-linter check --help
```

All implemented rules run on each check. There are currently no CLI options for selecting rules, automatic fixes, strict mode, JSON output, baselines or a custom HTML output path.

## Reading findings

The console groups findings by rule. It always prints all 18 rule headings; a rule without findings shows `No findings`.

Each finding contains one or more `path:line:column` locations, followed by its severity, a description and a suggested action. Line and column numbers start at 1. File-level checks use `1:1`, which does not mean that the first YAML key is invalid.

| Type / action in HTML | Meaning |
| --- | --- |
| **Warning / Fix** | The rule identified a condition to correct. Read the suggestion and update the configuration manually. |
| **Information / Review** | Inspect the case before deciding whether a change is appropriate. For example, an empty connected file may be intentional. |

`Fix` describes the recommended action; the tool does not perform it. Several locations in one finding identify the files involved in the same condition. Several rules may report independent issues on the same file.

Discovery and parsing skip notes go to **stderr**, separately from findings on **stdout**. A skipped input may not have been checked fully. `No findings` means that the rule found no reportable condition in its eligible inputs, not that every file in the repository was validated.

## HTML reports

`--html` preserves the console report and then writes a self-contained HTML file. The page works offline, uses collapsible rule sections and includes only rules with findings. Each finding lists its files, issue, type, action and fix suggestion. A report with no findings displays `No findings`.

On each run with `--html`:

1. `<REPO>/envgene-linter-report.html` is created or overwritten.
2. After a successful write, the linter creates or updates `<REPO>/.gitignore` to include `envgene-linter-report.html`, unless an accepted entry is already present. Other entries are preserved.
3. A completion message is printed to stderr.

Without `--html`, the linter writes neither the report nor `.gitignore`; an existing report is left untouched. Configuration files are not changed by either mode.

Reports from some rules can contain configuration values in finding messages. SEC-5 redacts secret values, Credential IDs, variable names, source expressions and remote-store paths from its findings, and INT-2 uses generic reference-kind keys and messages without IDs, expressions or secret values. These guarantees are specific to those rules. The tool does not upload reports; inspect their contents before sharing them or publishing them as CI artifacts.

## Implemented rules

Each link opens the current processing algorithm. The descriptions below summarize current behavior; some historical catalog labels are broader than the implemented check.

| Rule | Checks | Type / action |
| --- | --- | --- |
| [PLACE-1](docs/algorithms/place1.md) | Matching values across contributing environments or clusters that can move to a more general layer | Warning / Fix |
| [PLACE-2](docs/algorithms/place2.md) | An environment or cluster repeats an inherited value | Warning / Fix |
| [PLACE-3](docs/algorithms/place3.md) | A selected Cloud Passport is outside the cluster layer | Warning / Fix |
| [PLACE-4](docs/algorithms/place4.md) | Cloud Passport contract keys occur in selected ParameterSets | Warning / Fix |
| [PLACE-6](docs/algorithms/place6.md) | Connected pipeline/E2E ParameterSets bind to a target other than Cloud | Warning / Fix |
| [PLACE-7](docs/algorithms/place7.md) | A connected ParameterSet reference is shared across deploy, E2E or technical categories in an environment | Warning / Fix |
| [PLACE-8](docs/algorithms/place8.md) | Connected or used ParameterSets, resource profiles or credentials are empty | Information / Review |
| [PLACE-9](docs/algorithms/place9.md) | Used passport ambiguity, multiple passports per cluster role, and passport/companion placement | Warning / Fix |
| [PLACE-10](docs/algorithms/place10.md) | Connected entities are outside their type's required directory | Warning / Fix |
| [SEC-1](docs/algorithms/sec1.md) | Literal values in secret-named parameters of connected ParameterSets and supported Cloud/Namespace objects | Warning / Fix |
| [SEC-3](docs/algorithms/sec3.md) | Credential references in runtime parameters and ParameterSets selected through technical bindings | Warning / Fix |
| [SEC-4](docs/algorithms/sec4.md) | Named user/password pairs reference the same Credential ID | Information / Review |
| [SEC-5](docs/algorithms/sec5.md) | Protection of connected secret candidates, supported references and selected Credential sources | Information / Review |
| [INT-2](docs/algorithms/int2.md) | Every supported connected reference resolves to an object in its applicable context | Warning / Fix or Information / Review |
| [NAME-1](docs/algorithms/name1.md) | Different parameter keys may represent the same concept based on equal values | Information / Review |
| [NAME-2](docs/algorithms/name2.md) | A selected entity's filename stem differs from its `name` field | Warning / Fix |
| [NAME-3](docs/algorithms/name3.md) | Eligible filenames and used cluster, environment or namespace names are not kebab-case | Information / Review |
| [NAME-4](docs/algorithms/name4.md) | A connected ParameterSet name violates the subject/category convention or embeds scope, ticket or release identifiers | Information / Review |

PLACE-5 and other rules not listed above are not implemented.

### PLACE-10 directory mapping

PLACE-10 covers all five entity types below, not only ParameterSets:

| Entity | Required directory |
| --- | --- |
| ParameterSet | `parameters/` |
| Resource Profile Override | `resource_profiles/` |
| Shared Template Variables | `shared-template-variables/` |
| Shared credentials | `credentials/` |
| Cloud Passport | `cloud-passport/` |

The directory is checked within the file's actual repository, cluster or environment scope. Nested directories inside the required directory are allowed.

The local generator's Shared Template Variable lookup supports legacy `configuration/` and `configurations/` locations. A connected `environments/configuration/variables/ci-global-vars.yml` can therefore be loaded by the generator and still trigger PLACE-10: the standard requires `shared-template-variables/`. This finding describes a directory-standard mismatch, not a failed generation. Consult the [lookup algorithm](docs/algorithms/place10.md) before moving a file; support for a destination depends on the lookup scope.

### SEC-1 detection limits

SEC-1 uses explicit secret-name suffixes (such as `password`, `token` and `api_key`), not arbitrary secret detection. It skips empty values and unevaluated expressions. Cloud files belong to discovered environments; Namespace files require resolved ParameterSet or profile bindings. Credential documents themselves are outside this check. SEC-1 messages omit values; other rules may still include configuration values. See the [SEC-1 algorithm](docs/algorithms/sec1.md) for exact matching and limitations.

### SEC-3 runtime parameters

SEC-3 reports direct `${creds.get(...)}` calls and structured `$type: credRef` references in `technicalConfigurationParameters`, including nested values. It also checks ParameterSets selected through `envSpecificTechnicalParamsets`. Parameter names do not affect this check. Deploy/E2E-only inputs are excluded. Move the secret to deployment parameters while retaining its Credential reference; see the [SEC-3 algorithm](docs/algorithms/sec3.md).

### SEC-4 Credential pair references

SEC-4 identifies sibling user/password parameters with a matching prefix and compares the Credential IDs in their references. Supported user endings are `LOGIN`, `USERNAME`, `USER`, `USER_NAME`; password endings are `PASSWORD`, `PASSWD`, `PASS`, `PWD`. Names support case normalization, camelCase, underscores and dots. Different IDs produce Information / Review at both parameters; equal IDs pass without inspecting Credential definitions.

Pairs remain within one mapping. A lone parameter, literal counterpart or unparseable reference does not produce an ID mismatch. `USER` / `TOKEN`, `CLIENT_ID` / `CLIENT_SECRET` and `accessKey` / `accessSecret` are not included. Messages omit Credential IDs and secret values. See [SEC-4](docs/algorithms/sec4.md).

### SEC-5 secret-protection review

SEC-5 inspects connected secret candidates and selected Credential inputs. It accepts structurally recognizable SOPS values with usable document metadata, supported external Credentials, and EnvGene's automatic CI token fallback. Literal values, unsupported encryption, and sources that cannot be established statically produce Information / Review. A bare `${NAME}` expression is not automatically treated as a protected CI/CD reference. Recognized Credential references (including `credentialsId`) are not secret values. An unavailable catalog or Credential entry does not produce a finding at the reference; available target content is still inspected.

SEC-5 has a larger, separate source set than older rules: generated environment Credentials, the selected Cloud Passport companion, the bound deployer entry and companion, system integration/root-credentials references, active legacy registry consumers, selected Artifact Definitions with `registry.credentialsId`, and ordinary connected ParameterSet and Cloud/Namespace parameter maps. This expansion does not change the credential sets or findings of other rules. SEC-5 does not inspect Effective Set outputs, arbitrary CI workflows, inactive registries, unused deployers, unrelated companions or historical copies. It performs no decryption, environment lookup, network access or external-store validation. See [SEC-5](docs/algorithms/sec5.md).

### INT-2 reference resolution

INT-2 checks connected Credential, ParameterSet and Resource Profile references. A definitely missing or ambiguous target produces Warning / Fix; a dynamic reference, unreadable target or unavailable template context produces Information / Review. Credential calls with or without property access, embedded calls, structured `credRef` and known bare Credential-ID fields are supported. The rule checks Credential object existence only; it does not validate types, properties, secret completeness or protection, and it omits IDs and secret values from its findings.

Generated environment Credentials are authoritative when present. Without that catalog, connected shared/passport inputs can establish that an ID exists, but an absent ID remains unknown because generation may provide it. ParameterSet layers merge deterministically rather than becoming ambiguous. Template-supplied ParameterSets and profiles remain unknown when their context is unavailable. Resource Profile overrides follow directory priority; multiple physical matches within the selected directory are ambiguous. INT-2 uses local inputs without fetching templates, rendering Jinja or decrypting values. See [INT-2](docs/algorithms/int2.md).

## What is checked

Checks apply only to entities with supported evidence of use:

- ParameterSets referenced through local deploy, E2E or technical bindings.
- Cloud Passports selected explicitly or by supported automatic lookup.
- Resource profiles, shared credentials and Shared Template Variables selected through supported bindings.
- Known fixed-path inventory-generation credentials and used passport credential companions, for the applicable rules.
- Artifact Definitions selected through supported artifact selectors.
- Security sources used by SEC-5 and applicable INT-2 references: generated environment Credentials; selected passport and deployer companions; bound system integration, root-credentials, active legacy registry and selected artifact-registry Credential references.
- Used environment definitions and relevant directories for NAME-3.

Unused files do not contribute rule findings, values, categories or locations. Discovery can still encounter them and emit skip notes. PLACE-9 also diagnoses an ambiguous **used passport lookup** even when it cannot choose one file.

Current limitations:

- Jinja is not rendered. Dynamic or unavailable external/template references are not inferred as connections.
- INT-2 reports definitely missing or ambiguous supported references; dynamic or unavailable template context receives Review. Other unresolved references do not gain a general missing-file check.
- Content checks skip unreadable or unsupported documents. Applicable path or naming checks can still report on a selected file without parsing its contents.
- Application and Registry Definitions are not checked merely because their directories exist. SEC-5 and INT-2 follow only their established active legacy registry and selected artifact-registry consumers.
- The linter implements the rules listed above, not complete schema validation or a full EnvGene generation run.

See [Connected entities](docs/algorithms/connections.md) and [Effective Set](docs/algorithms/effective-set.md) for selection, precedence and merge details.

## Exit codes and CI

| Exit code | Meaning |
| --- | --- |
| `0` | The command completed, including runs with Warning or Information findings |
| `2` | Invalid CLI arguments, no `environments/` directory, or failure to write the HTML report |

Skip notes do not by themselves change the exit code. Failure to update `.gitignore` is reported on stderr after the HTML file is written and does not make the command fail. Unexpected runtime failures are outside these handled cases.

**A successful exit is not a “no findings” gate.** Strict mode is not implemented. Use the reports for review; do not rely on the current exit code to reject configurations with findings.

To capture findings and diagnostics separately in a shell with the tool installed:

```bash
envgene-linter check /path/to/instance-repository > lint-findings.txt 2> lint-diagnostics.txt
```

To also generate a browsable report:

```bash
envgene-linter check /path/to/instance-repository --html > lint-findings.txt 2> lint-diagnostics.txt
```

The redirected text files are written in the shell's current directory. The HTML file is written in the checked repository. These output files are overwritten on subsequent runs of the same commands.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| `envgene-linter: command not found` | Activate the environment used for installation, or invoke `.venv/bin/envgene-linter` from the linter checkout. |
| Installation rejects the Python version | Create the virtual environment using Python 3.12 or newer. |
| `not an instance repository: no environments/ directory` | Pass the repository root, not `environments/` or an individual environment directory. |
| A file produces no finding | Confirm that it is connected through a supported binding or known usage; inspect stderr for skip notes and check the rule's algorithm. |
| An environment is missing from results | Check for `<cluster>/<environment>/Inventory/env_definition.yml` and inspect parsing diagnostics. |
| An existing HTML report did not change | Run with `--html`; a console-only check leaves the previous report untouched. |
| `cannot write HTML report` | Check write permissions for the checked repository and its existing report file. The command exits with code 2. |
| `cannot update .gitignore` | The report was written, but the ignore file could not be updated. Check permissions or encoding and add the report entry manually if appropriate. |
| A directory named `ok` still reports findings | Bundled fixtures are specific to one rule; all implemented rules run during a CLI check. |

## Development and further documentation

For an editable installation with test dependencies, run from the linter checkout with its virtual environment activated:

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
```

Editable installation makes changes under `src/` available without reinstalling. Test fixtures live in `testdata/`; unit and integration tests live in `tests/`.

Runnable synthetic examples for every implemented rule are available in
[testdata/rules](testdata/rules/), with an `ok` and `not-ok` repository
for each rule. The regular pytest suite verifies these examples, including in
GitHub Actions. Expectations apply to the named rule; other rules may also report
findings. For NAME-3, `ok` still reports the required `env_definition.yml`
filename because it contains an underscore; `not-ok` additionally reports
`Bad_Name.yml`. The tests explicitly account for this existing behavior.

- [Connected entities and rule eligibility](docs/algorithms/connections.md)
- [Effective Set and parameter merging](docs/algorithms/effective-set.md)
- [Development specification index](docs/superpowers/specs/README.md) — includes reading order and historical supersession notes

The linked rule algorithms describe current behavior. Dated specifications preserve design decisions and identify later changes; older report counts or selection requirements should be read with their supersession notes.
