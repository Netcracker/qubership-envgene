# envgenehelper/constants.py
from enum import Enum

cleanup_targets = [
    "Applications",
    "Namespaces",
    "Profiles",
    "cloud.yml",
    "tenant.yml",
    "bg_domain.yml",
    "composite_structure.yml",
]

CI_JOB_ARTIFACT_MAX_SIZE_MB = 1200  # 80% from limit 1.5


class ESGenerationContext(Enum):
    TOPOLOGY = "topology"
    PIPELINE = "pipeline"
    DEPLOYMENT = "deployment"
    RUNTIME = "runtime"
    CLEANUP = "cleanup"


ES_MAPPING_FILE = "mapping.yaml"
