"""Verify the exact release file allowlist without extracting archives."""

from pathlib import Path
import tarfile
import tomllib
import zipfile


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    project = tomllib.loads((root / "pyproject.toml").read_text())["project"]
    stem = f"envgene_linter-{project['version']}"
    sources = {
        p.relative_to(root / "src").as_posix()
        for p in (root / "src/envgene_linter").rglob("*.py")
    }
    metadata = {"METADATA", "WHEEL", "entry_points.txt", "top_level.txt", "RECORD"}
    with zipfile.ZipFile(root / "dist" / f"{stem}-py3-none-any.whl") as archive:
        names = set(archive.namelist())
        allowed = sources | {f"{stem}.dist-info/{name}" for name in metadata}
        if names != allowed:
            raise SystemExit(f"Unexpected/missing wheel files: {sorted(names ^ allowed)}")
        body = archive.read(f"{stem}.dist-info/METADATA").decode()
        if f"Version: {project['version']}\n" not in body:
            raise SystemExit("Wheel version does not match pyproject.toml")
    docs = {"README.md", "PYPI_README.md", "pyproject.toml", "MANIFEST.in", "PKG-INFO", "setup.cfg"}
    egg_info = {"PKG-INFO", "SOURCES.txt", "dependency_links.txt", "entry_points.txt", "requires.txt", "top_level.txt"}
    allowed = docs | {f"src/{name}" for name in sources}
    allowed |= {f"src/envgene_linter.egg-info/{name}" for name in egg_info}
    with tarfile.open(root / "dist" / f"{stem}.tar.gz") as archive:
        names = set()
        for entry in archive:
            if entry.isdir():
                continue
            if not entry.isfile() or not entry.name.startswith(stem + "/"):
                raise SystemExit("Unexpected archive entry type or root")
            names.add(entry.name[len(stem) + 1:])
        if names - allowed or not {f"src/{name}" for name in sources} <= names:
            raise SystemExit("Source archive violates the release allowlist")
    print(f"Verified {stem}: both archives contain only allowed release files.")


if __name__ == "__main__":
    main()
