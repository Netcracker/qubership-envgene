"""Step definitions for SBOM storage migration scenarios."""
from pytest_bdd import then


@then('no flat SBOM files remain directly under the sboms directory')
def no_flat_sboms_remain(workspace):
    flat_files = [f for f in workspace.sboms_dir.iterdir() if f.is_file()]
    assert not flat_files, (
        f"Expected no flat SBOM files under {workspace.sboms_dir}, "
        f"but found: {[f.name for f in flat_files]}"
    )
