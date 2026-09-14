import os
import tempfile
from pathlib import Path

import envgenehelper as helper
from envgenehelper import getenv_with_error
from envgenehelper.logger import logger
from dpg.v1.utils.registry.registry import ArtifactoryUtils

_MAVEN_PROVIDER = "MAVEN_PROVIDER"
_PROVIDER_AWS = "aws"

_TRANSIENT_DIR = Path(tempfile.gettempdir()) / "envgene-regdefv2-adapter"
_TRANSIENT_PUBREG_PARAMS_FILE = _TRANSIENT_DIR / "pubreg_params.yaml"
REGDEFS_DIRNAME = "RegDefs"
REGDEF_V2_TMP_DIR = _TRANSIENT_DIR / REGDEFS_DIRNAME
PUBREG_CREDS_TMP_FILE = _TRANSIENT_DIR / "transient-creds.yml"

TRANSIENT_CRED_ID = "transient-pub-reg-creds"
_AUTH_CONFIG_KEY = "pub-reg-auth"


def _collect_pubreg_params() -> dict:
    params = {}
    for key, value in os.environ.items():
        if key.startswith(("PUB_REG_", "NON_PUB_REG_")) and value.strip():
            params[key] = value.strip()
    for key in (_MAVEN_PROVIDER, "HELM_REPO_BASE_URL"):
        value = os.getenv(key, "").strip()
        if value:
            params[key] = value
    return params


def _synthesize_v2_from_v1(v1_data: dict, aws_domain: str, aws_region: str, cred_id: str) -> dict:
    v1_maven = v1_data.get("mavenConfig", {})
    return {
        "version": "2.0",
        "name": v1_data["name"],
        "authConfig": {
            _AUTH_CONFIG_KEY: {
                "provider": "aws",
                "authMethod": "secret",
                "credentialsId": cred_id,
                "awsDomain": aws_domain,
                "awsRegion": aws_region,
            }
        },
        "mavenConfig": {
            "authConfig": _AUTH_CONFIG_KEY,
            **v1_maven,
        },
    }


def _build_transient_creds(cred_id: str, username: str, password: str) -> dict:
    return {
        cred_id: {
            "data": {
                "username": username,
                "password": password,
            }
        }
    }


def run_regdefv2_adapter(ctx) -> None:
    maven_provider = os.getenv(_MAVEN_PROVIDER, "").strip().lower()

    if not maven_provider:
        logger.info("regdefv2_adapter: MAVEN_PROVIDER not set — no-op")
        return

    _TRANSIENT_DIR.mkdir(parents=True, exist_ok=True)

    params = _collect_pubreg_params()
    helper.writeYamlToFile(_TRANSIENT_PUBREG_PARAMS_FILE, params)
    os.environ["LOCAL_PUBREG_FILE"] = str(_TRANSIENT_PUBREG_PARAMS_FILE)
    logger.info(f"regdefv2_adapter: pubreg params → {_TRANSIENT_PUBREG_PARAMS_FILE}")

    if maven_provider != _PROVIDER_AWS:
        logger.info(
            f"regdefv2_adapter: MAVEN_PROVIDER={maven_provider!r} — flat params written, no RegDef v2 synthesized"
        )
        return

    logger.info("regdefv2_adapter: MAVEN_PROVIDER=aws — synthesizing transient RegDef v2 from committed v1")

    access_key = getenv_with_error("PUB_REG_KEY")
    secret_key = getenv_with_error("PUB_REG_SECRET")
    aws_domain_override = os.getenv("PUB_REG_DOMAIN", "").strip()
    aws_region_override = os.getenv("PUB_REG_REGION", "").strip()

    source_regdefs_path = (
        ctx.work_dir / "environments" / ctx.cluster_name / ctx.env_name / "RegDefs"
    )
    if not source_regdefs_path.is_dir():
        raise ValueError(
            f"regdefv2_adapter: {source_regdefs_path} is not a directory; cannot synthesize RegDef v2"
        )

    REGDEF_V2_TMP_DIR.mkdir(parents=True, exist_ok=True)
    for regdef_file in source_regdefs_path.iterdir():
        if regdef_file.suffix not in ('.yml', '.yaml'):
            continue
        v1_data = helper.openYaml(regdef_file)
        if v1_data.get("version") == "2.0" or "authConfig" in v1_data:
            helper.writeYamlToFile(REGDEF_V2_TMP_DIR / regdef_file.name, v1_data)
            logger.info(f"regdefv2_adapter: {regdef_file.name} already v2 — copied as-is")
            continue

        reg_url = v1_data.get("mavenConfig", {}).get("repositoryDomainName", "")
        aws_domain = aws_domain_override or ArtifactoryUtils.extract_aws_domain(reg_url)
        if not aws_domain:
            raise ValueError(
                f"regdefv2_adapter: Cannot determine AWS CodeArtifact domain for {regdef_file.name} — "
                "set PUB_REG_DOMAIN or ensure mavenConfig.repositoryDomainName contains a CodeArtifact URL"
            )
        aws_region = aws_region_override or ArtifactoryUtils.extract_aws_region(reg_url)
        if not aws_region:
            raise ValueError(
                f"regdefv2_adapter: Cannot determine AWS region for {regdef_file.name} — "
                "set PUB_REG_REGION or ensure mavenConfig.repositoryDomainName contains a CodeArtifact URL"
            )

        v2_data = _synthesize_v2_from_v1(v1_data, aws_domain, aws_region, TRANSIENT_CRED_ID)
        helper.writeYamlToFile(REGDEF_V2_TMP_DIR / regdef_file.name, v2_data)
        logger.info(f"regdefv2_adapter: synthesized v2 for {regdef_file.name}")

    creds = _build_transient_creds(TRANSIENT_CRED_ID, access_key, secret_key)
    helper.writeYamlToFile(PUBREG_CREDS_TMP_FILE, creds)
    ctx.regdef_v2_dir = REGDEF_V2_TMP_DIR
    ctx.pubreg_creds_file = PUBREG_CREDS_TMP_FILE
    logger.info(f"regdefv2_adapter: transient dir → {_TRANSIENT_DIR}")
