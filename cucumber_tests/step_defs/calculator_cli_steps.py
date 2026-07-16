"""Step definitions for Calculator CLI BDD scenarios.

Covers UC-CC-DP (deployPostfix matching), UC-CC-MR (macro resolution),
UC-CC-HR (cross-level hierarchy references), and UC-CC-CR (cross-context
parameter references) use cases from docs/use-cases/calculator-cli.md.

All scenarios test Effective Set v2.0 generation behaviour via the
unified pipeline orchestrator. Feature-specific steps here add only
assertions that are not provided by shared_steps.
"""
from pathlib import Path

from pytest_bdd import then
from cucumber_tests.framework.workspace import EnvGeneWorkspace


# ── Effective-set generation outcome ─────────────────────────────────────────


@then("the effective set is generated successfully")
def effective_set_generated_successfully(workspace: EnvGeneWorkspace) -> None:
    """Assert that the pipeline completed without error (return code 0).

    This is a semantic alias for 'orchestrator completes successfully'
    tailored specifically for Calculator CLI / Effective Set generation
    scenarios where success means an effective set was produced.
    """
    workspace.assert_success(
        f"Effective Set generation failed.\n"
        f"STDOUT: {workspace.stdout}\n"
        f"STDERR: {workspace.stderr}"
    )
