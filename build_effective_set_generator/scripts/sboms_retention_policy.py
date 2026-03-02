from envgenehelper import getenv_with_error, get_envgene_config_yaml, logger, cleanup_dir_by_size, deleteFileIfExists, \
    cleanup_dir_by_age, get_sboms_dir
from envgenehelper.constants import CI_JOB_ARTIFACT_MAX_SIZE_MB
from envgenehelper.models import SbomRetentionConfig


def sboms_retention_policy():
    work_dir = getenv_with_error('CI_PROJECT_DIR')
    sboms_dir = get_sboms_dir(work_dir)
    config = get_envgene_config_yaml()
    sbom_retention = SbomRetentionConfig.model_validate(config.get("sbom_retention", {}))

    if not sbom_retention.enabled:
        logger.info("SBOMs retention policy is disabled")
        return

    if not sboms_dir.exists():
        logger.warning(f"There is no such directory: {sboms_dir}")
        return

    logger.info("SBOMs retention policy is enabled")
    for sbom_path in sboms_dir.iterdir():
        logger.info(f"Removing file: {sbom_path}")
        deleteFileIfExists(sbom_path)

    for app_sbom_dir in sboms_dir.iterdir():
        cleanup_dir_by_age(app_sbom_dir, sbom_retention.keep_versions_per_app)

    cleanup_dir_by_size(sboms_dir, CI_JOB_ARTIFACT_MAX_SIZE_MB)


if __name__ == "__main__":
    sboms_retention_policy()
