from enum import Enum
from os import getenv

from envgenehelper import get_envgene_config_yaml, calculate_merge_mode, MergeType


class ESGenerationContext(Enum):
    TOPOLOGY = "topology"
    PIPELINE = "pipeline"
    DEPLOYMENT = "deployment"
    RUNTIME = "runtime"
    CLEANUP = "cleanup"


ES_MAPPING_FILE = "mapping.yaml"


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

    if get_envgene_config_yaml().get("partial_effective_set_generation") and merge_mode.name != MergeType.REPLACE:
        return GenerationMode.PARTIAL

    return GenerationMode.FULL
