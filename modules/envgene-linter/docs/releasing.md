# Releasing EnvGene Linter

The initial alpha release is `0.0.1`. Its PyPI development-status classifier is
Alpha; the version itself is a normal release version, not a PEP 440 prerelease
such as `0.0.1a1`.

For installation and use without publication, follow
[Build and run locally](/modules/envgene-linter/docs/local-build.md).

## Files to keep together

The project is already a standalone package. Copy these files if preparing a
separate release checkout:

- `src/envgene_linter/` - the complete Python package, including all rules
- `pyproject.toml` - metadata, runtime dependencies, and the CLI entry point
- `README.md` and `PYPI_README.md` - repository and package-index documentation
- `CHANGELOG.md` - changes by version and migration instructions
- `tests/` and `testdata/` - local synthetic tests, not distribution contents
- `scripts/check_dist.py` - distribution-content verification
- `docs/releasing.md` and `.gitignore` - release instructions and local ignores

Packaging follows `external-cred-provision`: `poetry-core` is the build backend,
`[project]` holds the metadata, and the console script is shorter than the PyPI
name. Do not copy its application code or dependencies. This project keeps its
`src/` layout and its own dependencies. `tests/`, `testdata/`, `docs/` and
`scripts/` are excluded from the source archive.

Do not copy real instance repositories, `.superpowers/`, `.venv/`, `.git/`,
local reports or session transcripts into a public release checkout.

## PyPI description

Poetry joins `PYPI_README.md` and `CHANGELOG.md`, in that order, into the package description.
Users read the installation instructions and full release history directly on PyPI.
Edit the instructions in `PYPI_README.md` and the history in `CHANGELOG.md`.
Do not copy the history into the instructions manually.

Both Markdown files are included in the source archive so a wheel rebuilt from it has the same description.
`scripts/check_dist.py` checks the complete description in the wheel and source archive metadata.
A new release is required to update the description on PyPI.

## Before publishing

1. The package metadata declares the Apache-2.0 license, the same license as the
   EnvGene repository and `qubership-external-cred-provision`.
2. Confirm ownership/availability of the `qubership-envgene-linter` project on PyPI.
3. Review and commit the intended changes on the branch selected for publication.
   A local build uses the working tree, including uncommitted files.
4. Update the [changelog](/modules/envgene-linter/CHANGELOG.md) with the release changes and migration instructions.
   Finalize the version heading and remove any unreleased marker before building the release.
   PyPI preserves the description uploaded with that version.
5. Choose a new version, such as `0.0.3`. The GitHub Actions workflow sets it in the build
   and synchronizes `pyproject.toml` after publication. For a manual build, set the version before building.
   PyPI does not allow replacing an uploaded distribution with another file of the same name.

## Build and check locally

Run from `modules/envgene-linter` with Python 3.12 or newer.
The commands below use `0.0.3` as the release version. For a manual build, set
`project.version` in `pyproject.toml` to `0.0.3` first:

```bash
python3 -m venv .release-venv
source .release-venv/bin/activate
python -m pip install -e '.[dev,release]'
python -m pytest -q
python -m build
python -m twine check --strict dist/qubership_envgene_linter-0.0.3.tar.gz dist/qubership_envgene_linter-0.0.3-py3-none-any.whl
python scripts/check_dist.py
```

The default `python -m build` builds a source archive, then builds the wheel from
that archive. This verifies that the source archive includes the required code.
When build dependencies are already installed, `python -m build --no-isolation`
can perform the same builds without downloading build tools.

Test the wheel in another virtual environment, outside the source checkout:

```bash
python3 -m venv /tmp/envgene-linter-smoke
/tmp/envgene-linter-smoke/bin/python -m pip install dist/qubership_envgene_linter-0.0.3-py3-none-any.whl
/tmp/envgene-linter-smoke/bin/python -m pip check
/tmp/envgene-linter-smoke/bin/envgene-linter --help
/tmp/envgene-linter-smoke/bin/envgene-linter check --help
```

Use a disposable synthetic instance repository to check default HTML output and `--console` output.
Run `envgene-linter check` from its root, then repeat with an explicit path from another directory.
Both commands write a report and update `.gitignore` in the checked repository.
Confirm that the default output contains the absolute report path and no findings.

## Publish from GitHub Actions

Run **Publish to PyPI: qubership-envgene-linter** from the Actions tab. Enter the
release version as strict SemVer (`X.Y.Z`, for example `0.0.3`).

The workflow publishes when the run is on upstream `feature/envgene-linter-dev`
or `main` in `Netcracker/qubership-envgene`. Forks and other branches build and
test only. The repository secret `PYPI_API_TOKEN` supplies the PyPI token.

The workflow runs the test suite, builds the sdist and wheel, checks the
archive allowlist, smoke-tests `envgene-linter`, uploads both files to PyPI,
and commits the release version back to `pyproject.toml` when it differs.

Workflow file:
[envgene-linter-pypi-publish.yaml](/.github/workflows/envgene-linter-pypi-publish.yaml).

## Publish manually

Only run this after completing the checks and confirming the release contents:

```bash
python -m twine upload dist/qubership_envgene_linter-0.0.3.tar.gz dist/qubership_envgene_linter-0.0.3-py3-none-any.whl
```

Authenticate through Twine's supported interactive or trusted-publishing flow.
For API-token authentication, the username is `__token__` and the password is
the PyPI token. Never put a token in source files, command arguments or commits.
Upload the two explicit reviewed files, not a wildcard that could include old
builds. Prefer the GitHub Actions workflow above for a normal release.

After publication, verify installation in a fresh environment:

```bash
python -m pip install --no-cache-dir qubership-envgene-linter==0.0.3
envgene-linter --help
```

Official reference: [Packaging Python Projects](https://packaging.python.org/en/latest/tutorials/packaging-projects/)

## Local verification on 2026-09-22

- Branch: `dev`, created from the current `feat/place8` checkout, preserving all
  working-tree changes. No commit, push or PyPI upload was performed.
- Interpreter: Python 3.14. Python 3.12 is declared as the minimum but was not
  available locally for a separate compatibility run.
- Full suite: **613 passed**.
- Source archive and wheel built with `python -m build --no-isolation`;
  the wheel was built from the source archive.
- `twine check --strict`: both distributions passed.
- `scripts/check_dist.py`: both distribution file allowlists passed.
- Wheel installed into a fresh virtual environment using local dependency wheels;
  `pip check` reported no broken requirements.
- From outside the checkout: package version and import location, CLI help,
  a synthetic missing-reference INT-2 finding, HTML output, `.gitignore` update
  and invalid-path exit status were verified.
- License confirmation and PyPI project ownership remain outstanding.
