from envgenehelper import INVENTORY_DIR_NAME, Path, beautifyYaml, getEnvDefinitionPath, \
    get_namespaces_path, get_schema_dir, logger, readYaml, set_nested_yaml_attribute, writeYamlToFile
from envgenehelper.deploy_plan_adapter import DELTA_DEPLOY_PLAN_FILE_NAME, DEPLOY_PLAN_FILE_NAME, EnvgeneDeployPlan

DEPLOYMENT_PROFILE_NAME = "deployment-profile"
RESOURCE_PROFILES_DIR_NAME = "resource_profiles"
RESOURCE_PROFILE_SCHEMA = "resource-profile.schema.json"


def plan_applications(plan_path: Path) -> list[str]:
    applications = []
    for entity in EnvgeneDeployPlan.read(plan_path).entities:
        application = entity.version.split(":")[0]
        if application and application not in applications:
            applications.append(application)
    return applications


def deployed_applications(env_dir: Path) -> list[str] | None:
    inventory = env_dir / INVENTORY_DIR_NAME
    delta_plan = inventory / DELTA_DEPLOY_PLAN_FILE_NAME
    plan = inventory / DEPLOY_PLAN_FILE_NAME
    plan_path = delta_plan if delta_plan.is_file() else plan
    if not plan_path.is_file():
        logger.warning(f"Neither '{delta_plan}' nor '{plan}' is found, so the applications deployed by this run are "
                       f"unknown and the '{DEPLOYMENT_PROFILE_NAME}' override is not generated")
        return None
    applications = plan_applications(plan_path)
    if not applications and plan_path != plan and plan.is_file():
        logger.info(f"'{plan_path}' deploys no application, the applications are read from '{plan}'")
        plan_path = plan
        applications = plan_applications(plan)
    if not applications:
        logger.warning(f"'{plan_path}' deploys no application, so the '{DEPLOYMENT_PROFILE_NAME}' override is not "
                       f"generated")
        return None
    logger.info(f"Applications deployed by this run, read from '{plan_path}': {', '.join(applications)}")
    return applications


def build_deployment_profile_override(env_dir: Path, profile_name: str) -> dict | None:
    applications = deployed_applications(env_dir)
    if applications is None:
        return None
    overridden = [{"name": application, "baseline": profile_name, "services": []} for application in applications]
    logger.info(f"The '{DEPLOYMENT_PROFILE_NAME}' override sets baseline '{profile_name}' as the default of "
                f"{len(overridden)} deployed application(s)")
    return {"name": DEPLOYMENT_PROFILE_NAME, "applications": overridden}


def write_deployment_profile_override(env_dir: Path, profile_name: str) -> Path | None:
    override = build_deployment_profile_override(env_dir, profile_name)
    if override is None:
        return None
    override_path = env_dir / INVENTORY_DIR_NAME / RESOURCE_PROFILES_DIR_NAME / f"{DEPLOYMENT_PROFILE_NAME}.yml"
    if override_path.is_file():
        logger.warning(f"'{override_path}' already exists and is overwritten by the override generated from PROFILE. "
                       f"An override of this name written by hand is lost, so its name is reserved for this step")
    override_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Writing the '{DEPLOYMENT_PROFILE_NAME}' override with baseline '{profile_name}' to '{override_path}'")
    writeYamlToFile(override_path, override, schema_name=RESOURCE_PROFILE_SCHEMA, schemas_dir=get_schema_dir())
    beautifyYaml(override_path)
    return override_path


def environment_override_keys(env_dir: Path) -> list[str]:
    keys = {"cloud"}
    keys |= {path.parent.name for path in get_namespaces_path(env_dir).glob("*/namespace.yml")}
    return sorted(keys)


def append_override_to_env_definition(env_dir: Path, override_name: str = DEPLOYMENT_PROFILE_NAME) -> list[str]:
    env_definition_path = Path(getEnvDefinitionPath(str(env_dir)))
    env_definition = readYaml(env_definition_path)
    profiles = env_definition.get("envTemplate", {}).get("envSpecificResourceProfiles") or {}
    appended = []
    for key in environment_override_keys(env_dir):
        current = profiles.get(key)
        names = [current] if isinstance(current, str) else list(current or [])
        if override_name in names:
            continue
        names.append(override_name)
        set_nested_yaml_attribute(env_definition, f"envTemplate.envSpecificResourceProfiles.{key}", names)
        appended.append(key)
    if not appended:
        logger.info(f"The override list of every namespace already holds '{override_name}'")
        return appended
    logger.info(f"'{override_name}' is appended last to the override list of: {', '.join(appended)}")
    writeYamlToFile(env_definition_path, env_definition)
    return appended


def apply_deployment_profile(env_dir: Path, profile_name: str) -> Path | None:
    override_path = write_deployment_profile_override(env_dir, profile_name)
    if override_path is None:
        return None
    append_override_to_env_definition(env_dir)
    return override_path
