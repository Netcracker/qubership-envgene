import sys
import pytest
import os
import subprocess
import time
import json
import zipfile
import urllib.request
from pathlib import Path
from tests.framework.workspace import EnvGeneWorkspace
from tests.step_defs.common_steps import *

@pytest.fixture(scope="session", autouse=True)
def mock_nexus(tmp_path_factory):
    base_dir = tmp_path_factory.mktemp("mock_nexus")
    
    art_dir = base_dir / "release" / "org" / "test" / "test-artifact" / "v1"
    art_dir.mkdir(parents=True, exist_ok=True)
    with open(art_dir / "test-artifact-v1.json", "w") as f:
        json.dump({"configurations": [{"maven_repository": "http://localhost:8000/release", "artifacts": [{"id": "org.test:test-artifact:v1"}]}]}, f)
    with zipfile.ZipFile(art_dir / "test-artifact-v1.zip", "w") as z:
        z.writestr("templates/env_templates/test.yml", "tenant: '{{ templates_dirs.common }}/Tenant.yml.j2'\ncloud: '{{ templates_dirs.common }}/Cloud.yml.j2'\nbg_domain: '{{ templates_dirs.common }}/BgDomain.yml.j2'\nnamespaces:\n  - template_path: '{{ templates_dirs.common }}/Namespace.yml.j2'\n    deploy_postfix: core\n    template_override: {name: core}\n  - template_path: '{{ templates_dirs.common }}/Namespace.yml.j2'\n    deploy_postfix: bss\n    template_override: {name: bss-origin}\n")
        z.writestr("templates/BgDomain.yml.j2", "name: dummy-bg-domain\ncontrollerNamespace: {name: controller-ns, credentials: dummy}\noriginNamespace: {name: bss-origin, credentials: dummy}\npeerNamespace: {name: bss-peer, credentials: dummy}\n")
        z.writestr("templates/env_templates/composite-prod.yml", "tenant: '{{ templates_dirs.common }}/Tenant.yml.j2'\ncloud: '{{ templates_dirs.common }}/Cloud.yml.j2'\nnamespaces: []\n")
        z.writestr("templates/Tenant.yml.j2", "name: dummy-tenant\nregistryName: default\ncredential: dummy-cred\nglobalE2EParameters: {}\ndeployParameters: {}\ndeployParameterSets: []\ne2eParameters: {}\ne2eParameterSets: []\ntechnicalConfigurationParameters: {}\ntechnicalConfigurationParameterSets: []\n")
        z.writestr("templates/Cloud.yml.j2", "name: dummy-cloud\nnamespacePrefix: dummy\ndeployParameters: {}\ndeployParameterSets: []\ne2eParameters: {}\ne2eParameterSets: []\ntechnicalConfigurationParameters: {}\ntechnicalConfigurationParameterSets: []\napiUrl: dummy\napiPort: 80\ndashboardUrl: dummy\nlabels: []\ndefaultCredentialsId: dummy\nprotocol: dummy\nmaasConfig: {credentialsId: dummy}\nvaultConfig: {credentialsId: dummy}\nconsulConfig: {credentialsId: dummy, tokenSecret: dummy}\ndbaasConfigs: []\n")
        z.writestr("templates/Namespace.yml.j2", "name: dummy-namespace\nlabels: []\ndeployParameters: {}\ndeployParameterSets: []\ne2eParameters: {}\ne2eParameterSets: []\ntechnicalConfigurationParameters: {}\ntechnicalConfigurationParameterSets: []\nisServerSideMerge: false\ncleanInstallApprovalRequired: false\nmergeDeployParametersAndE2EParameters: false\ncredentialsId: dummy\n")
        z.writestr("templates/appdefs/app1.yml.j2", "name: app1\nregistryName: default-registry\ngroupId: org.test\nartifactId: test-app\nsupportParallelDeploy: false\ndeployParameters: {}\ntechnicalConfigurationParameters: {}\n")
        z.writestr("templates/regdefs/registry1.yml.j2", "name: default-registry\ncredentialsId: dummy\ndockerConfig:\n  groupName: dummy\n  groupUri: dummy\n  releaseRepoName: dummy\n  releaseUri: dummy\n  snapshotRepoName: dummy\n  snapshotUri: dummy\n  stagingRepoName: dummy\n  stagingUri: dummy\nmavenConfig:\n  fullRepositoryUrl: dummy\n  releaseGroup: dummy\n  repositoryDomainName: dummy\n  snapshotGroup: dummy\n  targetRelease: dummy\n  targetSnapshot: dummy\n  targetStaging: dummy\n")
        z.writestr("templates/appdefs/app3.yml.j2", "name: app3\ngroupId: org.test\nartifactId: app3\nregistryName: \"{{ appdefs.overrides.registryName | default('off-site-registry-X') }}\"\nsupportParallelDeploy: false\ndeployParameters: {}\ntechnicalConfigurationParameters: {}\n")
        z.writestr("templates/regdefs/off-site-registry-X.yml.j2", "name: off-site-registry-X\ncredentialsId: dummy\ndockerConfig:\n  groupName: dummy\n  groupUri: dummy\n  releaseRepoName: dummy\n  releaseUri: dummy\n  snapshotRepoName: dummy\n  snapshotUri: dummy\n  stagingRepoName: dummy\n  stagingUri: dummy\nmavenConfig:\n  fullRepositoryUrl: dummy\n  releaseGroup: dummy\n  repositoryDomainName: dummy\n  snapshotGroup: dummy\n  targetRelease: dummy\n  targetSnapshot: dummy\n  targetStaging: dummy\n")
    foo_dir = base_dir / "release" / "org" / "test" / "foo" / "1.0"
    foo_dir.mkdir(parents=True, exist_ok=True)
    with open(foo_dir / "foo-1.0.json", "w") as f:
        json.dump({"configurations": [{"maven_repository": "http://localhost:8000/release", "artifacts": [{"id": "org.test:foo:1.0"}]}]}, f)
    with zipfile.ZipFile(foo_dir / "foo-1.0.zip", "w") as z:
        z.writestr("templates/env_templates/test.yml", "tenant: '{{ templates_dirs.common }}/Tenant.yml.j2'\ncloud: '{{ templates_dirs.common }}/Cloud.yml.j2'\nbg_domain: '{{ templates_dirs.common }}/BgDomain.yml.j2'\nnamespaces:\n  - template_path: '{{ templates_dirs.common }}/Namespace.yml.j2'\n    deploy_postfix: core\n    template_override: {name: core}\n  - template_path: '{{ templates_dirs.common }}/Namespace.yml.j2'\n    deploy_postfix: bss\n    template_override: {name: bss-origin}\n")
        z.writestr("templates/BgDomain.yml.j2", "name: dummy-bg-domain\ncontrollerNamespace: {name: controller-ns, credentials: dummy}\noriginNamespace: {name: bss-origin, credentials: dummy}\npeerNamespace: {name: bss-peer, credentials: dummy}\n")
        z.writestr("templates/env_templates/composite-prod.yml", "tenant: '{{ templates_dirs.common }}/Tenant.yml.j2'\ncloud: '{{ templates_dirs.common }}/Cloud.yml.j2'\nnamespaces: []\n")
        z.writestr("templates/Tenant.yml.j2", "name: dummy-tenant\nregistryName: default\ncredential: dummy-cred\nglobalE2EParameters: {}\ndeployParameters: {}\ndeployParameterSets: []\ne2eParameters: {}\ne2eParameterSets: []\ntechnicalConfigurationParameters: {}\ntechnicalConfigurationParameterSets: []\n")
        z.writestr("templates/Cloud.yml.j2", "name: dummy-cloud\nnamespacePrefix: dummy\ndeployParameters: {}\ndeployParameterSets: []\ne2eParameters: {}\ne2eParameterSets: []\ntechnicalConfigurationParameters: {}\ntechnicalConfigurationParameterSets: []\napiUrl: dummy\napiPort: 80\ndashboardUrl: dummy\nlabels: []\ndefaultCredentialsId: dummy\nprotocol: dummy\nmaasConfig: {credentialsId: dummy}\nvaultConfig: {credentialsId: dummy}\nconsulConfig: {credentialsId: dummy, tokenSecret: dummy}\ndbaasConfigs: []\n")
        z.writestr("templates/Namespace.yml.j2", "name: dummy-namespace\nlabels: []\ndeployParameters: {}\ndeployParameterSets: []\ne2eParameters: {}\ne2eParameterSets: []\ntechnicalConfigurationParameters: {}\ntechnicalConfigurationParameterSets: []\nisServerSideMerge: false\ncleanInstallApprovalRequired: false\nmergeDeployParametersAndE2EParameters: false\ncredentialsId: dummy\n")

    pet_dir = base_dir / "release" / "org" / "test" / "project-env-template" / "v1.2.3"
    pet_dir.mkdir(parents=True, exist_ok=True)
    with open(pet_dir / "project-env-template-v1.2.3.json", "w") as f:
        json.dump({"configurations": [{"maven_repository": "http://localhost:8000/release", "artifacts": [{"id": "org.test:project-env-template:v1.2.3"}]}]}, f)
    with zipfile.ZipFile(pet_dir / "project-env-template-v1.2.3.zip", "w") as z:
        z.writestr("templates/env_templates/test.yml", "tenant: '{{ templates_dirs.common }}/Tenant.yml.j2'\ncloud: '{{ templates_dirs.common }}/Cloud.yml.j2'\nbg_domain: '{{ templates_dirs.common }}/BgDomain.yml.j2'\nnamespaces:\n  - template_path: '{{ templates_dirs.common }}/Namespace.yml.j2'\n    deploy_postfix: core\n    template_override: {name: core}\n  - template_path: '{{ templates_dirs.common }}/Namespace.yml.j2'\n    deploy_postfix: bss\n    template_override: {name: bss-origin}\n")
        z.writestr("templates/BgDomain.yml.j2", "name: dummy-bg-domain\ncontrollerNamespace: {name: controller-ns, credentials: dummy}\noriginNamespace: {name: bss-origin, credentials: dummy}\npeerNamespace: {name: bss-peer, credentials: dummy}\n")
        z.writestr("templates/env_templates/composite-prod.yml", "tenant: '{{ templates_dirs.common }}/Tenant.yml.j2'\ncloud: '{{ templates_dirs.common }}/Cloud.yml.j2'\nnamespaces: []\n")
        z.writestr("templates/Tenant.yml.j2", "name: dummy-tenant\nregistryName: default\ncredential: dummy-cred\nglobalE2EParameters: {}\ndeployParameters: {}\ndeployParameterSets: []\ne2eParameters: {}\ne2eParameterSets: []\ntechnicalConfigurationParameters: {}\ntechnicalConfigurationParameterSets: []\n")
        z.writestr("templates/Cloud.yml.j2", "name: dummy-cloud\nnamespacePrefix: dummy\ndeployParameters: {}\ndeployParameterSets: []\ne2eParameters: {}\ne2eParameterSets: []\ntechnicalConfigurationParameters: {}\ntechnicalConfigurationParameterSets: []\napiUrl: dummy\napiPort: 80\ndashboardUrl: dummy\nlabels: []\ndefaultCredentialsId: dummy\nprotocol: dummy\nmaasConfig: {credentialsId: dummy}\nvaultConfig: {credentialsId: dummy}\nconsulConfig: {credentialsId: dummy, tokenSecret: dummy}\ndbaasConfigs: []\n")
        z.writestr("templates/Namespace.yml.j2", "name: dummy-namespace\nlabels: []\ndeployParameters: {}\ndeployParameterSets: []\ne2eParameters: {}\ne2eParameterSets: []\ntechnicalConfigurationParameters: {}\ntechnicalConfigurationParameterSets: []\nisServerSideMerge: false\ncleanInstallApprovalRequired: false\nmergeDeployParametersAndE2EParameters: false\ncredentialsId: dummy\n")

    test_app_dir = base_dir / "release" / "com" / "test" / "test_app_artifact" / "1.0.0"
    test_app_dir.mkdir(parents=True, exist_ok=True)
    with open(test_app_dir / "test_app_artifact-1.0.0.json", "w") as f:
        json.dump({"applications": [{"version": "test_app:1.0.0", "deployPostfix": "dp1"}], "deployGraph": [{"chunkName": "wave1", "apps": ["test_app:dp1"]}]}, f)
        
    test_app2_dir = base_dir / "release" / "com" / "test" / "test_app_2_artifact" / "2.0.0"
    test_app2_dir.mkdir(parents=True, exist_ok=True)
    with open(test_app2_dir / "test_app_2_artifact-2.0.0.json", "w") as f:
        json.dump({"applications": [{"version": "test_app_2:2.0.0", "deployPostfix": "dp2"}], "deployGraph": [{"chunkName": "wave1", "apps": ["test_app_2:dp2"]}]}, f)

    proc = subprocess.Popen([sys.executable, "tests/mock_server.py", "8000", str(base_dir)])
    
    # Wait for the mock server to start
    for i in range(10):
        try:
            urllib.request.urlopen("http://localhost:8000/")
            break
        except Exception:
            time.sleep(0.5)
    else:
        print("MOCK SERVER FAILED TO START ON PORT 8000")

    yield
    proc.terminate()
    proc.wait()

@pytest.fixture
def workspace(tmp_path):
    return EnvGeneWorkspace(tmp_path)


def pytest_bdd_apply_tag(tag, function):
    """Handle custom Gherkin tags as pytest marks.

    @xfail  — marks the test as expected to fail (known framework gap, not a test bug).
    """
    if tag == "xfail":
        marker = pytest.mark.xfail(
            reason="Known framework gap: ENVGENE_PROJECT is not validated by the orchestrator.",
            strict=False,
        )
        marker(function)
        return True  # tag handled, do not raise unknown-tag warning
    return None  # let pytest-bdd handle all other tags normally
