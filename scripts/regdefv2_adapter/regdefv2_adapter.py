import os
from pathlib import Path

import jsonschema

import envgenehelper as helper
from envgenehelper.business_helper import get_current_env_dir_from_env_vars, get_template_dirs, NamespaceRole
from envgenehelper.config_helper import get_regdef_v2_schema
from envgenehelper.logger import logger

from build_env.render_config_env import EnvGenerator, build_minimal_render_context

MAVEN_PROVIDER = "MAVEN_PROVIDER"
PUBLIC_CLOUD_PROVIDERS = ("aws", "gcp", "azure")

REGDEFS_DIRNAME = "RegDefs"

TRANSIENT_CRED_ID = "transient-pub-reg-creds"
AUTH_CONFIG_KEY = "pub-reg-auth"

REGISTRY_AUTH_PARAM_PREFIXES = ("PUB_REG_", "NON_PUB_REG_")
REGISTRY_AUTH_PARAM_NAMES = (MAVEN_PROVIDER, "HELM_REPO_BASE_URL")

V2_MAVEN_CONFIG_FIELDS = (
    "repositoryDomainName",
    "targetSnapshot",
    "targetStaging",
    "targetRelease",
    "snapshotGroup",
    "releaseGroup",
)

PUB_REG_TO_AUTH_CONFIG_FIELD = {
    "PUB_REG_REGION": "awsRegion",
    "PUB_REG_DOMAIN": "awsDomain",
    "PUB_REG_ROLE_ARN": "awsRoleARN",
    "PUB_REG_ROLE_SESSION_PREFIX": "awsRoleSessionPrefix",

    "PUB_REG_PROJECT": "gcpRegProject",
    "PUB_REG_POOL_ID": "gcpRegPoolId",
    "PUB_REG_PROVIDER_ID": "gcpRegProviderId",
    "PUB_REG_SA_EMAIL": "gcpRegSAEmail",

    "PUB_REG_TENANT_ID": "azureTenantId",
    "PUB_REG_ACR_RESOURCE": "azureACRResource",
    "PUB_REG_ACR_NAME": "azureACRName",
}


def _resolve_pubreg_params(e2e_parameters: dict) -> dict:
    env_creds = helper.get_cred_config()
    params = {}
    for key, value in e2e_parameters.items():
        is_registry_auth_param = key.startswith(REGISTRY_AUTH_PARAM_PREFIXES) or key in REGISTRY_AUTH_PARAM_NAMES
        if not isinstance(value, str) or not is_registry_auth_param:
            continue
        resolved = helper.expand_cred_macro_and_return_value(key, value, env_creds).strip()
        if resolved:
            params[key] = resolved
    return params


def _validate_required_pubreg_params(params: dict, auth_method: str) -> None:
    if auth_method != "anonymous":
        if not params.get("PUB_REG_KEY"):
            raise ValueError("PUB_REG_KEY is required in Cloud e2eParameters unless PUB_REG_METHOD=anonymous")
        if not params.get("PUB_REG_SECRET"):
            raise ValueError("PUB_REG_SECRET is required in Cloud e2eParameters unless PUB_REG_METHOD=anonymous")
    if not auth_method:
        raise ValueError("PUB_REG_METHOD is required in Cloud e2eParameters for public cloud MAVEN_PROVIDER")


def _build_auth_config(params: dict, cred_id: str, maven_provider: str) -> dict:
    auth_method = params.get("PUB_REG_METHOD", "")
    auth_config = {
        "provider": maven_provider,
        "authMethod": auth_method,
        "authType": "longLived" if auth_method == "secret" else "shortLived",
        "credentialsId": cred_id,
    }
    for param_key, auth_key in PUB_REG_TO_AUTH_CONFIG_FIELD.items():
        value = params.get(param_key, "").strip()
        if value:
            auth_config[auth_key] = value
    oidc_url = params.get("PUB_REG_OIDC_URL", "").strip()
    if oidc_url:
        auth_config["gcpOIDC"] = {"URL": oidc_url}
    return auth_config


def _convert_v2_from_v1(v1_data: dict, auth_config: dict) -> dict:
    v1_maven = v1_data.get("mavenConfig", {})
    v2_maven = {key: v1_maven[key] for key in V2_MAVEN_CONFIG_FIELDS if key in v1_maven}
    v2_maven["authConfig"] = AUTH_CONFIG_KEY
    return {
        "version": "2.0",
        "name": v1_data["name"],
        "authConfig": {AUTH_CONFIG_KEY: auth_config},
        "mavenConfig": v2_maven,
    }




