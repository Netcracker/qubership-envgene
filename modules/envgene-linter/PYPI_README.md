# EnvGene Linter

- [Install](#install)
- [Run a check](#run-a-check)
- [Open the report](#open-the-report)
- [Optional commands](#optional-commands)
- [Troubleshooting](#troubleshooting)

EnvGene Linter checks the configuration files in an EnvGene instance repository and saves the findings in an HTML report.

## Install

You need Python 3.12 or newer with pip. Run this command in a terminal to install or update the tool:

```bash
python -m pip install --upgrade qubership-envgene-linter
```

If your system uses `python3` instead of `python`, use `python3 -m pip` in that command.
You do not need to download the source code or build the package.

## Run a check

Open a terminal in the root of your instance repository: the directory containing `environments/`.
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
- If the linter reports a missing `environments/` directory, run it from the instance repository root.

This is an alpha release. Checks cover supported references and generator inputs, not every file in the repository.
Exit code `0` means the check completed, including runs with findings. Exit code `2` indicates a command or execution error.
