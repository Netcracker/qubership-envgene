# Build and run EnvGene Linter locally

- [Requirements](#requirements)
- [Install directly from source](#install-directly-from-source)
- [Build distribution files](#build-distribution-files)
- [Install the wheel](#install-the-wheel)
- [Run a check](#run-a-check)
- [Publish to PyPI](#publish-to-pypi)

You can build and use the current checkout without publishing it to PyPI.
Local installation uses your working files, including uncommitted changes.

## Requirements

- Python 3.12 or newer with pip.
- A checkout of the EnvGene repository.
- An instance repository containing an `environments/` directory to check.

The commands below use Bash. Use `python3` instead of `python` if that is your Python command.
If pip reports `externally-managed-environment`, use a virtual environment.
Keep the same Python environment active when you install and run the linter.

From the EnvGene repository root, enter the module:

```bash
cd modules/envgene-linter
```

## Install directly from source

For local use without keeping distribution files, run from the module directory:

```bash
python -m pip install --upgrade .
```

Pip builds and installs the local source and its dependencies. It does not upload anything to PyPI.
Repeat this command after changing the source, then follow [Run a check](#run-a-check).

For development, use an editable installation so source changes take effect without reinstalling:

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
```

## Build distribution files

To create files you can install later or share, run from the module directory:

```bash
python -m pip install build twine
python -m build
```

The build creates two files in `dist/`:

- `qubership_envgene_linter-<version>-py3-none-any.whl`: the installable wheel.
- `qubership_envgene_linter-<version>.tar.gz`: the source distribution.

The version comes from `project.version` in `pyproject.toml`. You do not need to change it for local use.
The build includes the instructions and changelog in the package description.
Build tools and runtime dependencies may be downloaded from your configured package index.

If the build backend is already installed, `python -m build --no-isolation` builds without creating
a separate build environment. The backend requirement is declared in `[build-system]` in `pyproject.toml`.

Read the version from the checkout and verify its two archives:

```bash
LINTER_VERSION=$(python -c 'import pathlib, tomllib; print(tomllib.loads(pathlib.Path("pyproject.toml").read_text())["project"]["version"])')
python -m twine check --strict "dist/qubership_envgene_linter-${LINTER_VERSION}.tar.gz" "dist/qubership_envgene_linter-${LINTER_VERSION}-py3-none-any.whl"
python scripts/check_dist.py
```

These checks validate package metadata, archive contents, and the embedded PyPI description.
They do not publish the package.

## Install the wheel

From the module directory, using `LINTER_VERSION` from the previous step:

```bash
python -m pip install --force-reinstall "dist/qubership_envgene_linter-${LINTER_VERSION}-py3-none-any.whl"
python -m pip check
```

`--force-reinstall` replaces an installed package even if your local build has the same version number.
For another machine, copy the wheel and install it with `python -m pip install /path/to/package.whl`.
That machine also needs Python 3.12 or newer and access to the runtime dependencies.

## Run a check

From any directory, pass the instance repository path:

```bash
envgene-linter check /path/to/instance-repository
```

Or open a terminal in the instance repository root and run:

```bash
envgene-linter check
```

Open `envgene-linter-report.html` in your browser using the absolute path printed in the terminal.
Add `--console` if you also want findings in the terminal.
Each successful check replaces the HTML report and adds its filename to the instance repository's `.gitignore`.

## Publish to PyPI

Local builds and PyPI releases use the same package configuration.
Publication is a separate action and requires a new release version.
Follow [Releasing EnvGene Linter](/modules/envgene-linter/docs/releasing.md) to publish through GitHub Actions
or upload reviewed distribution files manually.
