# EnvGene Linter

- [Install](#install)
- [Run a check](#run-a-check)
- [Open the report](#open-the-report)
- [Optional commands](#optional-commands)
- [Troubleshooting](#troubleshooting)

EnvGene Linter checks EnvGene instance and template repositories and saves findings in an HTML report.
TPL-1 checks template repositories. Other implemented rules apply to instance repositories.

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

When the check finishes, the terminal shows the report location, for example:

```text
Report saved to: /path/to/instance-repository/envgene-linter-report.html
```

Open that HTML file in your browser. Each finding shows the affected file, the issue, and a suggested action.
The linter does not fix configuration files automatically.

Every successful check replaces the previous report. The report filename is added to the repository's `.gitignore`.
Errors and messages about skipped files appear in the terminal. Review those messages if a file could not be checked.

## Optional commands

To also display findings in the terminal:

```bash
envgene-linter check --console
```

To check a repository without changing directories:

```bash
envgene-linter check /path/to/instance-repository
```

Both commands also create the HTML report. The old `--html` flag is no longer needed or accepted.

## Troubleshooting

- If pip reports `externally-managed-environment`, install in a Python virtual environment.
  A virtual environment is optional for the linter, but some systems require one for pip installations.
- If the terminal cannot find `envgene-linter`, check that your Python scripts directory is on `PATH`.
  If you installed in a virtual environment, activate that environment first.
- If neither `environments/` nor `templates/` is found, run the command from the repository root.
- Instance rules show Not applicable for template-only repositories. TPL-1 still runs unless disabled.

This is an alpha release. Most checks cover supported references and generator inputs.
TPL-1 checks YAML and template placement under `templates/`, `environments/`, and `configuration/`.
Exit code `0` means the check completed, including runs with findings. Exit code `2` indicates a command or execution error.
