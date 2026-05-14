from pathlib import Path
from envgenehelper import getenv_with_error, get_env_instances_dir, findAllYamlsInDir, openYaml
from envgenehelper.errors import ValidationError
from .logger import logger
def validate_parameters(env_dir: str = ""):
    if not env_dir:
        environment_name = getenv_with_error('ENVIRONMENT_NAME')
        cluster_name = getenv_with_error('CLUSTER_NAME')
        instances_dir = getenv_with_error('INSTANCES_DIR')

        env_dir = get_env_instances_dir(environment_name, cluster_name, instances_dir)

    logger.info("Starting validation of parameters")

    param_errors = []

    def validate_yaml(entity_name, yaml_data):
        for param_type in ["deployParameters", "e2eParameters", "technicalConfigurationParameters"]:
            params = yaml_data.get(param_type, {})

            if not isinstance(params, dict):
                continue

            for key, value in params.items():
                if is_envgenenullvalue(value):
                    param_errors.append(
                        f"{entity_name}.{param_type}.{key} - is not set"
                    )

    tenant_file = f"{env_dir}/tenant.yml"
    tenant_yaml = openYaml(tenant_file)
    tenant_name = tenant_yaml.get("name", "tenant")
    validate_yaml(tenant_name, tenant_yaml)

    cloud_file = f"{env_dir}/cloud.yml"
    cloud_yaml = openYaml(cloud_file)
    cloud_name = cloud_yaml.get("name", "cloud")
    validate_yaml(cloud_name, cloud_yaml)

    namespaces = findAllYamlsInDir(f"{env_dir}/Namespaces")
    for ns_path in namespaces:
        ns_yaml = openYaml(ns_path)
        namespace_name = ns_yaml.get("name", "namespace")
        validate_yaml(f"namespace.{namespace_name}", ns_yaml)

    if len(param_errors) > 0:
        error_message = "Error while validating parameters:\n"
        for err in param_errors:
            error_message += f"\t{err}\n"

        raise ValidationError(error_message)

    logger.info("Validation of parameters is completed")
