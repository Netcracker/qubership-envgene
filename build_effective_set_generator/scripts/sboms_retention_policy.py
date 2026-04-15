from envgenehelper import getenv_with_error, get_envgene_config_yaml, logger, is_over_size_limit, deleteFileIfExists, \
    cleanup_dir_by_age, get_sboms_dir
from envgenehelper.constants import CI_JOB_ARTIFACT_MAX_SIZE_MB
from envgenehelper.models import SbomRetentionConfig


def sboms_retention_policy():
    work_dir = getenv_with_error('CI_PROJECT_DIR')
    sboms_dir = get_sboms_dir(work_dir)
    config = get_envgene_config_yaml().get("sbom_retention")

    if not config:
        disabled = True
    else:
        sbom_retention = SbomRetentionConfig.model_validate(config)
        disabled = not sbom_retention.enabled

    if disabled:
        logger.info("SBOMs retention policy is disabled")
        return

    if not sboms_dir.exists():
        logger.warning(f"There is no such directory: {sboms_dir}")
        return

    logger.info("SBOMs retention policy is enabled")

    if not is_over_size_limit(sboms_dir, CI_JOB_ARTIFACT_MAX_SIZE_MB):
        logger.info("Directory size below threshold, skipping cleanup")
        return

    logger.info("Directory size above threshold, starting cleanup")
    for sbom_path in sboms_dir.iterdir():
        if sbom_path.is_file():
            logger.info(f"Removing outdated format file: {sbom_path}")
            deleteFileIfExists(sbom_path)

    for app_sbom_dir in sboms_dir.iterdir():
        if app_sbom_dir.is_dir():
            cleanup_dir_by_age(app_sbom_dir, sbom_retention.keep_versions_per_app)


if __name__ == "__main__":
    sboms_retention_policy()
