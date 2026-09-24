import os
from pathlib import Path

import jsonschema
from artifact_searcher.auth_resolver import (
    AUTH_METHOD_ANONYMOUS, AUTH_METHOD_SECRET, AUTH_METHOD_SERVICE_ACCOUNT, CRED_FIELD_DATA, CRED_FIELD_PASSWORD, CRED_FIELD_SECRET, CRED_FIELD_USERNAME,
)

import envgenehelper as helper
from envgenehelper.business_helper import get_current_env_dir_from_env_vars
from envgenehelper.config_helper import get_regdef_v2_schema
from envgenehelper.logger import logger

from build_env.render_config_env import EnvGenerator, build_minimal_render_context

MAVEN_PROVIDER = "MAVEN_PROVIDER"
PUBLIC_CLOUD_PROVIDERS = ("aws", "gcp")

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

_PUBREG_PROVIDER_AUTH_FIELDS: dict[str, dict[str, str]] = {
    "aws": {
        "PUB_REG_REGION": "awsRegion",
        "PUB_REG_DOMAIN": "awsDomain",
    },
    "gcp": {
        "PUB_REG_PROJECT": "gcpRegProject",
        "PUB_REG_SA_EMAIL": "gcpRegSAEmail",
    },
}


def _resolve_pubreg_params(e2e_parameters: dict, env_dir: str) -> dict:
    env_creds = helper.decrypt_file(helper.getEnvCredentialsPath(env_dir), in_place=False, allow_default=True)
    params = {}
    for key, value in e2e_parameters.items():
        is_registry_auth_param = key.startswith(REGISTRY_AUTH_PARAM_PREFIXES) or key in REGISTRY_AUTH_PARAM_NAMES
        if not isinstance(value, str) or not is_registry_auth_param:
            continue
        resolved = helper.expand_cred_macro_and_return_value(key, value, env_creds).strip()
        if resolved:
            params[key] = resolved
    return params


def _require_pubreg_param(params: dict, param_name: str, maven_provider: str, auth_method: str) -> None:
    if not params.get(param_name):
        raise ValueError(f"{param_name} is required in Cloud e2eParameters "
                         f"for MAVEN_PROVIDER={maven_provider} and PUB_REG_METHOD={auth_method}")


def _validate_required_pubreg_params(params: dict, maven_provider: str, auth_method: str) -> None:
    if not auth_method:
        raise ValueError("PUB_REG_METHOD is required in Cloud e2eParameters for public cloud MAVEN_PROVIDER")

    if auth_method == AUTH_METHOD_ANONYMOUS:
        return

    if maven_provider == "aws" and auth_method == AUTH_METHOD_SECRET:
        _require_pubreg_param(params, "PUB_REG_KEY", maven_provider, auth_method)
        _require_pubreg_param(params, "PUB_REG_SECRET", maven_provider, auth_method)
        _require_pubreg_param(params, "PUB_REG_REGION", maven_provider, auth_method)
        _require_pubreg_param(params, "PUB_REG_DOMAIN", maven_provider, auth_method)
        _require_pubreg_param(params, "PUB_REG_REPOSITORY", maven_provider, auth_method)
        return

    if maven_provider == "gcp" and auth_method == AUTH_METHOD_SERVICE_ACCOUNT:
        _require_pubreg_param(params, "PUB_REG_SECRET", maven_provider, auth_method)


def _build_auth_config(params: dict, cred_id: str, maven_provider: str) -> dict:
    auth_method = params.get("PUB_REG_METHOD", "")
    auth_config = {
        "provider": maven_provider,
        "authMethod": auth_method,
    }
    if auth_method != AUTH_METHOD_ANONYMOUS:
        auth_config["authType"] = "longLived" if auth_method == AUTH_METHOD_SECRET else "shortLived"
        auth_config["credentialsId"] = cred_id
    for param_key, auth_key in _PUBREG_PROVIDER_AUTH_FIELDS.get(maven_provider, {}).items():
        value = params.get(param_key, "").strip()
        if value:
            auth_config[auth_key] = value
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
        ctx.env_name, render_context_vars, env_dir, helper.pubreg_transient_dir(ctx.work_dir) / "parameters"
    )
    params = _resolve_pubreg_params(e2e_parameters, env_dir)

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
    logger.debug(f"pubreg_params content: {helper.mask_sensitive(params, keys_to_mask=(helper.CRED_VALUE_TYPE_SECRET, helper.CRED_VALUE_TYPE_PASSWORD, helper.CRED_VALUE_TYPE_USERNAME, 'key'))}")

    if maven_provider not in PUBLIC_CLOUD_PROVIDERS:
        return

    logger.info(f"MAVEN_PROVIDER={maven_provider!r} — synthesizing transient RegDef v2 from committed v1")

    auth_method = params.get("PUB_REG_METHOD", "")
    access_key = params.get("PUB_REG_KEY")
    secret_key = params.get("PUB_REG_SECRET")
    _validate_required_pubreg_params(params, maven_provider, auth_method)

    source_regdefs_path = ctx.committed_regdefs_dir
    if not source_regdefs_path.is_dir():
        raise ValueError(f"{source_regdefs_path} does not exist; cannot synthesize RegDef v2")
    template_regdefs_dir = Path(render_context_vars["render_dir"]) / REGDEFS_DIRNAME

    regdef_v2_tmp_dir.mkdir(parents=True, exist_ok=True)
    for template_regdef_file_path in helper.findAllYamlsInDir(template_regdefs_dir, recursively=False):
        regdef_file = source_regdefs_path / Path(template_regdef_file_path).name
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

    if auth_method != AUTH_METHOD_ANONYMOUS:
        if auth_method == AUTH_METHOD_SERVICE_ACCOUNT:
            cred_data = {CRED_FIELD_SECRET: secret_key}
        else:
            cred_data = {CRED_FIELD_USERNAME: access_key, CRED_FIELD_PASSWORD: secret_key}
        creds = {TRANSIENT_CRED_ID: {CRED_FIELD_DATA: cred_data}}
        helper.register_extra_creds(creds)
        logger.info(f"Registered transient credential {TRANSIENT_CRED_ID!r}")
        logger.debug(f"transient creds content: {helper.mask_sensitive(creds)}")
    ctx.transient_regdefs_dir = regdef_v2_tmp_dir
    logger.info(f"Transient public registry auth directory: {run_transient_dir}")
