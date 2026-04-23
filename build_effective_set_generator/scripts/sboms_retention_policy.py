from envgenehelper import getenv_with_error, get_envgene_config_yaml, logger, deleteFileIfExists, \
    cleanup_dir_by_age, get_sboms_dir, is_over_size_limit
from envgenehelper.constants import CI_JOB_ARTIFACT_MAX_SIZE_MB
from envgenehelper.models import SbomRetentionConfig


def sboms_retention_policy():
    work_dir = getenv_with_error('CI_PROJECT_DIR')
    sboms_dir = get_sboms_dir(work_dir)

    if not sboms_dir.exists():
        logger.warning(f"SBOM directory does not exist: {sboms_dir}")
        return

    config = get_envgene_config_yaml().get("sbom_retention")
    if not config:
        disabled = True
    else:
        sbom_retention = SbomRetentionConfig.model_validate(config)
        disabled = not sbom_retention.enabled

    if disabled:
        logger.info("SBOM retention policy is disabled")
        return

    logger.info(f"SBOM retention policy is enabled for directory {sboms_dir}")

    for sbom_path in sboms_dir.iterdir():
        if sbom_path.is_file():
            logger.info(f"Removing legacy SBOM file: {sbom_path}")
            deleteFileIfExists(sbom_path)

    keep_versions_per_app = sbom_retention.keep_versions_per_app
    if keep_versions_per_app:
        logger.info(f"SBOM retention policy keep_versions_per_app={keep_versions_per_app},"
                    f" starting cleanup: {sboms_dir}")
        for app_sbom_dir in sboms_dir.iterdir():
            cleanup_dir_by_age(app_sbom_dir, sbom_retention.keep_versions_per_app)

    if is_over_size_limit(sboms_dir, CI_JOB_ARTIFACT_MAX_SIZE_MB):
        logger.info(f"SBOM directory exceeds size limit, starting cleanup: {sboms_dir}")
        for app_sbom_dir in sboms_dir.iterdir():
            cleanup_dir_by_age(app_sbom_dir, 1)


if __name__ == "__main__":
    sboms_retention_policy()
