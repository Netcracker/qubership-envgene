import os
import shutil
from pathlib import Path

from envgenehelper import openYaml, writeYamlToFile, getenv_with_error, writeToFile
from envgenehelper import logger


def run_env_test_setup():
    logger.info("Start template testing...")
    base_dir = getenv_with_error('CI_PROJECT_DIR')
    deployer_yaml = openYaml(Path(f"{base_dir}/configuration/deployer.yml"))
    deployer = next(k for k in deployer_yaml.keys() if "deployer" in k)

    configs_conf_path = Path(f"{base_dir}/configuration/config.yml")
    writeYamlToFile(configs_conf_path, "crypt: false\n")

    env_name = getenv_with_error("ENV_NAME")
    env_template_vers = getenv_with_error("ENV_TEMPLATE_VERSION")
    project_dir = getenv_with_error("CI_PROJECT_DIR")
    env_template_vers_split = env_template_vers.replace('.', '_')
    cluster_example_url = os.getenv("ansible_var_clusterExampleUrl")
    tenant_name = f"template_testing_{project_dir}_{env_name}"

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
            "artifact": env_template_vers
        },
    }

    logger.info(f"env_definition: {env_definition}")
    env_definition_conf_path = base_dir / "configuration" / "env_definition.yml"
    writeYamlToFile(env_definition_conf_path, env_definition)

    envs_directory_path = base_dir / "environments"
    envs_directory_path.mkdir(parents=True, exist_ok=True)
    (envs_directory_path / tenant_name).mkdir(parents=True, exist_ok=True)
    version_path = envs_directory_path / tenant_name / f"{tenant_name}_{env_template_vers_split.replace('-', '_')}" / "Inventory"
    version_path.mkdir(parents=True, exist_ok=True)

    shutil.copy(env_definition_conf_path, version_path / "env_definition.yml")

    env_name = f"{tenant_name}/{tenant_name}_{env_template_vers_split.replace('-', '_')}"
    environment_name = f"{tenant_name}_{env_template_vers_split.replace('-', '_')}"

    os.environ["CLUSTER_NAME"] = tenant_name
    os.environ["ENVIRONMENT_NAME"] = environment_name
    os.environ["ENV_NAME"] = env_name

    set_variable_path = base_dir / "set_variable.txt"
    writeToFile(set_variable_path, env_name)
