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
