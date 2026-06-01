from enum import Enum
from os import getenv

from envgenehelper import get_envgene_config_yaml, calculate_merge_mode, MergeType, logger, get_sd_dir, SD_FILE_NAME


class ESGenerationContext(Enum):
    TOPOLOGY = "topology"
    PIPELINE = "pipeline"
    DEPLOYMENT = "deployment"
    RUNTIME = "runtime"
    CLEANUP = "cleanup"


ES_MAPPING_FILE = "mapping.yml"
ES_DIR_NAME = "effective-set"


class GenerationMode(Enum):
    FULL = "full"
    PARTIAL = "partial"
    NO_SD = "no_sd"


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


def resolve_es_generation_mode():
    merge_mode = calculate_merge_mode(getenv("SD_REPO_MERGE_MODE"), getenv("SD_DELTA"))

    sd_path = get_sd_dir().joinpath(SD_FILE_NAME)
    sd_input = bool(getenv("SD_DATA") or bool(getenv("SD_VERSION")))
    any_sd = sd_path.exists() and sd_input

    if not any_sd:
        logger.info(f"Resolved effective set generation mode: {GenerationMode.FULL} (no SD input found)")
        return GenerationMode.FULL

    strategy = get_envgene_config_yaml().get(
        "effective_set_generation_strategy",
        GenerationMode.PARTIAL,
    )

    if strategy == GenerationMode.PARTIAL and merge_mode.name != MergeType.REPLACE:
        logger.info(f"Resolved effective set generation mode: {GenerationMode.PARTIAL} (strategy={strategy},"
                    f" merge_mode={merge_mode.name})")
        return GenerationMode.PARTIAL

    logger.info(f"Resolved effective set generation mode: {GenerationMode.FULL} (strategy={strategy},"
                f" merge_mode={merge_mode.name})")
    return GenerationMode.FULL
