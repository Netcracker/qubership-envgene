from pytest_bdd import scenarios, then
from pathlib import Path
from tests.shared_steps.unified_pipeline_steps import *
from tests.shared_steps.common_steps import *

scenarios('../features/effective_set_generation/effective-set-no-sbom.feature')


@then("the effective set contains only topology and pipeline contexts")
def effective_set_no_sd_contexts(workspace):
    """
    UC-ES-NOSBOM-1: In No-SD mode (no incoming SD, no existing Full SD), the
    effective-set directory must contain 'topology' and 'pipeline' subdirectories
    and must NOT contain 'deployment', 'runtime', or 'cleanup' subdirectories.

    Per documentation (docs/features/effective-set-generation.md, No-SD Mode):
      Applied when the pipeline runs without an incoming SD and no Full SD exists
      in the repository. Only topology and pipeline contexts are produced.
    """
    env_dir = workspace.builder.get_env_dir("test-cluster", "test-env")
    es_dir = env_dir / "effective-set"

    assert es_dir.exists(), (
        f"effective-set directory was not created at {es_dir}\n"
        f"STDOUT:\n{workspace.stdout}\nSTDERR:\n{workspace.stderr}"
    )

    present = {p.name for p in es_dir.iterdir() if p.is_dir()}

    assert "topology" in present or "pipeline" in present, (
        f"Neither 'topology' nor 'pipeline' context found in {es_dir}. "
        f"Present directories: {present}\n"
        f"STDOUT:\n{workspace.stdout}\nSTDERR:\n{workspace.stderr}"
    )

    unexpected = present & {"deployment", "runtime", "cleanup"}
    assert not unexpected, (
        f"No-SD mode must not produce {unexpected} contexts, "
        f"but they were found in {es_dir}. "
        f"Present directories: {present}\n"
        f"STDOUT:\n{workspace.stdout}\nSTDERR:\n{workspace.stderr}"
    )
