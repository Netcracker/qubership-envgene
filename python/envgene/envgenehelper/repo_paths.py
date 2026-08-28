from typing import Optional

from envgenehelper import getenv_with_error, get_cluster_name_from_full_name, get_environment_name_from_full_name


REPO_ROOT_PATHS = [
    "appdefs/",
    "regdefs/",
    "configuration/",
    "sboms/",
    "templates/",
]

def get_job_paths(cluster_name: Optional[str] = None, env_name: Optional[str] = None,
                                include_full_cluster: bool = False) -> list[str]:
    if cluster_name is None or env_name is None:
        full_env_name = getenv_with_error("FULL_ENV_NAME")
        cluster_name = cluster_name or get_cluster_name_from_full_name(full_env_name)
        env_name = env_name or get_environment_name_from_full_name(full_env_name)

    paths = list(REPO_ROOT_PATHS)
    paths.extend(_get_env_artifact_paths(cluster_name, env_name))

    if include_full_cluster:
        paths.append(f"environments/{cluster_name}/")

    return paths


def _get_env_artifact_paths(cluster_name: str, env_name: str) -> list[str]:
    env_artifact_paths = [
        f'environments/{cluster_name}/{env_name}'
    ]
    shared_entity_paths = _get_shared_entity_paths(cluster_name)
    env_artifact_paths.extend(shared_entity_paths)

    return env_artifact_paths


def _get_shared_entity_paths(cluster_name: str) -> list[str]:
    env_artifact_subdirs = [
        "configuration",
        "configurations",
        "resource_profiles",
        "rp_override",
        "Profiles",
        "parameters",
        "cloud-passport",
        "cloud-passports",
        "credentials",
        "Credentials",
        "shared-credentials",
    ]

    cluster_only_subdirs = [
        "app-deployer",
        "cloud-deployer",
    ]

    paths = [f"environments/{d}" for d in env_artifact_subdirs]

    paths.extend(
        f"environments/{cluster_name}/{d}"
        for d in env_artifact_subdirs + cluster_only_subdirs
    )

    return paths
