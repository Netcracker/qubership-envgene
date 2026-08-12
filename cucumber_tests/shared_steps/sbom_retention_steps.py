"""Step definitions for SBOM retention scenarios.

Provides SBOM-specific assertions: file counts per application directory,
removal tracking via pipeline logs, and sparse-file inflation for total-size-limit tests.
"""
import os

from pytest_bdd import given, then, parsers


@given(parsers.parse('SBOM mtimes are assigned by version index in "{app}"'))
def assign_sbom_mtimes_by_version(workspace, app: str):
    """Set mtime on each *.sbom.json so that numeric version order equals age order.

    Files are sorted by the integer N in <app>-vN.sbom.json. The oldest gets
    mtime = base, the newest gets mtime = base + (count-1)*1. This makes the
    retention sort deterministic and name-assertable regardless of checkout time.
    """
    app_dir = workspace.sboms_dir / app
    assert app_dir.exists(), f"SBOM directory {app_dir} does not exist"
    files = sorted(
        app_dir.glob("*.sbom.json"),
        key=lambda f: int(f.name.replace(".sbom.json", "").rsplit("-v", 1)[-1]),
    )
    base_mtime = 1_000_000_000
    for idx, f in enumerate(files):
        os.utime(f, (base_mtime + idx, base_mtime + idx))


@then('no SBOM files were removed')
def no_sbom_files_removed(workspace):
    """Assert that the pipeline did not emit any SBOM removal log lines."""
    output = workspace.stdout + "\n" + workspace.stderr
    removed = [line for line in output.splitlines()
               if "Removing file:" in line or "Removing legacy SBOM file:" in line]
    assert not removed, f"Expected no SBOM removals, but found {len(removed)}:\n" + "\n".join(removed)


@then(parsers.parse('{count:d} SBOM files were removed in total'))
def sbom_files_removed_total(workspace, count: int):
    """Count 'Removing file:' and 'Removing legacy SBOM file:' lines in pipeline output."""
    output = workspace.stdout + "\n" + workspace.stderr
    removed = sum(1 for line in output.splitlines()
                  if "Removing file:" in line or "Removing legacy SBOM file:" in line)
    assert removed == count, f"Expected {count} removed SBOM files, got {removed}"


@then(parsers.parse('the SBOM directory "{app}" contains {count:d} files'))
def sbom_directory_contains_files(workspace, app: str, count: int):
    """Assert that the per-application SBOM subdirectory has exactly count files."""
    app_dir = workspace.sboms_dir / app
    assert app_dir.exists(), f"SBOM directory {app_dir} does not exist"
    actual = len(list(app_dir.glob("*.sbom.json")))
    assert actual == count, f"Expected {count} files in {app}, found {actual}"


@then('only the single most recent SBOM file remains in each application directory')
def single_most_recent_remains(workspace):
    """Assert exactly 1 SBOM file in every per-application subdirectory."""
    for app_dir in workspace.sboms_dir.iterdir():
        if app_dir.is_dir():
            actual = len(list(app_dir.glob("*.sbom.json")))
            assert actual == 1, (
                f"Expected exactly 1 file in {app_dir.name}, found {actual}"
            )


@given('the SBOM files are inflated to exceed the size limit')
def inflate_sbom_files(workspace):
    """Create sparse files that make the total /sboms/ size exceed 600 MB.

    Distributes roughly 500 MB across the first file in each application
    subdirectory via sparse seek, ensuring total exceeds the 600 MB threshold.
    """
    app_dirs = [d for d in workspace.sboms_dir.iterdir() if d.is_dir()]
    per_app_mb = 500  # 500 MB per app → 3 apps × 500 = 1500 MB > 600
    for app_dir in app_dirs:
        files = sorted(app_dir.glob("*.sbom.json"))
        if files:
            target = files[-1]
            mtime_before = target.stat().st_mtime
            with open(target, "r+b") as f:
                f.seek(int(per_app_mb * 1024 * 1024) - 1)
                f.write(b"\0")
            # restore mtime so that assign_sbom_mtimes_by_version ordering is preserved
            os.utime(target, (mtime_before, mtime_before))


@then(parsers.parse('the SBOM directory "{app}" contains exactly the files "{filenames}"'))
def sbom_directory_contains_exactly(workspace, app: str, filenames: str):
    """Assert the per-application SBOM directory holds exactly the named files (comma-separated)."""
    expected = set(filenames.split(","))
    app_dir = workspace.sboms_dir / app
    assert app_dir.exists(), f"SBOM directory {app_dir} does not exist"
    actual = {f.name for f in app_dir.glob("*.sbom.json")}
    assert actual == expected, (
        f"SBOM directory '{app}' mismatch.\n"
        f"  Expected: {sorted(expected)}\n"
        f"  Actual:   {sorted(actual)}\n"
        f"STDOUT: {workspace.stdout}\nSTDERR: {workspace.stderr}"
    )


@then('no flat SBOM files remain at the top of the sboms directory')
def no_flat_sbom_files_remain(workspace):
    """Assert no *.sbom.json files remain directly under /sboms/ (only subdirs)."""
    flat_files = list(workspace.sboms_dir.glob("*.sbom.json"))
    assert not flat_files, (
        f"Expected no flat SBOM files, but found: {[f.name for f in flat_files]}\n"
        f"STDOUT: {workspace.stdout}\nSTDERR: {workspace.stderr}"
    )
