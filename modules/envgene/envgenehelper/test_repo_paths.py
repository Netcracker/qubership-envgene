from unittest.mock import patch

import pytest

from .repo_paths import (
    REPO_ROOT_PATHS,
    get_env_artifact_paths,
    get_shared_entity_paths,
    get_sparse_checkout_paths,
)

CLUSTER = "my-cluster"
ENV = "my-env"
FULL_ENV_NAME = f"{CLUSTER}/{ENV}"

EXPECTED_SHARED_ENTITY_PATHS = [
    # site-level shared
    "environments/configuration",
    "environments/configurations",
    "environments/resource_profiles",
    "environments/rp_override",
    "environments/Profiles",
    "environments/parameters",
    "environments/cloud-passport",
    "environments/cloud-passports",
    "environments/credentials",
    "environments/Credentials",
    "environments/shared-credentials",
    # cluster-level shared
    f"environments/{CLUSTER}/configuration",
    f"environments/{CLUSTER}/configurations",
    f"environments/{CLUSTER}/resource_profiles",
    f"environments/{CLUSTER}/rp_override",
    f"environments/{CLUSTER}/Profiles",
    f"environments/{CLUSTER}/parameters",
    f"environments/{CLUSTER}/cloud-passport",
    f"environments/{CLUSTER}/cloud-passports",
    f"environments/{CLUSTER}/credentials",
    f"environments/{CLUSTER}/Credentials",
    f"environments/{CLUSTER}/shared-credentials",
    f"environments/{CLUSTER}/app-deployer",
    f"environments/{CLUSTER}/cloud-deployer",
]

EXPECTED_SPARSE_CHECKOUT_PATHS = [
    *REPO_ROOT_PATHS,
    f"environments/{CLUSTER}/{ENV}",
    *EXPECTED_SHARED_ENTITY_PATHS,
]


class TestGetSharedEntityPaths:
    def test_returns_site_and_cluster_paths(self):
        assert get_shared_entity_paths(CLUSTER) == EXPECTED_SHARED_ENTITY_PATHS


class TestGetEnvArtifactPaths:
    def test_includes_env_dir_and_shared_paths(self):
        assert get_env_artifact_paths(CLUSTER, ENV) == [
            f"environments/{CLUSTER}/{ENV}",
            *EXPECTED_SHARED_ENTITY_PATHS,
        ]


class TestGetSparseCheckoutPaths:
    def test_full_path_list(self):
        assert get_sparse_checkout_paths(FULL_ENV_NAME) == EXPECTED_SPARSE_CHECKOUT_PATHS

    def test_cred_rotation_adds_full_cluster_dir(self):
        with patch.dict("os.environ", {"CRED_ROTATION_PAYLOAD": "payload"}, clear=False):
            paths = get_sparse_checkout_paths(FULL_ENV_NAME)
        assert paths == [*EXPECTED_SPARSE_CHECKOUT_PATHS, f"environments/{CLUSTER}/"]

    def test_invalid_env_name_raises(self):
        with pytest.raises(ValueError, match="Invalid environment name"):
            get_sparse_checkout_paths("no-slash")
