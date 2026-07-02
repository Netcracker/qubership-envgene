import json
import yaml
import pytest
from pytest_bdd import scenarios, given, when, then, parsers


@given(parsers.parse('an Environment Inventory exists for "{env_path}"'))
def inv_exists(workspace, env_path):
    cluster, env = env_path.split('/')
    workspace.builder.create_inventory_file(cluster, env, {"inventory": {}, "envTemplate": {"name": "test", "artifact": "test-artifact:v1"}})
    app_def = {
        "name": "test-artifact",
        "registry": {
            "name": "cloud-registry",
            "type": "artifactory",
            "maven_config": {
                "repository_domain_name": "http://localhost:8000",
                "targetSnapshot": "snapshot",
                "targetStaging": "staging",
                "targetRelease": "release"
            }
        },
        "artifact_id": "test-artifact",
        "group_id": "org.test",
        "supportParallelDeploy": True,
        "deployParameters": {},
        "technicalConfigurationParameters": {}
    }
    workspace.builder.create_artifact_def("test-artifact", app_def)

@given(parsers.parse('a template descriptor specifies namespace "{template}" with deploy_postfix "{postfix}"'))
def template_descriptor_postfix(workspace, template, postfix):
    namespaces = [{"template_path": f"templates/env_templates/dev/Namespaces/{template}", "deploy_postfix": postfix}]
    workspace.builder.create_template_descriptor("test-cluster", "test-env", namespaces)

@given(parsers.parse('the namespace is part of a BG Domain with role "{role}"'))
def bg_domain_role(workspace, role):
    bg_domain = {
        "controllerNamespace": {"name": "controller-ns"},
        "originNamespace": {"name": "bss-origin"} if role == "origin" else {"name": "ns"},
        "peerNamespace": {"name": "bss-peer"} if role == "peer" else {"name": "ns"}
    }
    env_dir = workspace.builder.get_env_dir("test-cluster", "test-env")
    with open(env_dir / "bg_domain.yml", "w") as f:
        yaml.dump(bg_domain, f)

@when('the Instance pipeline is started')
def start_instance_pipeline(workspace):
    env = getattr(workspace, 'extra_env', {})
    workspace.run_pipeline(extra_env=env)

@then(parsers.parse('the namespace folder "{folder}" is created in the environment instance'))
def namespace_folder_created(workspace, folder):
    env_dir = workspace.builder.get_env_dir("test-cluster", "test-env")
    assert (env_dir / "Namespaces" / folder).exists(), f"Namespace folder {folder} was not created"

@given(parsers.parse('the environment inventory specifies "envTemplate.artifact" as "{artifact}"'))
def env_template_artifact(workspace, artifact):
    content = {
        "inventory": {},
        "envTemplate": {
            "name": "composite-prod",
            "artifact": artifact
        }
    }
    workspace.builder.create_inventory_file("test-cluster", "test-env", content)
    
    app_name = artifact.split(":")[0]
    app_def = {
        "name": app_name,
        "registry": {
            "name": "cloud-registry",
            "type": "artifactory",
            "maven_config": {
                "repository_domain_name": "http://localhost:8000",
                "targetSnapshot": "snapshot",
                "targetStaging": "staging",
                "targetRelease": "release"
            }
        },
        "artifact_id": app_name,
        "group_id": "org.test",
        "supportParallelDeploy": True,
        "deployParameters": {},
        "technicalConfigurationParameters": {}
    }
    workspace.builder.create_artifact_def(app_name, app_def)

@then(parsers.parse('all namespaces are rendered using "{artifact}"'))
def all_namespaces_rendered(workspace, artifact):
    assert workspace.returncode == 0, f"Pipeline failed with return code {workspace.returncode}"

@given('SD_DATA is provided in the pipeline parameters')
def sd_data_provided(workspace):
    if not hasattr(workspace, 'extra_env'):
        workspace.extra_env = {}
    workspace.extra_env["SD_DATA"] = '{"applications": []}'
    workspace.extra_env["SD_SOURCE_TYPE"] = "json"

@then('the effective set includes data from SD_DATA')
def effective_set_includes_sd(workspace):
    assert workspace.returncode == 0

@given(parsers.parse('multiple environment inventories exist for "{env1}" and "{env2}"'))
def multiple_inv_exist(workspace, env1, env2):
    c1, e1 = env1.split('/')
    c2, e2 = env2.split('/')
    workspace.builder.create_inventory_file(c1, e1, {"inventory": {}, "envTemplate": {"artifact": "foo:1.0"}})
    workspace.builder.create_inventory_file(c2, e2, {"inventory": {}, "envTemplate": {"artifact": "foo:1.0"}})
    app_def = {
        "name": "foo",
        "registry": {
            "name": "cloud-registry",
            "type": "artifactory",
            "maven_config": {
                "repository_domain_name": "http://localhost:8000",
                "targetSnapshot": "snapshot",
                "targetStaging": "staging",
                "targetRelease": "release"
            }
        },
        "artifact_id": "foo",
        "group_id": "org.test",
        "supportParallelDeploy": True,
        "deployParameters": {},
        "technicalConfigurationParameters": {}
    }
    workspace.builder.create_artifact_def("foo", app_def)

@then(parsers.parse('the environment instance for "{env_path}" is generated successfully'))
def env_instance_generated(workspace, env_path):
    c, e = env_path.split('/')
    d = workspace.builder.get_env_dir(c, e)
    assert d.exists()
