# EnvGene Linter

EnvGene Linter checks local **EnvGene instance and template repositories**.
Instance checks cover placement, naming, secret handling, reference integrity, and structured values.
Template-only repositories are checked by TPL-1 only. The linter saves an HTML report and prints its absolute path.
Use `--console` to also print findings in the terminal.

See the [changelog](/modules/envgene-linter/CHANGELOG.md) for release changes and migration instructions.

Most instance rules check files selected by supported local references or known generator usage.
INT-4 also examines recognized unconnected authored entities for review.
TPL-1 checks YAML and template placement under `templates/`, `environments/`, and `configuration/`, regardless of bindings.
The linter does not generate environments, render Jinja templates, or automatically fix configuration files.
Checks run locally without network calls.

## Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Quick start](#quick-start)
- [Choosing the repository to check](#choosing-the-repository-to-check)
- [Command reference](#command-reference)
- [Reading findings](#reading-findings)
- [HTML reports](#html-reports)
- [Implemented rules](#implemented-rules)
- [Build-time rule switches](#build-time-rule-switches)
- [What is checked](#what-is-checked)
- [Exit codes and CI](#exit-codes-and-ci)
- [Troubleshooting](#troubleshooting)
- [Development and further documentation](#development-and-further-documentation)

## Requirements

- Python **3.12 or newer**, with `pip`.
- A local EnvGene repository containing `environments/`, `templates/`, or both.

## Installation

The Python command can be named `python` or `python3`, depending on your installation.
Check which command is available with `python --version` or `python3 --version`.
Use one of the following commands with Python 3.12 or newer to install or update the tool from PyPI:

```bash
python -m pip install --upgrade qubership-envgene-linter
```

Or, if your Python command is `python3`:

```bash
python3 -m pip install --upgrade qubership-envgene-linter
```

On Windows, you can also use `py -m pip` if the Python launcher is installed.
The package name is `qubership-envgene-linter`, and the installed command is `envgene-linter`.
You do not need a source checkout or a local build.

A virtual environment is optional for the linter. If pip reports `externally-managed-environment`,
install in a virtual environment as required by your Python installation.

## Quick start

Open a terminal in your repository root, the directory containing `environments/` or `templates/`, and run:

```bash
envgene-linter check
```

The command creates an HTML report and prints its absolute path:

```text
Report saved to: /path/to/instance-repository/envgene-linter-report.html
```

Open that file in a browser. To also print findings in the terminal:

```bash
envgene-linter check --console
```

To check another repository, pass its path:

```bash
envgene-linter check /path/to/instance-repository
```

Every successful check writes the report and adds it to the checked repository's `.gitignore`.
See [HTML reports](#html-reports) for details.

## Choosing the repository to check

The optional argument identifies the **repository root**, which contains `environments/`, `templates/`, or both.
A template-only repository does not need `environments/`. TPL-1 runs there.
Other checks are not yet supported in this mode and appear as `Not applicable` in reports.
Without an argument, the linter checks the current directory. It does not search parent directories.
Paths may be absolute or relative to your current working directory. Quote paths containing spaces.

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

In instance repositories, environments are discovered through `<cluster>/<environment>/Inventory/env_definition.yml`.
Directory names identify clusters and environments. Individual entity directories are optional when not used.

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
envgene-linter check [OPTIONS] [REPO]
```

| Argument or option   | Meaning                                                         |
|----------------------|-----------------------------------------------------------------|
| `REPO`               | Repository root. Defaults to the current directory.             |
| `--console`          | Also print findings in the terminal. HTML is still generated.   |
| `--help`             | Show command help and exit.                                     |

```bash
envgene-linter --help
envgene-linter check --help
```

All applicable enabled rules run on each check. There are currently no CLI options for selecting rules, automatic fixes, strict mode, JSON output, baselines or a custom HTML output path.

## Reading findings

With `--console`, the terminal report groups findings by enabled rule.
An applicable enabled rule without findings shows `No findings`. Reports omit disabled rules.
For template-only repositories, `Not applicable` marks checks not yet supported in this mode.
It does not establish that the corresponding standard rules are irrelevant to template objects.

Each finding contains one or more `path:line:column` locations, followed by its severity, a description and a suggested action. Line and column numbers start at 1. File-level checks use `1:1`, which does not mean that the first YAML key is invalid.

| Action in HTML | Meaning |
| --- | --- |
| **Fix** | The rule identified a condition to correct. Read the suggestion and update the configuration manually. |
| **Review** | Inspect the case before deciding whether a change is appropriate. For example, an empty connected file may be intentional. |

`Fix` describes the recommended action; the tool does not perform it. Several locations in one finding identify the files involved in the same condition. Several rules may report independent issues on the same file.

Discovery and parsing skip notes always go to **stderr**, even without `--console`.
With `--console`, findings go to **stdout**. A skipped input may not have been checked fully.
`No findings` means that the rule found no reportable condition in its eligible inputs.
It does not mean that every file in the repository was validated.

## HTML reports

Every successful check writes a self-contained HTML report, including runs with no findings.
The header and browser tab title show the repository's root folder name, without its full local path.
The page works offline and uses collapsible sections for rules with findings.
Each finding lists its files, issue, action, and fix suggestion.
The HTML report does not display the finding type.
A report with no findings displays `No findings`.

On each check:

1. The linter creates or overwrites `<REPO>/envgene-linter-report.html`.
2. After writing the report, it adds `envgene-linter-report.html` to `<REPO>/.gitignore` if needed.
   Existing ignore entries are preserved.
3. It prints `Report saved to: <absolute-path>` to stderr.

The `--console` flag adds a terminal report. Configuration files are not changed.
The `--html` flag was removed in `0.0.2`. Remove it from existing commands.

Reports from some rules can contain configuration values in finding messages. SEC-5 redacts secret values, Credential IDs, variable names, source expressions and remote-store paths from its findings, and INT-2 uses generic reference-kind keys and messages without IDs, expressions or secret values. These guarantees are specific to those rules. The tool does not upload reports; inspect their contents before sharing them or publishing them as CI artifacts.

## Implemented rules

The table lists the 20 rules enabled by default. Each link opens the processing algorithm and its coverage limits.

| Rule                                                           | Checks                                                                                                              | Severity / action                       |
|----------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------|-----------------------------------------|
| [PLACE-1](/modules/envgene-linter/docs/algorithms/place1.md)   | Matching values across contributing environments or clusters that can move to a more general layer                  | Warning / Fix                           |
| [PLACE-2](/modules/envgene-linter/docs/algorithms/place2.md)   | An environment or cluster repeats an inherited value                                                                | Warning / Fix                           |
| [PLACE-3](/modules/envgene-linter/docs/algorithms/place3.md)   | A selected Cloud Passport is outside the cluster layer                                                              | Warning / Fix                           |
| [PLACE-4](/modules/envgene-linter/docs/algorithms/place4.md)   | Cloud Passport contract keys occur in selected ParameterSets                                                        | Warning / Fix                           |
| [PLACE-6](/modules/envgene-linter/docs/algorithms/place6.md)   | Connected pipeline and end-to-end ParameterSets bind to a target other than Cloud                                   | Warning / Fix                           |
| [PLACE-7](/modules/envgene-linter/docs/algorithms/place7.md)   | A connected ParameterSet reference is shared across deploy, end-to-end, or technical categories in an environment   | Warning / Fix                           |
| [PLACE-8](/modules/envgene-linter/docs/algorithms/place8.md)   | Connected or used ParameterSets, resource profiles or credentials are empty                                         | Information / Review                    |
| [PLACE-9](/modules/envgene-linter/docs/algorithms/place9.md)   | Used passport ambiguity, multiple passports per cluster role, and passport/companion placement                      | Warning / Fix                           |
| [PLACE-10](/modules/envgene-linter/docs/algorithms/place10.md) | Connected entities are outside their type's required directory                                                      | Warning / Fix                           |
| [SEC-1](/modules/envgene-linter/docs/algorithms/sec1.md)       | Literal values in secret-named parameters of connected ParameterSets and supported Cloud/Namespace objects          | Warning / Fix                           |
| [SEC-3](/modules/envgene-linter/docs/algorithms/sec3.md)       | Credential references in runtime parameters and ParameterSets selected through technical bindings                   | Warning / Fix                           |
| [SEC-4](/modules/envgene-linter/docs/algorithms/sec4.md)       | Named user/password pairs reference the same Credential ID                                                          | Information / Review                    |
| [SEC-5](/modules/envgene-linter/docs/algorithms/sec5.md)       | Protection of connected secret candidates, supported references and selected Credential sources                     | Information / Review                    |
| [INT-2](/modules/envgene-linter/docs/algorithms/int2.md)       | Every supported connected reference resolves to an object in its applicable context                                 | Warning / Fix or Information / Review   |
| [INT-3](/modules/envgene-linter/docs/algorithms/int3.md)       | A used reference name is defined at multiple environment, cluster, or repository scopes                             | Warning / Fix                           |
| [INT-4](/modules/envgene-linter/docs/algorithms/int4.md)       | No reference to a recognized authored entity was found in available local sources                                   | Information / Review                    |
| [NAME-2](/modules/envgene-linter/docs/algorithms/name2.md)     | A selected entity's filename stem differs from its `name` field                                                     | Warning / Fix                           |
| [NAME-8](/modules/envgene-linter/docs/algorithms/name8.md)     | A used default Cloud Passport or its selected companion has a noncanonical filename                                 | Warning / Fix                           |
| [VAL-4](/modules/envgene-linter/docs/algorithms/val4.md)       | Connected ParameterSet values contain JSON collections or YAML block collections encoded as strings                 | Warning / Review                        |
| [TPL-1](/modules/envgene-linter/docs/algorithms/tpl1.md)       | Jinja outside template files or supported descriptor fields, misplaced `.j2` files, or ambiguous template syntax    | Warning / Fix or Information / Review   |

Three additional rules are implemented but disabled by default:
[NAME-1](/modules/envgene-linter/docs/algorithms/name1.md),
[NAME-3](/modules/envgene-linter/docs/algorithms/name3.md), and
[NAME-4](/modules/envgene-linter/docs/algorithms/name4.md).
See the [coverage matrix](/modules/envgene-linter/docs/rule-applicability-matrix.md) for the remaining standard rules.

### PLACE-10 directory mapping

PLACE-10 checks connected ParameterSets, Resource Profile Overrides, Shared Template Variables, shared credentials,
and Cloud Passports against their required directories. A legacy path can work in the generator and still produce
an advisory placement finding. Check the supported lookup scope before moving a file.
See the [PLACE-10 algorithm](/modules/envgene-linter/docs/algorithms/place10.md) for the directory mapping.

### SEC-1 detection limits

SEC-1 uses secret-name suffixes such as `password`, `token`, and `api_key` in connected parameter bags.
It skips empty values and unevaluated expressions. This heuristic does not identify every secret or inspect Credential
documents. See the [SEC-1 algorithm](/modules/envgene-linter/docs/algorithms/sec1.md) for matching and source selection.

### SEC-3 runtime parameters

SEC-3 reports supported Credential references in runtime parameter bags and ParameterSets selected through technical
bindings. It checks references regardless of the parameter name. Literal secret detection belongs to SEC-1.
See the [SEC-3 algorithm](/modules/envgene-linter/docs/algorithms/sec3.md) for supported reference forms.

### SEC-4 Credential pair references

SEC-4 reviews recognized sibling user/password parameters that reference different Credential IDs.
Matching IDs do not establish that the Credential exists or has the required shape.
See the [SEC-4 algorithm](/modules/envgene-linter/docs/algorithms/sec4.md) for recognized parameter pairs.

### SEC-5 secret-protection review

SEC-5 reviews protection of selected secret candidates and Credential sources. It recognizes supported SOPS structures,
external Credentials, and the automatic CI token fallback. Unknown protection remains Information / Review.
The check does not decrypt values, access secret stores, or establish repository-wide protection.
See the [SEC-5 algorithm](/modules/envgene-linter/docs/algorithms/sec5.md) for source selection and accepted formats.

### INT-2 reference resolution

INT-2 checks supported Credential, ParameterSet, and Resource Profile references in their selected context.
Definitely missing or ambiguous targets produce Warning / Fix. Dynamic references and unavailable template context
produce Information / Review. Credential checks establish object existence, not property or secret validity.
See the [INT-2 algorithm](/modules/envgene-linter/docs/algorithms/int2.md) for source precedence and resolution limits.

### INT-4 candidates for review

INT-4 checks authored ParameterSets, Shared Template Variable files, Resource Profile Overrides, and individual
Credential entries. It reports candidates with no observed reference as Information / Review and explains uncertainty.
System consumers and local generated objects can establish references. External templates and rendered references
are not fully analyzed, so a finding does not prove that removal is safe. No automatic deletion is performed.
See the [INT-4 algorithm](/modules/envgene-linter/docs/algorithms/int4.md) for coverage and exclusions.

### INT-3 definitions at multiple scopes

INT-3 reports used ParameterSet, shared Credential file, Shared Template Variable, and Resource Profile Override names
defined at multiple scopes. It includes definitions hidden by a used reference's lookup.
Unreferenced names, repeated Credential IDs in differently named files, and duplicates confined to one scope are excluded.

ParameterSet fragments can merge during generation. INT-3 checks their naming against the standard
without claiming that every lower-scope file is ignored. Findings show the participating paths and suggest distinct names
or a definition at one scope. INT-3 messages omit Credential IDs and document values.
See the [INT-3 algorithm](/modules/envgene-linter/docs/algorithms/int3.md) for lookup boundaries and examples.

## What is checked

Except for INT-4 and TPL-1, checks apply only to entities with supported evidence of use:

- ParameterSets referenced through local deploy, end-to-end, or technical bindings.
- Cloud Passports selected explicitly or by supported automatic lookup.
- Resource profiles, shared credentials and Shared Template Variables selected through supported bindings.
- Known fixed-path inventory-generation credentials and used passport credential companions, for the applicable rules.
- Artifact Definitions selected through supported artifact selectors.
- Security sources used by SEC-5 and applicable INT-2 references: generated environment Credentials; selected passport and deployer companions; bound system integration, root-credentials, active legacy registry and selected artifact-registry Credential references.

Except for INT-4 and TPL-1, unreferenced names do not produce findings.
TPL-1 independently checks all YAML and `.j2` files under `templates/`, `environments/`, and `configuration/`.
It allows generator-rendered descriptor fields and marks ambiguous Helm or application placeholders for Review.
See [TPL-1](/modules/envgene-linter/docs/algorithms/tpl1.md) for the field exceptions and file scope.
Discovery can still encounter unused files and emit skip notes.
INT-3 includes definitions hidden by a used reference's lookup, without adding them to other rules' inputs.
INT-4 catalogs recognized unconnected authored entities separately to review their references.
PLACE-9 also diagnoses an ambiguous **used passport lookup** even when it cannot choose one file.

Current limitations:

- Jinja is not rendered. Dynamic or unavailable external/template references are not inferred as connections.
- INT-2 reports definitely missing or ambiguous supported references; dynamic or unavailable template context receives Review. Other unresolved references do not gain a general missing-file check.
- Most content checks skip unreadable or unsupported documents. TPL-1 also scans malformed YAML as text. Applicable path or naming checks can still report on a selected file without parsing its contents.
- Outside TPL-1, Application and Registry Definitions are not checked merely because their directories exist. SEC-5 and INT-2 follow only their established active legacy registry and selected artifact-registry consumers.
- The linter implements the rules listed above, not complete schema validation or a full EnvGene generation run.

See [Connected entities](docs/algorithms/connections.md) and [Effective Set](docs/algorithms/effective-set.md) for selection, precedence and merge details.

## Build-time rule switches

Edit `RULE_ENABLED` in
[`src/envgene_linter/rule_config.py`](src/envgene_linter/rule_config.py) before
building the package. Every implemented rule has its own Python boolean:

```python
"NAME-2": True,
```

`True` runs the rule; `False` skips its check function. The rules in the table
above are enabled in the current source. Change any flag and rebuild in GitHub
Actions to distribute your chosen configuration. This is a package setting, not a YAML file in the checked
repository or a command-line override. Use `True`/`False`, not quoted strings or
numbers, and keep all rule entries. Invalid entries produce exit code 2.

Console and HTML reports omit disabled rules and their findings.
If every rule is disabled, repository analysis is skipped and both reports say `No rules enabled`.

Regression tests explicitly enable rules to preserve coverage regardless of the
release configuration. Separate tests verify switches, validation and reports.
The build includes `rule_config.py` automatically. Previously installed wheels
retain their original settings until replaced by a rebuilt package. When
publishing another build on PyPI, use a new distribution version.

## Exit codes and CI

| Exit code | Meaning                                                                                                                                    |
|-----------|--------------------------------------------------------------------------------------------------------------------------------------------|
| `0`       | The command completed, including runs with Warning or Information findings                                                                 |
| `2`       | Invalid CLI arguments or rule flags, neither `environments/` nor `templates/` when checks are enabled, or failure to write the HTML report |

Skip notes do not by themselves change the exit code. Failure to update `.gitignore` is reported on stderr after the HTML file is written and does not make the command fail. Unexpected runtime failures are outside these handled cases.

**A successful exit is not a “no findings” gate.** Strict mode is not implemented. Use the reports for review; do not rely on the current exit code to reject configurations with findings.

To capture findings and diagnostics separately:

```bash
envgene-linter check /path/to/instance-repository --console > lint-findings.txt 2> lint-diagnostics.txt
```

The text files are written in the shell's current directory. The HTML report is written in the checked repository.
The report path and diagnostics go to `lint-diagnostics.txt`. Output files are overwritten on subsequent runs.

## Troubleshooting

| Symptom                                                               | What to check                                                                                                                                                  |
|-----------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `envgene-linter: command not found`                                   | Check that your Python scripts directory is on `PATH`. If you used a virtual environment, activate it.                                                         |
| Installation rejects the Python version                               | Create the virtual environment using Python 3.12 or newer.                                                                                                     |
| `not an EnvGene repository: no environments/ or templates/ directory` | Pass the repository root containing one of these directories.                                                                                                  |
| A file produces no finding                                            | Check the rule's documented scope and stderr for skip notes. Most instance rules require evidence of use. TPL-1 scans its supported directories independently. |
| An environment is missing from results                                | Check for `<cluster>/<environment>/Inventory/env_definition.yml` and inspect parsing diagnostics.                                                              |
| An existing HTML report did not change                                | Check the printed absolute path and stderr for errors. Each successful check overwrites the report.                                                            |
| `cannot write HTML report`                                            | Check write permissions for the checked repository and its existing report file. The command exits with code 2.                                                |
| `cannot update .gitignore`                                            | The report was written, but the ignore file could not be updated. Check permissions or encoding and add the report entry manually if appropriate.              |
| A directory named `ok` still reports findings                         | Bundled fixtures are specific to one rule; all enabled rules run during a CLI check.                                                                           |

## Development and further documentation

To install the current checkout or build and run a wheel without publishing it, follow
[Build and run locally](/modules/envgene-linter/docs/local-build.md).
For PyPI publication, see [Releasing EnvGene Linter](/modules/envgene-linter/docs/releasing.md).

For development, clone the EnvGene repository and activate a virtual environment.
From the EnvGene repository root, install the linter with test dependencies:

```bash
cd modules/envgene-linter
python -m pip install -e '.[dev]'
python -m pytest -q
```

Editable installation makes changes under `src/` available without reinstalling. Test fixtures live in `testdata/`; unit and integration tests live in `tests/`.

Runnable synthetic examples for every implemented rule are available in
[testdata/rules](testdata/rules/), with an `ok` and `not-ok` repository
for each rule. The regular pytest suite verifies these examples, including in
GitHub Actions. Expectations apply to the named rule; other rules may also report
findings.

- [Connected entities and rule eligibility](docs/algorithms/connections.md)
- [Rule applicability and coverage matrix](/modules/envgene-linter/docs/rule-applicability-matrix.md)
- [Effective Set and parameter merging](docs/algorithms/effective-set.md)
- [Development specification index](docs/superpowers/specs/README.md) — includes reading order and historical supersession notes

The linked rule algorithms describe current behavior. Dated specifications preserve design decisions and identify later changes; older report counts or selection requirements should be read with their supersession notes.
