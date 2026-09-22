# Releasing EnvGene Linter

The initial alpha release is `0.0.1`. Its PyPI development-status classifier is
Alpha; the version itself is a normal release version, not a PEP 440 prerelease
such as `0.0.1a1`.

## Files to keep together

The project is already a standalone package. Copy these files if preparing a
separate release checkout:

- `src/envgene_linter/` — the complete Python package, including all rules;
- `pyproject.toml` — metadata, runtime dependencies and the CLI entry point;
- `MANIFEST.in` — the source archive allowlist;
- `README.md` and `PYPI_README.md` — repository and package-index documentation;
- `LICENSE`, once the project owner has confirmed the license and it is added;
- `tests/` and `testdata/` — local synthetic tests, not distribution contents;
- `scripts/check_dist.py` — distribution-content verification;
- `docs/releasing.md` and `.gitignore` — release instructions and local ignores.

The `external-cred-provision` example uses the same setuptools build backend and
console-script mechanism. Do not copy its application code or dependencies.
This project retains its existing `src/` layout and its own dependencies.

Do not copy real instance repositories, `.superpowers/`, `.venv/`, `.git/`,
local reports or session transcripts into a public release checkout.

## Before publishing

1. Confirm the project license with its owner. Add the approved license text and
   metadata; include it in `MANIFEST.in`. No license has been inferred from another
   repository.
2. Confirm ownership/availability of the `envgene-linter` project on PyPI.
3. Review and commit the intended source changes on `dev`. In this working copy,
   several implemented rules and their tests were still untracked when release
   preparation began. A build uses the working tree, not only committed files.
   Do not use an indiscriminate `git add .` to prepare a public repository.
4. Check that `pyproject.toml` contains the intended version. PyPI does not allow
   replacing an already uploaded distribution with another file of the same name.

## Build and check locally

Use Python 3.12 or newer:

```bash
python3 -m venv .release-venv
source .release-venv/bin/activate
python -m pip install -e '.[dev,release]'
python -m pytest -q
python -m build
python -m twine check --strict dist/envgene_linter-0.0.1.tar.gz dist/envgene_linter-0.0.1-py3-none-any.whl
python scripts/check_dist.py
```

The default `python -m build` builds a source archive, then builds the wheel from
that archive. This verifies that the source archive includes the required code.
When build dependencies are already installed, `python -m build --no-isolation`
can perform the same builds without downloading build tools.

Test the wheel in another virtual environment, outside the source checkout:

```bash
python3 -m venv /tmp/envgene-linter-smoke
/tmp/envgene-linter-smoke/bin/python -m pip install dist/envgene_linter-0.0.1-py3-none-any.whl
/tmp/envgene-linter-smoke/bin/python -m pip check
/tmp/envgene-linter-smoke/bin/envgene-linter --help
/tmp/envgene-linter-smoke/bin/envgene-linter check --help
```

Use a disposable synthetic instance repository to check terminal and `--html`
output. The HTML option writes a report and updates `.gitignore` in its target.

## Publish manually

Only run this after completing the checks and confirming the release contents:

```bash
python -m twine upload dist/envgene_linter-0.0.1.tar.gz dist/envgene_linter-0.0.1-py3-none-any.whl
```

Authenticate through Twine's supported interactive or trusted-publishing flow.
For API-token authentication, the username is `__token__` and the password is
the PyPI token. Never put a token in source files, command arguments or commits.
Upload the two explicit reviewed files, not a wildcard that could include old
builds. There is no automatic publishing workflow in this alpha preparation.

After publication, verify installation in a fresh environment:

```bash
python -m pip install --no-cache-dir envgene-linter==0.0.1
envgene-linter --help
```

Official reference: https://packaging.python.org/en/latest/tutorials/packaging-projects/

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
