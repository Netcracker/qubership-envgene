from .git_helper import GitRepoManager


class TestGetSparseCheckoutPaths:
    def test_full_path_list(self):
        paths = GitRepoManager.get_sparse_checkout_paths("my-cluster", "my-env")
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

    def test_cred_rotation_adds_full_cluster_dir(self):
        paths = GitRepoManager.get_sparse_checkout_paths("my-cluster", "my-env", include_full_cluster=True)
        assert "environments/my-cluster/" in paths
