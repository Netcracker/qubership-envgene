import os
import shlex
import sys
from os import getenv
from pathlib import Path

from envgenehelper.collections_helper import split_multi_value_param
from envgenehelper.models import PipelineType

RESOLVED_ENV_FILE = "envgene-resolved.env"


def resolve_env_names() -> list[str]:
    env_names = os.getenv("ENV_NAMES")
    cluster_name = os.getenv("CLUSTER_NAME")
    env_name = os.getenv("ENVIRONMENT_NAME")

    if env_names and (cluster_name or env_name):
        raise ValueError(
            "Set ENV_NAMES only, or both CLUSTER_NAME and ENVIRONMENT_NAME, "
            "but not both at the same time"
        )

    if env_names:
        names = split_multi_value_param(env_names)
    elif cluster_name and env_name:
        env_names = f"{cluster_name}/{env_name}"
        os.environ["ENV_NAMES"] = env_names
        names = [env_names]
    else:
        raise ValueError("Set ENV_NAMES or both CLUSTER_NAME and ENVIRONMENT_NAME")

    for name in names:
        if "/" not in name:
            raise ValueError(
                f"Invalid environment name '{name}'. "
                f"Expected format: <cluster>/<env>"
            )

    pipeline_type = getenv("PIPELINE_TYPE")
    if pipeline_type and PipelineType(pipeline_type) == PipelineType.GITLAB_DEPLOY and len(names) > 1:
        raise ValueError(
            "Multiple values in ENV_NAMES are not supported when PIPELINE_TYPE is GITLAB_DEPLOY"
        )

    return names


def main() -> int:
    try:
        env_names = resolve_env_names()
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1

    env_names_value = ",".join(env_names)
    Path(RESOLVED_ENV_FILE).write_text(
        f"ENV_NAMES={shlex.quote(env_names_value)}\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
