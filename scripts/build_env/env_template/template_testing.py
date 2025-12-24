import os
import shutil

from envgenehelper import openYaml, writeYamlToFile, getenv_with_error, writeToFile
from envgenehelper.config_helper import base_dir, ENVGENE_CONFIG_PATH


def run_env_test_setup():
    deployer_yaml = openYaml(base_dir / "configuration/deployer.yml")
    deployer = next(k for k in deployer_yaml.keys() if "deployer" in k)

    configs_conf_path = ENVGENE_CONFIG_PATH
    writeYamlToFile(configs_conf_path, "crypt: false\n")

    env_name = getenv_with_error("ENV_NAME")
    env_template_vers = getenv_with_error("ENV_TEMPLATE_VERSION")
    project_dir = getenv_with_error("CI_PROJECT_DIR")
    env_template_vers_split = env_template_vers.replace('.', '_')
    cluster_example_url = os.getenv("ansible_var_clusterExampleUrl")
    tenant_name = f"template_testing_{project_dir}_{env_name}"

    build_env_registry = os.getenv("ansible_var_build_env_registry")
    build_env_repository = os.getenv("ansible_var_build_env_repository")
    build_env_template_repository = os.getenv("ansible_var_build_env_templateRepository")
    group_id = os.getenv("GROUP_ID")
    artifact_id = os.getenv("ARTIFACT_ID")

    definition_env_name = "env-test"
    env_definition = {
        "inventory": {
            "environmentName": definition_env_name,
            "cloudName": env_template_vers_split.replace("-", "_"),
            "tenantName": tenant_name,
            "deployer": deployer,
            "clusterUrl": cluster_example_url,
            "config": {
                "updateCredIdsWithEnvName": True,
                "updateRPOverrideNameWithEnvName": False,
            },
        },
        "envTemplate": {
            "name": env_name,
            "templateArtifact": {
                "registry": build_env_registry,
                "repository": build_env_repository,
                "templateRepository": build_env_template_repository,
                "artifact": {
                    "group_id": group_id,
                    "artifact_id": artifact_id,
                    "version": env_template_vers,
                },
            },
        },
    }

    env_definition_conf_path = base_dir / "configuration" / "env_definition.yml"
    writeYamlToFile(env_definition_conf_path, env_definition)
    env_definition = openYaml(env_definition_conf_path)

    registry_config_path = base_dir / "configuration" / "registry.yml"
    build_env_username = os.getenv("ansible_var_build_env_username")
    build_env_password = os.getenv("ansible_var_build_env_password")
    build_env_release_repository = os.getenv("ansible_var_build_env_releaseRepository")
    build_env_snapshot_repository = os.getenv("ansible_var_build_env_snapshotRepository")
    build_env_staging_repository = os.getenv("ansible_var_build_env_stagingRepository")
    build_env_proxy_repository = os.getenv("ansible_var_build_env_proxyRepository")
    build_env_release_template_repository = os.getenv("ansible_var_build_env_releaseTemplateRepository")
    build_env_snapshot_template_repository = os.getenv("ansible_var_build_env_snapshotTemplateRepository")
    build_env_staging_template_repository = os.getenv("ansible_var_build_env_stagingTemplateRepository")

    registry_config = {
        "artifactorycn": {
            "username": build_env_username,
            "password": build_env_password,
            "releaseRepository": build_env_release_repository,
            "snapshotRepository": build_env_snapshot_repository,
            "stagingRepository": build_env_staging_repository,
            "proxyRepository": build_env_proxy_repository,
            "releaseTemplateRepository": build_env_release_template_repository,
            "snapshotTemplateRepository": build_env_snapshot_template_repository,
            "stagingTemplateRepository": build_env_staging_template_repository,
        }
    }

    writeYamlToFile(registry_config_path, registry_config)
    # registry_config = openYaml(registry_config_path)

    tenant_name = env_definition['inventory']['tenantName']

    envs_directory_path = base_dir / "environments"
    envs_directory_path.mkdir(parents=True, exist_ok=True)
    (envs_directory_path / tenant_name).mkdir(parents=True, exist_ok=True)
    version_path = envs_directory_path / tenant_name / f"{tenant_name}_{env_template_vers_split.replace('-', '_')}" / "Inventory"
    version_path.mkdir(parents=True, exist_ok=True)

    src = env_definition_conf_path
    dest = version_path / "env_definition.yml"
    shutil.copy(src, dest)

    env_name = f"{tenant_name}/{tenant_name}_{env_template_vers_split.replace('-', '_')}"
    # cluster_name = tenant_name
    # environment_name = f"{tenant_name}_{env_template_vers_split.replace('-', '_')}"

    set_variable_path = base_dir / "set_variable.txt"
    writeToFile(set_variable_path, env_name)
