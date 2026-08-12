"""Step definitions for SBOM retention scenarios.

Provides SBOM-specific assertions: file counts per application directory,
removal tracking via pipeline logs, and sparse-file inflation for total-size-limit tests.
"""
import os
import time

from pytest_bdd import given, then, parsers


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
    """Create sparse files that make the total /sboms/ size exceed 1200 MB.

    Distributes roughly 500 MB across the first file in each application
    subdirectory via sparse seek, ensuring total exceeds the 1200 MB threshold.
    """
    app_dirs = [d for d in workspace.sboms_dir.iterdir() if d.is_dir()]
    per_app_mb = 500  # 500 MB per app → 3 apps × 500 = 1500 MB > 1200
    for app_dir in app_dirs:
        files = sorted(app_dir.glob("*.sbom.json"))
        if files:
            target = files[0]
            with open(target, "r+b") as f:
                f.seek(int(per_app_mb * 1024 * 1024) - 1)
                f.write(b"\0")
