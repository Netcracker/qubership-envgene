import os
import shutil
from pathlib import Path
from urllib.parse import urlparse

import yaml
from envgenehelper import openYaml, writeYamlToFile, getenv_with_error, writeToFile, logger, convert_dict_to_yaml, \
    store_value_to_yaml


def run_env_test_setup():
    logger.info("Start set up environment for template testing")
    base_dir = getenv_with_error('CI_PROJECT_DIR')
    deployer_yaml = openYaml(Path(f"{base_dir}/configuration/deployer.yml"))
    deployer = next(k for k in deployer_yaml.keys() if "deployer" in k)

    configs_conf_path = Path(f"{base_dir}/configuration/config.yml")
    writeYamlToFile(configs_conf_path, yaml.safe_load("crypt: false\n"))

    env_template_art_vers = getenv_with_error("ENV_TEMPLATE_VERSION")
    env_name = getenv_with_error("ENV_NAME")
    env_template_vers_split = env_template_art_vers.split(':')[1].replace('.', '_')
    cluster_example_url = os.getenv("ansible_var_clusterExampleUrl", "https://test-cluster.example.com")
    tenant_name = getenv_with_error("CLUSTER_NAME")

    definition_env_name = "env-test"
    env_template_version_normalized = f"{env_template_vers_split.replace('-', '_')}"
    env_definition = {
        "inventory": {
            "environmentName": definition_env_name,
            "cloudName": env_template_version_normalized,
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
            "artifact": env_template_art_vers
        },
    }

    logger.info(f"env_definition: {env_definition}")
    env_definition_conf_path = Path(f"{base_dir}/configuration/env_definition.yml")
    writeYamlToFile(env_definition_conf_path, env_definition)

    base_path = Path(base_dir)
    version_dir_path = base_path / "environments" / tenant_name / f"{tenant_name}_{env_template_version_normalized}" / "Inventory"

    for path in (
            base_path / "environments",
            base_path / "environments" / tenant_name,
            version_dir_path,
    ):
        path.mkdir(parents=True, exist_ok=True)
        logger.info("Created directory: %s", path)

    shutil.copy(env_definition_conf_path, version_dir_path / "env_definition.yml")

    env_name = f"{tenant_name}/{tenant_name}_{env_template_version_normalized}"

    set_variable_path = Path(f"{base_dir}/set_variable.txt")
    writeToFile(set_variable_path, env_name)

    art_id = os.getenv("ARTIFACT_ID")
    group_id = os.getenv("GROUP_ID")
    art_url = os.getenv("ARTIFACT_URL")
    group_path = group_id.replace(".", "/")
    build_env_staging_repository = os.getenv("build_env_stagingRepository", art_url.split(group_path)[0] + group_path)

    cred_path = Path(f"{base_dir}/configuration/credentials/credentials.yml")
    cred_id = "artifactory-cred"
    cred = {
        "type": "usernamePassword",
        "data": {
            "username": os.getenv("build_env_username", ""),
            "password": os.getenv("build_env_password", "")
        }
    }
    cred_config = openYaml(cred_path)
    store_value_to_yaml(cred_config, cred_id, convert_dict_to_yaml(cred))
    writeYamlToFile(cred_path, cred_config)

    parsed = urlparse(build_env_staging_repository)
    art_def = {
        "name": art_id,
        "groupId": group_id,
        "artifactId": art_id,
        "registry": {
            "name": "artifactory",
            "credentialsId": cred_id,
            "mavenConfig": {
                "repositoryDomainName": f"{parsed.scheme}://{parsed.netloc}/",
                "targetStaging": parsed.path.strip("/").split("/", 1)[0],
                "targetSnapshot": "",
                "targetRelease": ""
            },
        },
    }
    logger.info(f"Artifact definition: {art_def}")
    art_config_path = f"{base_path}/configuration/artifact_definitions/{art_id}.yaml"
    writeYamlToFile(art_config_path, art_def)
