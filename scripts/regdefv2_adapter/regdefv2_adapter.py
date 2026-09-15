import os
import tempfile
from pathlib import Path

import jsonschema

import envgenehelper as helper
from envgenehelper.business_helper import get_current_env_dir_from_env_vars
from envgenehelper.config_helper import get_regdef_v2_schema
from envgenehelper.logger import logger
from dpg.v1.utils.registry.registry import ArtifactoryUtils

from build_env.render_config_env import EnvGenerator, build_minimal_render_context

MAVEN_PROVIDER = "MAVEN_PROVIDER"
PROVIDER_AWS = "aws"
PUBLIC_CLOUD_PROVIDERS = ("aws", "gcp", "azure")

TRANSIENT_DIR = Path(tempfile.gettempdir()) / "envgene-regdefv2-adapter"
TRANSIENT_PUBREG_PARAMS_FILE = TRANSIENT_DIR / "pubreg_params.yaml"
REGDEFS_DIRNAME = "RegDefs"
REGDEF_V2_TMP_DIR = TRANSIENT_DIR / REGDEFS_DIRNAME
PUBREG_CREDS_TMP_FILE = TRANSIENT_DIR / "transient-creds.yml"

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
    if not params.get("PUB_REG_PROVIDER"):
        raise ValueError("PUB_REG_PROVIDER is required in Cloud e2eParameters for public cloud MAVEN_PROVIDER")
    if not auth_method:
        raise ValueError("PUB_REG_METHOD is required in Cloud e2eParameters for public cloud MAVEN_PROVIDER")


def _build_auth_config(params: dict, cred_id: str) -> dict:
    auth_method = params.get("PUB_REG_METHOD", "")
    auth_config = {
        "provider": params.get("PUB_REG_PROVIDER", ""),
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




def run_regdefv2_adapter(ctx) -> None:
    env_dir = str(get_current_env_dir_from_env_vars())
    render_context_vars = build_minimal_render_context(ctx.env_name, ctx.cluster_name, env_dir, str(ctx.work_dir))
    e2e_parameters = EnvGenerator().render_cloud_e2e_parameters(
        ctx.env_name, render_context_vars, env_dir, TRANSIENT_DIR / "parameters"
    )
    params = _resolve_pubreg_params(e2e_parameters)

    maven_provider = params.get(MAVEN_PROVIDER, "").strip().lower()

    if not maven_provider:
        logger.info("MAVEN_PROVIDER not set in Cloud e2eParameters — skipping registry auth setup")
        return

    TRANSIENT_DIR.mkdir(parents=True, exist_ok=True)

    helper.writeYamlToFile(TRANSIENT_PUBREG_PARAMS_FILE, params)
    os.environ["LOCAL_PUBREG_FILE"] = str(TRANSIENT_PUBREG_PARAMS_FILE)
    logger.info(f"Registry auth parameters written to {TRANSIENT_PUBREG_PARAMS_FILE}")

    if maven_provider not in PUBLIC_CLOUD_PROVIDERS:
        logger.info(f"MAVEN_PROVIDER={maven_provider!r} — registry auth parameters written, no RegDef v2 synthesized")
        return

    logger.info(f"MAVEN_PROVIDER={maven_provider!r} — synthesizing transient RegDef v2 from committed v1")

    auth_method = params.get("PUB_REG_METHOD", "")
    access_key = params.get("PUB_REG_KEY")
    secret_key = params.get("PUB_REG_SECRET")
    _validate_required_pubreg_params(params, auth_method)

    source_regdefs_path = ctx.committed_regdefs_dir
    if not source_regdefs_path.is_dir():
        raise ValueError(f"{source_regdefs_path} does not exist; cannot synthesize RegDef v2")

    REGDEF_V2_TMP_DIR.mkdir(parents=True, exist_ok=True)
    for regdef_file_path in helper.findAllYamlsInDir(source_regdefs_path, recursively=False):
        regdef_file = Path(regdef_file_path)
        v1_data = helper.openYaml(regdef_file)

        if v1_data.get("version") == "2.0" or "authConfig" in v1_data:
            helper.writeYamlToFile(REGDEF_V2_TMP_DIR / regdef_file.name, v1_data)
            logger.info(f"{regdef_file.name} already v2 — copied as-is")
            continue

        file_auth_config = _build_auth_config(params, TRANSIENT_CRED_ID)
        if maven_provider == PROVIDER_AWS:
            reg_url = v1_data.get("mavenConfig", {}).get("repositoryDomainName", "")
            if "awsDomain" not in file_auth_config:
                aws_domain = ArtifactoryUtils.extract_aws_domain(reg_url)
                if aws_domain:
                    file_auth_config["awsDomain"] = aws_domain
            if "awsRegion" not in file_auth_config:
                aws_region = ArtifactoryUtils.extract_aws_region(reg_url)
                if aws_region:
                    file_auth_config["awsRegion"] = aws_region

        v2_data = _convert_v2_from_v1(v1_data, file_auth_config)
        jsonschema.validate(instance=v2_data, schema=get_regdef_v2_schema())
        helper.writeYamlToFile(REGDEF_V2_TMP_DIR / regdef_file.name, v2_data)
        logger.info(f"Synthesized v2 for {regdef_file.name}")

    creds = {TRANSIENT_CRED_ID: {"data": {"username": access_key, "password": secret_key}}}
    helper.writeYamlToFile(PUBREG_CREDS_TMP_FILE, creds)
    ctx.transient_regdefs_dir = REGDEF_V2_TMP_DIR
    logger.info(f"Transient public registry auth directory: {TRANSIENT_DIR}")
