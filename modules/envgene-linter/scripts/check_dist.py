"""Verify the exact release file allowlist without extracting archives."""

from pathlib import Path
from email.parser import Parser
import tarfile
import tomllib
import zipfile


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    stem = f"{project['name'].replace('-', '_')}-{project['version']}"
    description = "\n".join(
        (root / name).read_text(encoding="utf-8")
        for name in ("PYPI_README.md", "CHANGELOG.md")
    )
    sources = {
        p.relative_to(root / "src").as_posix()
        for p in (root / "src/envgene_linter").rglob("*.py")
    }
    metadata = {"METADATA", "WHEEL", "entry_points.txt", "RECORD"}
    with zipfile.ZipFile(root / "dist" / f"{stem}-py3-none-any.whl") as archive:
        names = set(archive.namelist())
        allowed = sources | {f"{stem}.dist-info/{name}" for name in metadata}
        if names != allowed:
            raise SystemExit(f"Unexpected/missing wheel files: {sorted(names ^ allowed)}")
        body = archive.read(f"{stem}.dist-info/METADATA").decode()
        if f"Name: {project['name']}\n" not in body:
            raise SystemExit("Wheel name does not match pyproject.toml")
        if f"Version: {project['version']}\n" not in body:
            raise SystemExit("Wheel version does not match pyproject.toml")
        if Parser().parsestr(body).get_payload().strip() != description.strip():
            raise SystemExit("Wheel description must include the readme and full changelog")
    sdist_files = {"PYPI_README.md", "CHANGELOG.md", "pyproject.toml", "PKG-INFO"} | {
        f"src/{name}" for name in sources
    }
    with tarfile.open(root / "dist" / f"{stem}.tar.gz") as archive:
        names = set()
        for entry in archive:
            if entry.isdir():
                continue
            if not entry.isfile() or not entry.name.startswith(stem + "/"):
                raise SystemExit("Unexpected archive entry type or root")
            names.add(entry.name[len(stem) + 1:])
        if names != sdist_files:
            raise SystemExit(
                f"Source archive violates the release allowlist: {sorted(names ^ sdist_files)}"
            )
        with archive.extractfile(f"{stem}/PKG-INFO") as metadata_file:
            body = metadata_file.read().decode("utf-8")
        if Parser().parsestr(body).get_payload().strip() != description.strip():
            raise SystemExit("Source archive description must include the readme and full changelog")
    print(f"Verified {stem}: both archives contain only allowed release files.")


if __name__ == "__main__":
    main()
