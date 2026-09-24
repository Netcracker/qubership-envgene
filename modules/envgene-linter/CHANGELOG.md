# EnvGene Linter changelog

- [0.0.3](#003)
- [0.0.2](#002)
- [0.0.1](#001)

## 0.0.3

- Simplify installation to one pip command and show how to run a check and open the HTML report.
- Include the complete changelog directly in the PyPI description, after the usage instructions.
- Verify that both distribution archives contain the instructions and changelog in their descriptions.

The CLI behavior and linter rules are unchanged from `0.0.2`.

## 0.0.2

- Allow `envgene-linter check` without a repository argument to check the current directory.
  Explicit repository paths remain supported.
- Create or update `envgene-linter-report.html` by default and print its absolute path.
- Add `--console` to also print findings in the terminal. Errors and parsing diagnostics remain visible by default.
- Remove `--html`. HTML reports are generated automatically, including when `--console` is used.
- Update installation instructions to use the `qubership-envgene-linter` package from PyPI.

To migrate from `0.0.1`, remove `--html` from existing commands.
Add `--console` to commands that need findings on stdout, including shell redirection and CI log collection.
Each successful check now writes the report and adds it to the checked repository's `.gitignore` if needed.
The report location must be writable. Findings still return exit code `0`, and operational errors return `2`.

## 0.0.1

- Initial PyPI release of `qubership-envgene-linter`.
- Check local instance repositories for placement, naming, secret handling, and reference integrity.
- Print findings in the terminal, with optional HTML output through `--html`.
- Support rule switches configured when the package is built.
