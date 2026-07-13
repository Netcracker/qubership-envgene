from enum import Enum
from os import getenv

from envgenehelper import get_envgene_config_yaml, calculate_merge_mode, MergeType, logger, get_sd_dir, SD_FILE_NAME, \
    get_sd_dir_by_env_cluster_name, getenv_with_error


class ESGenerationContext(Enum):
    TOPOLOGY = "topology"
    PIPELINE = "pipeline"
    DEPLOYMENT = "deployment"
    RUNTIME = "runtime"
    CLEANUP = "cleanup"


ES_MAPPING_FILE = "mapping.yaml"
ES_DIR_NAME = "effective-set"


class GenerationMode(Enum):
    FULL = "full"
    PARTIAL = "partial"


class PartialMergeMode(Enum):
    FORWARD = "forward"
    REVERSE = "reverse"


def resolve_partial_merge_mode():
    merge_mode = calculate_merge_mode(getenv("SD_REPO_MERGE_MODE"), getenv("SD_DELTA"))

    if merge_mode == MergeType.BASIC_EXCLUSION:
        return PartialMergeMode.REVERSE

    if merge_mode in {MergeType.BASIC, MergeType.EXTENDED}:
        return PartialMergeMode.FORWARD

    raise ValueError(f"Unsupported merge mode for partial: {merge_mode}")


def resolve_es_generation_mode(cluster_name, env_name):
    merge_mode = calculate_merge_mode(getenv("SD_REPO_MERGE_MODE"), getenv("SD_DELTA"))

    sd_path = get_sd_dir_by_env_cluster_name(cluster_name, env_name) / SD_FILE_NAME
    sd_input = bool(getenv("SD_DATA") or bool(getenv("SD_VERSION")))
    any_sd = sd_path.exists() and sd_input

    if not any_sd:
        logger.info(f"Resolved effective set generation mode: {GenerationMode.FULL}. "
                    f"No SD input was provided or SD file does not exist (sd_input={sd_input}, sd_path={sd_path})")
        return GenerationMode.FULL

    strategy = GenerationMode(
        get_envgene_config_yaml().get(
            "effective_set_generation_strategy",
            GenerationMode.PARTIAL.value,
        )
    )

    if strategy == GenerationMode.PARTIAL and merge_mode != MergeType.REPLACE:
        logger.info(f"Resolved effective set generation mode: {GenerationMode.PARTIAL} (strategy={strategy},"
                    f" merge_mode={merge_mode})")
        return GenerationMode.PARTIAL

    logger.info(f"Resolved effective set generation mode: {GenerationMode.FULL} (strategy={strategy},"
                f" merge_mode={merge_mode})")
    return GenerationMode.FULL


def get_es_generation_mode():
    es_generation_mode = getenv("ES_GENERATION_MODE")
    if not es_generation_mode:
        cluster_name = getenv_with_error("CLUSTER_NAME")
        env_name = getenv_with_error("ENVIRONMENT_NAME")
        es_generation_mode = resolve_es_generation_mode(cluster_name, env_name)
    else:
        es_generation_mode = GenerationMode(es_generation_mode)
    logger.info(f"ES_GENERATION_MODE: {es_generation_mode}")
    return es_generation_mode
