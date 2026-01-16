import os
import shutil
from pathlib import Path

from envgenehelper import openYaml, writeYamlToFile, getenv_with_error, writeToFile, logger


def run_env_test_setup():
    logger.info("Start template testing...")
    base_dir = getenv_with_error('CI_PROJECT_DIR')
    deployer_yaml = openYaml(Path(f"{base_dir}/configuration/deployer.yml"))
    deployer = next(k for k in deployer_yaml.keys() if "deployer" in k)

    configs_conf_path = Path(f"{base_dir}/configuration/config.yml")
    writeYamlToFile(configs_conf_path, "crypt: false\n")

    env_template_vers = getenv_with_error("ENV_TEMPLATE_VERSION")
    env_name = os.getenv("ENV_NAME")
    project_dir = os.getenv("CI_PROJECT_NAME")
    env_template_vers_split = env_template_vers.replace('.', '_')
    cluster_example_url = os.getenv("ansible_var_clusterExampleUrl", "https://test-cluster.example.com")
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
    env_definition_conf_path = Path(f"{base_dir}/configuration/env_definition.yml")
    writeYamlToFile(env_definition_conf_path, env_definition)

    base_path = Path(base_dir)
    version_dir_path = base_path / "environments" / tenant_name / f"{tenant_name}_{env_template_vers_split.replace('-', '_')}" / "Inventory"

    for path in (
            base_path / "environments",
            base_path / "environments" / tenant_name,
            version_dir_path,
    ):
        path.mkdir(parents=True, exist_ok=True)
        logger.info("Created directory: %s", path)

    shutil.copy(env_definition_conf_path, version_dir_path / "env_definition.yml")

    env_name = f"{tenant_name}/{tenant_name}_{env_template_vers_split.replace('-', '_')}"
    environment_name = f"{tenant_name}_{env_template_vers_split.replace('-', '_')}"

    for k, v in {"CLUSTER_NAME": tenant_name, "ENVIRONMENT_NAME": environment_name, "ENV_NAME": env_name}.items():
        os.environ[k] = v
        logger.info("Env var set: %s=%s", k, v)

    set_variable_path = base_dir / "set_variable.txt"
    writeToFile(set_variable_path, env_name)
