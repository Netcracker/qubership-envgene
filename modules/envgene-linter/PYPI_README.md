# EnvGene Linter

- [Install](#install)
- [Run a check](#run-a-check)
- [Open the report](#open-the-report)
- [Optional commands](#optional-commands)
- [Troubleshooting](#troubleshooting)

EnvGene Linter checks EnvGene instance and template repositories and saves findings in HTML and JSON reports.
Template-only repositories are checked by TPL-1, TPL-4, and TPL-6. Other implemented checks require instance inputs.

Checks target authored configuration. Generated instance objects and pipeline outputs are excluded.
Generated Credential catalogs can still resolve references from authored inputs.

## Install

You need Python 3.12 or newer with pip.
The Python command can be named `python` or `python3`, depending on your installation.
Check which command is available with `python --version` or `python3 --version`.
Use one of the following commands with Python 3.12 or newer to install or update the tool:

```bash
python -m pip install --upgrade qubership-envgene-linter
```

Or, if your Python command is `python3`:

```bash
python3 -m pip install --upgrade qubership-envgene-linter
```

On Windows, you can also use `py -m pip` if the Python launcher is installed.
You do not need to download the source code or build the package.

## Run a check

Open a terminal in your repository root: the directory containing `environments/`, `templates/`, or both.
Run:

```bash
envgene-linter check
```

## Open the report

When the check finishes, the terminal shows both report locations, for example:

```text
HTML report saved here: /path/to/instance-repository/envgene-linter-report.html
JSON report saved here: /path/to/instance-repository/envgene-linter-report.json
```

Open that HTML file in your browser. Each finding shows the affected file, the issue, and a suggested action.
Use JSON for automated processing or AI tools. It contains an array of findings with `rule_id`, `rule_title`,
`files`, `issue`, `action`, and `fix_suggestion`. An empty result is `[]`.
The linter does not fix configuration files automatically.

Every successful check replaces both reports. Their filenames are added to the repository's `.gitignore`.
Skipped checks appear in HTML under `Incomplete checks` and in the terminal.
Recoverable YAML, JSON, and Jinja read or parser failures retain independent checks and replace both reports.
Structured skipped checks also appear in JSON as `Review` entries with an issue beginning `Check skipped:`.
Review these entries before treating a report as complete.

## Optional commands

To also display findings in the terminal:

```bash
envgene-linter check --console
```

To check a repository without changing directories:

```bash
envgene-linter check /path/to/instance-repository
```

To compare PLACE-12 candidates with local template source files:

```bash
envgene-linter check -i /path/to/instance-repository -t /path/to/template-repository
```

The long options are `--instance-repo` and `--template-repo`.
Use either the positional repository path or `-i`, not both. Without either, check the current directory.
The optional template path also accepts the `templates/` directory.
All commands create HTML and JSON reports in the checked repository.
Template context does not trigger a separate template check or report.
It does not render Jinja, download artifacts, or prove that the local source matches a published artifact.

## Troubleshooting

- If pip reports `externally-managed-environment`, install in a Python virtual environment.
  A virtual environment is optional for the linter, but some systems require one for pip installations.
- If the terminal cannot find `envgene-linter`, check that your Python scripts directory is on `PATH`.
  If you installed in a virtual environment, activate that environment first.
- If neither `environments/` nor `templates/` is found, run the command from the repository root.
- For template-only repositories, HTML and console output mark unsupported checks as `Not applicable`. JSON omits them.
  TPL-1, TPL-4, and TPL-6 still run unless disabled.

This is an alpha release. Most checks cover supported references and generator inputs.
Connected ParameterSet checks support `.yml`, `.yaml`, and `.json` files, including nested files under
repository, cluster, and Inventory `parameters/` directories. Reference checks and merging use the same selection.
An incomplete directory scan or unavailable role-specific template context receives Review in INT-2.
INT-2 also checks explicit Cloud Passport references. A definitely missing target receives Fix.
Optional passport absence is allowed, and incomplete or uncertain lookups receive Review.
PLACE-12 reviews repeated selected values in at least two environments using the same literal template name
and artifact name before the first `:` in `envTemplate.artifact`. Versions do not split groups.
One cluster is sufficient, and distinct authored source entries are required.
Every bound consumer in the scope must agree. Candidates are Review only; moving values requires confirmation
of template consumers. Each recommendation groups compatible values from the same selected ParameterSet sources.
Without `-t`, PLACE-12 shows actual values in ParameterSet YAML and explains how to connect the shared values.
Choose an unused name for `<shared-paramset-name>` and append its reference to the specified override list.
The recipe identifies a logical Cloud or Namespace association without inventing destination paths.
Optional `-t` / `--template-repo` context adds source comparisons, exact destination files, and a scoped descriptor
attachment when resolvable. Unresolved supplied context receives an explanation.
Recommendations with template context identify both absolute repository roots.
Source paths under `environments/` belong to the instance root. Paths under `templates/` belong to the template root.
Resolved recommendations name absolute files to create or edit and include the proposed YAML.
Descriptor changes identify the existing entry's line, column, and exact YAML path with zero-based Namespace indices.
An eligible complete ParameterSet can be proposed for relocation with its original name and existing bindings.
Existing ParameterSets with matching original or proposed names receive merge instructions.
Missing keys are added, equal values are reused, and conflicts retain the instance entries.
New references append last without duplicates. Lists inside parameter values are compared without concatenation.
Recipes identify exact instance entries to remove after publication, environment updates, and generation checks.
Unresolved changes retain Review without cleanup instructions.
TPL-1 checks Jinja in YAML under `templates/`, `environments/`, and `configuration/`.
It ignores YAML comments and allows `.j2` files regardless of their directory.
Exit code `0` means the check completed, including runs with findings. Exit code `2` indicates a command or execution error.

TPL-4 reviews references without recognized presence protection. It does not prove that generation fails.
TPL-6 checks template logic and allows raw blocks for Helm, application placeholders, and other literal text.
Built-in and custom filters are allowed, including filter blocks. Prohibited Jinja statements remain checked.
TPL-6 reviews unsupported or unconfirmed compatibility with the applicable EnvGene renderer, including unavailable
filters, unsupported legacy lookup forms, and compatibility processing that changes literal raw text.
Additional legacy-expression checks cover configuration YAML. Root GSF/CI description templates are excluded.
Both rules inspect `.j2` files under `templates/` and supported descriptor fields without rendering templates.
