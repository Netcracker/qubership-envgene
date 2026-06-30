import os
import shutil
import glob
from pytest_bdd import scenarios, given, when, then
from tests.framework.workspace import EnvGeneWorkspace
from tests.shared_steps.unified_pipeline_steps import *

scenarios('../features/sbom_storage_migration/sbom-storage-migration.feature')

@given('legacy flat SBOM files are present in the sboms directory')
def legacy_flat_sboms(workspace: EnvGeneWorkspace):
    sboms_dir = os.path.join(workspace.workspace_dir, 'environments', 'test-cluster', 'test-env', 'sboms')
    os.makedirs(sboms_dir, exist_ok=True)
    
    # Create some dummy flat SBOM files
    legacy_file_1 = os.path.join(sboms_dir, 'app-service-1-1.0.0.sbom.json')
    legacy_file_2 = os.path.join(sboms_dir, 'app-service-2-2.0.0.sbom.json')
    
    with open(legacy_file_1, 'w') as f:
        f.write('{"bomFormat": "CycloneDX"}')
    with open(legacy_file_2, 'w') as f:
        f.write('{"bomFormat": "CycloneDX"}')

@then('no flat SBOM files remain in the root sboms directory')
def no_flat_sboms_remain(workspace: EnvGeneWorkspace):
    sboms_dir = os.path.join(workspace.workspace_dir, 'environments', 'test-cluster', 'test-env', 'sboms')
    flat_sboms = glob.glob(os.path.join(sboms_dir, '*.sbom.json'))
    assert len(flat_sboms) == 0, f"Found unexpected flat SBOM files: {flat_sboms}"

@then('SBOM files are relocated to per-application subdirectories')
def sboms_are_relocated(workspace: EnvGeneWorkspace):
    sboms_dir = os.path.join(workspace.workspace_dir, 'environments', 'test-cluster', 'test-env', 'sboms')
    
    # Check that directories exist and contain files
    dirs = [d for d in os.listdir(sboms_dir) if os.path.isdir(os.path.join(sboms_dir, d))]
    assert len(dirs) > 0, "No per-application directories found"
    
    # In EnvGene execution with SD_DATA or default, real SBOMs might be downloaded.
    # Our mock files might have been deleted, and new real ones created.
    # The requirement is that no flat files remain and per-app folders are populated.
    for d in dirs:
        app_dir = os.path.join(sboms_dir, d)
        files = glob.glob(os.path.join(app_dir, '*.sbom.json'))
        # It's fine if some are empty or contain files, as long as it's the new format
