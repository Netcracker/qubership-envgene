import os
import shutil
import yaml
from pathlib import Path

# Get project root correctly
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
TEST_DATA_DIR = PROJECT_ROOT / 'test_data'
GOLDEN_DIR = TEST_DATA_DIR / 'golden'
E2E_DIR = TEST_DATA_DIR / 'e2e'

def write_yaml(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, sort_keys=False)

def write_text(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def create_base_structure(base_dir: Path):
    # Minimal config and inventory
    config_dir = base_dir / 'configuration'
    write_yaml(config_dir / 'config.yml', {"crypt": False, "placement_mode": "dual"})
    
    env_dir = base_dir / 'environments' / 'test-cluster' / 'test-env' / 'Inventory'
    write_yaml(env_dir / 'env_definition.yml', {
        "envTemplate": {
            "name": "test",
            "version": "1.0.0",
            "templateArtifact": {
                "artifact": {
                    "group_id": "org.test",
                    "artifact_id": "test-artifact",
                    "version": "v1"
                },
                "templateRepository": "maven-repo",
                "repository": "maven-repo",
                "registry": "test-registry"
            }
        },
        "inventory": {
            "cloudName": "test-cluster",
            "tenantName": "test-tenant",
            "environmentName": "test-env"
        }
    })

def copy_base_to_golden(base_dir: Path, ref_dir: Path):
    shutil.copytree(base_dir, ref_dir, dirs_exist_ok=True)

# The content in conftest.py zip
APP1_YML = "name: app1\nregistryName: default-registry\ngroupId: org.test\nartifactId: test-app\nsupportParallelDeploy: false\ndeployParameters: {}\ntechnicalConfigurationParameters: {}\n"
REG1_YML = "name: default-registry\ncredentialsId: dummy\ndockerConfig:\n  groupName: dummy\n  groupUri: dummy\n  releaseRepoName: dummy\n  releaseUri: dummy\n  snapshotRepoName: dummy\n  snapshotUri: dummy\n  stagingRepoName: dummy\n  stagingUri: dummy\nmavenConfig:\n  fullRepositoryUrl: dummy\n  releaseGroup: dummy\n  repositoryDomainName: dummy\n  snapshotGroup: dummy\n  targetRelease: dummy\n  targetSnapshot: dummy\n  targetStaging: dummy\n"
APP3_OFFSITE_YML = "name: app3\ngroupId: org.test\nartifactId: app3\nregistryName: off-site-registry-X\nsupportParallelDeploy: false\ndeployParameters: {}\ntechnicalConfigurationParameters: {}\n"
APP3_ONSITE_YML = "name: app3\ngroupId: org.test\nartifactId: app3\nregistryName: on-site-registry\nsupportParallelDeploy: false\ndeployParameters: {}\ntechnicalConfigurationParameters: {}\n"
REG3_YML = "name: off-site-registry-X\ncredentialsId: dummy\ndockerConfig:\n  groupName: dummy\n  groupUri: dummy\n  releaseRepoName: dummy\n  releaseUri: dummy\n  snapshotRepoName: dummy\n  snapshotUri: dummy\n  stagingRepoName: dummy\n  stagingUri: dummy\nmavenConfig:\n  fullRepositoryUrl: dummy\n  releaseGroup: dummy\n  repositoryDomainName: dummy\n  snapshotGroup: dummy\n  targetRelease: dummy\n  targetSnapshot: dummy\n  targetStaging: dummy\n"

def create_stubs():
    E2E_DIR.mkdir(parents=True, exist_ok=True)
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------
    # UC-ARD-TR-1: Basic AppDef/RegDef template rendering
    # ---------------------------------------------------------
    uc_1_base = E2E_DIR / 'uc_ard_tr_1_base'
    uc_1_ref = GOLDEN_DIR / 'ref-uc-ard-tr-1'
    
    if uc_1_base.exists(): shutil.rmtree(uc_1_base)
    if uc_1_ref.exists(): shutil.rmtree(uc_1_ref)
    
    create_base_structure(uc_1_base)
    # The templates will be downloaded from mock nexus
    
    # Golden
    copy_base_to_golden(uc_1_base, uc_1_ref)
    write_text(uc_1_ref / 'appdefs' / 'app1.yml', APP1_YML)
    write_text(uc_1_ref / 'regdefs' / 'default-registry.yml', REG1_YML)
    write_text(uc_1_ref / 'appdefs' / 'app3.yml', APP3_OFFSITE_YML)
    write_text(uc_1_ref / 'regdefs' / 'off-site-registry-X.yml', REG3_YML)
    write_text(uc_1_ref / 'environments' / 'test-cluster' / 'test-env' / 'AppDefs' / 'app1.yml', APP1_YML)
    write_text(uc_1_ref / 'environments' / 'test-cluster' / 'test-env' / 'RegDefs' / 'default-registry.yml', REG1_YML)

    # ---------------------------------------------------------
    # UC-ARD-TR-2: Basic AppDef/RegDef template delete
    # ---------------------------------------------------------
    uc_2_base = E2E_DIR / 'uc_ard_tr_2_base'
    uc_2_ref = GOLDEN_DIR / 'ref-uc-ard-tr-2'
    
    if uc_2_base.exists(): shutil.rmtree(uc_2_base)
    if uc_2_ref.exists(): shutil.rmtree(uc_2_ref)
    
    create_base_structure(uc_2_base)
    write_text(uc_2_base / 'environments' / 'test-cluster' / 'test-env' / 'AppDefs' / 'app1.yml', APP1_YML)
    write_text(uc_2_base / 'environments' / 'test-cluster' / 'test-env' / 'RegDefs' / 'default-registry.yml', REG1_YML)
    
    # Golden
    copy_base_to_golden(uc_2_base, uc_2_ref)
    write_text(uc_2_ref / 'appdefs' / 'app1.yml', APP1_YML)
    write_text(uc_2_ref / 'regdefs' / 'default-registry.yml', REG1_YML)
    write_text(uc_2_ref / 'appdefs' / 'app3.yml', APP3_OFFSITE_YML)
    write_text(uc_2_ref / 'regdefs' / 'off-site-registry-X.yml', REG3_YML)

    # ---------------------------------------------------------
    # UC-ARD-TR-3: Shared template repository, off-site instance rendering
    # ---------------------------------------------------------
    uc_3_base = E2E_DIR / 'uc_ard_tr_3_base'
    uc_3_ref = GOLDEN_DIR / 'ref-uc-ard-tr-3'
    
    if uc_3_base.exists(): shutil.rmtree(uc_3_base)
    if uc_3_ref.exists(): shutil.rmtree(uc_3_ref)
    
    create_base_structure(uc_3_base)
    # The templates app3.yml.j2 and off-site-registry-X.yml.j2 will be in mock nexus
    
    # Golden
    copy_base_to_golden(uc_3_base, uc_3_ref)
    write_text(uc_3_ref / 'appdefs' / 'app1.yml', APP1_YML)
    write_text(uc_3_ref / 'regdefs' / 'default-registry.yml', REG1_YML)
    write_text(uc_3_ref / 'environments' / 'test-cluster' / 'test-env' / 'AppDefs' / 'app1.yml', APP1_YML)
    write_text(uc_3_ref / 'environments' / 'test-cluster' / 'test-env' / 'RegDefs' / 'default-registry.yml', REG1_YML)
    write_text(uc_3_ref / 'appdefs' / 'app3.yml', APP3_OFFSITE_YML)
    write_text(uc_3_ref / 'regdefs' / 'off-site-registry-X.yml', REG3_YML)
    write_text(uc_3_ref / 'environments' / 'test-cluster' / 'test-env' / 'AppDefs' / 'app3.yml', APP3_OFFSITE_YML)
    write_text(uc_3_ref / 'environments' / 'test-cluster' / 'test-env' / 'RegDefs' / 'off-site-registry-X.yml', REG3_YML)

    # ---------------------------------------------------------
    # UC-ARD-TR-4: Shared template repository, on-site instance rendering
    # ---------------------------------------------------------
    uc_4_base = E2E_DIR / 'uc_ard_tr_4_base'
    uc_4_ref = GOLDEN_DIR / 'ref-uc-ard-tr-4'
    
    if uc_4_base.exists(): shutil.rmtree(uc_4_base)
    if uc_4_ref.exists(): shutil.rmtree(uc_4_ref)
    
    create_base_structure(uc_4_base)
    write_yaml(uc_4_base / 'environments' / 'configuration' / 'appregdef_config.yaml', {
        "appdefs": {
            "overrides": {
                "registryName": "on-site-registry"
            }
        }
    })
    
    # Golden
    copy_base_to_golden(uc_4_base, uc_4_ref)
    write_text(uc_4_ref / 'appdefs' / 'app1.yml', APP1_YML)
    write_text(uc_4_ref / 'regdefs' / 'default-registry.yml', REG1_YML)
    write_text(uc_4_ref / 'environments' / 'test-cluster' / 'test-env' / 'AppDefs' / 'app1.yml', APP1_YML)
    write_text(uc_4_ref / 'environments' / 'test-cluster' / 'test-env' / 'RegDefs' / 'default-registry.yml', REG1_YML)
    write_text(uc_4_ref / 'appdefs' / 'app3.yml', APP3_ONSITE_YML)
    write_text(uc_4_ref / 'regdefs' / 'off-site-registry-X.yml', REG3_YML)
    write_text(uc_4_ref / 'environments' / 'test-cluster' / 'test-env' / 'AppDefs' / 'app3.yml', APP3_ONSITE_YML)
    write_text(uc_4_ref / 'environments' / 'test-cluster' / 'test-env' / 'RegDefs' / 'off-site-registry-X.yml', REG3_YML)

if __name__ == '__main__':
    create_stubs()
    print("Done generating stubs for UC-ARD-TR.")
