import os

REPO_ROOT_PATHS = [
    "appdefs/",
    "regdefs/",
    "configuration/",
    "sboms/",
    "templates/",
]


def get_env_artifact_paths(cluster_name: str, env_name: str) -> list[str]:
    env_artifact_paths = [
        f'environments/{cluster_name}/{env_name}'
    ]
    shared_entity_paths = get_shared_entity_paths(cluster_name)
    env_artifact_paths.extend(shared_entity_paths)

    return env_artifact_paths


def get_shared_entity_paths(cluster_name: str) -> list[str]:
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


def get_sparse_checkout_paths(full_env_name: str) -> list[str]:
    if "/" not in full_env_name:
        raise ValueError(
            f"Invalid environment name '{full_env_name}'. "
            f"Expected format: <cluster>/<env>"
        )

    cluster_name, env_name = full_env_name.split("/", 1)
    paths = list(REPO_ROOT_PATHS)
    paths.extend(get_env_artifact_paths(cluster_name, env_name))

    if os.getenv("CRED_ROTATION_PAYLOAD"):
        paths.append(f"environments/{cluster_name}/")

    return paths