def _get_cloud_e2e_parameters(ctx, env_dir: str) -> dict:
    templates_dir = get_template_dirs().get(NamespaceRole.COMMON)
    if templates_dir and Path(templates_dir).is_dir():
        render_context_vars = build_minimal_render_context(ctx.env_name, ctx.cluster_name, env_dir, str(ctx.work_dir))
        return EnvGenerator().render_cloud_e2e_parameters(
            ctx.env_name, render_context_vars, env_dir, helper.pubreg_transient_dir(ctx.work_dir) / "parameters"
        )

    # no template repo fetched this run (appregdef_render didn't run) - nothing to render from, read the committed cloud.yml
    cloud_file = Path(env_dir) / "cloud.yml"
    if not cloud_file.is_file():
        logger.info(f"{cloud_file} is not found - no Cloud e2eParameters to read")
        return {}
    return helper.openYaml(cloud_file).get("e2eParameters", {}) or {}


def run_regdefv2_adapter(ctx) -> None:
    env_dir = str(get_current_env_dir_from_env_vars())
    params = _resolve_pubreg_params(_get_cloud_e2e_parameters(ctx, env_dir))

    maven_provider = params.get(MAVEN_PROVIDER, "").strip().lower()

    if not maven_provider:
        logger.info("MAVEN_PROVIDER not set in Cloud e2eParameters — skipping registry auth setup")
        return

    run_transient_dir = helper.pubreg_transient_dir(ctx.work_dir)
    run_transient_dir.mkdir(parents=True, exist_ok=True)
    transient_pubreg_params_file = run_transient_dir / helper.PUBREG_PARAMS_FILENAME
    regdef_v2_tmp_dir = run_transient_dir / REGDEFS_DIRNAME

    helper.writeYamlToFile(transient_pubreg_params_file, params)
    os.environ["LOCAL_PUBREG_FILE"] = str(transient_pubreg_params_file)
    logger.info(f"Registry auth parameters written to {transient_pubreg_params_file}")
    logger.info(f"DEBUG pubreg_params content: {params}")

    if maven_provider not in PUBLIC_CLOUD_PROVIDERS:
        return

    logger.info(f"MAVEN_PROVIDER={maven_provider!r} — synthesizing transient RegDef v2 from committed v1")

    auth_method = params.get("PUB_REG_METHOD", "")
    access_key = params.get("PUB_REG_KEY")
    secret_key = params.get("PUB_REG_SECRET")
    _validate_required_pubreg_params(params, auth_method)

    source_regdefs_path = ctx.committed_regdefs_dir
    if not source_regdefs_path.is_dir():
        raise ValueError(f"{source_regdefs_path} does not exist; cannot synthesize RegDef v2")

    regdef_v2_tmp_dir.mkdir(parents=True, exist_ok=True)
    for regdef_file_path in helper.findAllYamlsInDir(source_regdefs_path, recursively=False):
        regdef_file = Path(regdef_file_path)
        v1_data = helper.openYaml(regdef_file)

        if v1_data.get("version") == "2.0" or "authConfig" in v1_data:
            helper.writeYamlToFile(regdef_v2_tmp_dir / regdef_file.name, v1_data)
            logger.warning(f"{regdef_file.name}  already v2 — copied as-is. "
                           f"Deriving registry auth from registry v2 auth parameters is not  primary flow")
            continue

        file_auth_config = _build_auth_config(params, TRANSIENT_CRED_ID, maven_provider)

        v2_data = _convert_v2_from_v1(v1_data, file_auth_config)
        jsonschema.validate(instance=v2_data, schema=get_regdef_v2_schema())
        helper.writeYamlToFile(regdef_v2_tmp_dir / regdef_file.name, v2_data)
        logger.info(f"Synthesized v2 for {regdef_file.name}")

    creds = {TRANSIENT_CRED_ID: {"data": {"username": access_key, "password": secret_key}}}
    helper.register_extra_creds(creds)
    logger.info(f"Registered transient credential {TRANSIENT_CRED_ID!r}")
    logger.info(f"DEBUG transient creds content: {creds}")
    ctx.transient_regdefs_dir = regdef_v2_tmp_dir
    logger.info(f"Transient public registry auth directory: {run_transient_dir}")
