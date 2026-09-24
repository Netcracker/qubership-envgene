# EnvGene Linter

- [Installation](#installation)
- [Usage](#usage)
- [Implemented rules](#implemented-rules)
- [Rule configuration](#rule-configuration)
- [Exit status](#exit-status)
- [Release history](#release-history)

EnvGene Linter checks local EnvGene instance repositories for configuration
placement, naming, secret handling and reference integrity. It saves an HTML report and prints its absolute path.
Use `--console` to also print findings in the terminal.

This is an **alpha release**. Rule coverage is incomplete and findings should
be reviewed before changing configuration. INT-1 schema validation is not yet
implemented.

## Installation

Requires Python 3.12 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade qubership-envgene-linter
envgene-linter --help
```

The PyPI project name is `qubership-envgene-linter`. The installed command is
`envgene-linter`.

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`.

## Usage

From an EnvGene instance repository root containing `environments/`, run:

```bash
envgene-linter check
```

The command creates or overwrites `envgene-linter-report.html` in that repository
and prints its absolute path. Open the report in a browser.
The report is self-contained and is added to the repository's `.gitignore`.

To also print findings in the terminal, or to check another repository:

```bash
envgene-linter check --console
envgene-linter check /path/to/instance-repository
```

Errors and parsing diagnostics remain visible without `--console`.
The `--html` flag was removed in `0.0.2`. Remove it from existing commands.

Checks run locally without network calls. The tool does not render Jinja,
decrypt secrets, generate environments or automatically fix configuration.
It checks objects selected by supported local references or known generator
usage; unused files are not automatically included.

## Implemented rules

- Placement: PLACE-1, PLACE-2, PLACE-3, PLACE-4, PLACE-6, PLACE-7, PLACE-8,
  PLACE-9, PLACE-10.
- Naming: NAME-2.
- Secrets: SEC-1, SEC-3, SEC-4, SEC-5.
- Integrity: INT-2.

Findings include a location, rule identifier and message. Security findings
avoid displaying secret values. Review reports before sharing them: paths and
other configuration information may still be sensitive.

## Rule configuration

Package builders can set each rule to `True` or `False` in
`src/envgene_linter/rule_config.py` before rebuilding. The rules listed above
are enabled in this build. Installed packages use the configuration included in
their build. There is no repository-level configuration file or CLI override.
Disabled rules do not run and are listed as disabled in terminal and HTML
reports. Invalid flags cause exit code `2`.

## Exit status

Exit code `0` means the check completed, even when findings were reported.
Exit code `2` indicates a command or operational error. This alpha does not
provide a findings-based CI failure threshold.

## Release history

See the [changelog](https://github.com/Netcracker/qubership-envgene/blob/feature/envgene-linter-dev/modules/envgene-linter/CHANGELOG.md)
for changes by version and migration instructions.
