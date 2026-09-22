# EnvGene Linter

EnvGene Linter checks local EnvGene instance repositories for configuration
placement, naming, secret handling and reference integrity. It prints findings
in the terminal and can generate a standalone HTML report.

This is an **alpha release**. Rule coverage is incomplete and findings should
be reviewed before changing configuration. INT-1 schema validation is not yet
implemented.

## Installation

Requires Python 3.12 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install envgene-linter==0.0.1
envgene-linter --help
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`.

## Usage

Pass the root of an EnvGene instance repository containing an `environments/`
directory:

```bash
envgene-linter check /path/to/instance-repository
envgene-linter check /path/to/instance-repository --html
```

The `--html` option writes `envgene-linter-report.html` in the checked repository
and adds it to that repository's `.gitignore`. The report is self-contained.

Checks run locally without network calls. The tool does not render Jinja,
decrypt secrets, generate environments or automatically fix configuration.
It checks objects selected by supported local references or known generator
usage; unused files are not automatically included.

## Implemented rules

- Placement: PLACE-1, PLACE-2, PLACE-3, PLACE-4, PLACE-6, PLACE-7, PLACE-8,
  PLACE-9, PLACE-10.
- Naming: NAME-1, NAME-2, NAME-3, NAME-4.
- Secrets: SEC-1, SEC-3, SEC-4, SEC-5.
- Integrity: INT-2.

Findings include a location, rule identifier and message. Security findings
avoid displaying secret values. Review reports before sharing them: paths and
other configuration information may still be sensitive.

## Exit status

Exit code `0` means the check completed, even when findings were reported.
Exit code `2` indicates a command or operational error. This alpha does not
provide a findings-based CI failure threshold.
