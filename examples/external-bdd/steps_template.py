"""
Example Step Definitions (steps_template.py) for an external project.

Copy this file into your project (e.g., tests/step_defs/test_project.py).
"""

from pytest_bdd import scenarios, given, when, then, parsers

# -------------------------------------------------------------------------
# 1. Import the powerful Unified Pipeline Steps from EnvGene!
# -------------------------------------------------------------------------
# By importing these, you instantly get access to all the standard steps 
# like `Given the workspace is initialized...`, `When the unified pipeline 
# orchestrator runs`, and `Then the orchestrator completes successfully`.
#
# You don't need to rewrite them!
from tests.shared_steps.unified_pipeline_steps import *

# -------------------------------------------------------------------------
# 2. Link to your feature file(s)
# -------------------------------------------------------------------------
scenarios('../features/customer-e2e-template.feature')

# -------------------------------------------------------------------------
# 3. Write Custom Project-Specific Steps
# -------------------------------------------------------------------------
# If you need to verify something specific to your project that isn't covered 
# by the standard "matches the reference" step, you can write custom steps here.

@then(parsers.parse('a project-specific audit file is created at "{env_path}"'))
def verify_audit_file(workspace, env_path):
    """
    Example custom assertion.
    `workspace.base_dir` points to the temporary test directory where 
    the pipeline was executed.
    """
    audit_file = workspace.base_dir / "environments" / env_path / "audit.log"
    
    # Assert that the file was created
    assert audit_file.exists(), f"Audit file was not found at {audit_file}"
    
    # You can also check its contents
    content = audit_file.read_text()
    assert "AUDIT SUCCESS" in content, "Audit file missing success string"
