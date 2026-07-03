import os
from pathlib import Path

appdef_content = """name: app1
registryName: default-registry
groupId: org.test
artifactId: test-app
supportParallelDeploy: false
deployParameters: {}
technicalConfigurationParameters: {}
"""

regdef_content = """name: default-registry
credentialsId: dummy
dockerConfig:
  groupName: dummy
  groupUri: dummy
  releaseRepoName: dummy
  releaseUri: dummy
  snapshotRepoName: dummy
  snapshotUri: dummy
  stagingRepoName: dummy
  stagingUri: dummy
mavenConfig:
  fullRepositoryUrl: dummy
  releaseGroup: dummy
  repositoryDomainName: dummy
  snapshotGroup: dummy
  targetRelease: dummy
  targetSnapshot: dummy
  targetStaging: dummy
"""

files_to_update = [
    "/workspace/test_data/ard_ci_1_base/appdefs/app1.yml",
    "/workspace/test_data/ard_ci_1_base/regdefs/registry1.yml",
    "/workspace/test_data/ard_tr_2_base/appdefs/app1.yml",
    "/workspace/test_data/ard_tr_2_base/configuration/appdefs/app1.yml",
    "/workspace/test_data/ard_tr_2_base/configuration/regdefs/registry1.yml",
    "/workspace/test_data/ard_tr_2_base/regdefs/registry1.yml",
    "/workspace/test_data/ard_tr_2_base/templates/appdefs/app1.yml",
    "/workspace/test_data/ard_tr_2_base/templates/regdefs/registry1.yml",
    "/workspace/test_data/ard_ud_1_base/configuration/appdefs/app1.yml"
]

for file_path in files_to_update:
    # Ensure it's not starting with /workspace when running outside docker if needed, but we'll run it in docker.
    if os.path.exists(file_path):
        if "app1.yml" in file_path:
            with open(file_path, "w") as f:
                f.write(appdef_content)
            print(f"Updated {file_path}")
        elif "registry1.yml" in file_path:
            with open(file_path, "w") as f:
                f.write(regdef_content)
            print(f"Updated {file_path}")
    else:
        print(f"File not found: {file_path}")
