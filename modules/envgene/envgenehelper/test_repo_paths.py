import os

import pytest

from envgenehelper.repo_paths import get_sparse_checkout_paths


class TestGetSparseCheckoutPaths:
    def test_full_path_list(self):
        paths = get_sparse_checkout_paths("my-cluster/my-env")
        assert paths == [
            # repo root
            "appdefs/",
            "regdefs/",
            "configuration/",
            "sboms/",
            "templates/",
            # target env
            "environments/my-cluster/my-env",
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
            "environments/my-cluster/configuration",
            "environments/my-cluster/configurations",
            "environments/my-cluster/resource_profiles",
            "environments/my-cluster/rp_override",
            "environments/my-cluster/Profiles",
            "environments/my-cluster/parameters",
            "environments/my-cluster/cloud-passport",
            "environments/my-cluster/cloud-passports",
            "environments/my-cluster/credentials",
            "environments/my-cluster/Credentials",
            "environments/my-cluster/shared-credentials",
            "environments/my-cluster/app-deployer",
            "environments/my-cluster/cloud-deployer",
        ]

    def test_cred_rotation_adds_full_cluster_dir(self, monkeypatch):
        monkeypatch.setenv("CRED_ROTATION_PAYLOAD", '{"rotation_items": []}')
        paths = get_sparse_checkout_paths("my-cluster/my-env")
        assert "environments/my-cluster/" in paths

    def test_rejects_invalid_full_env_name(self):
        with pytest.raises(ValueError, match="Invalid environment name"):
            get_sparse_checkout_paths("my-cluster-my-env")
