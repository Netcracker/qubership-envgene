import pytest

from build_env.appregdef_render import override_app_reg_defs

APPDEF_CONTENT = """name: application-1
registryName: registry-1
artifactId: application-1
groupId: org.qubership
supportParallelDeploy: true
deployParameters: {}
technicalConfigurationParameters: {}
"""

REGDEF_CONTENT = """name: registry-1
credentialsId: registry-cred
mavenConfig:
  repositoryDomainName: maven.qubership.org
  fullRepositoryUrl: https://maven.qubership.org/repository
  targetSnapshot: snapshot
  targetStaging: staging
  targetRelease: release
  releaseGroup: ""
  snapshotGroup: ""
dockerConfig:
  snapshotUri: docker.qubership.org/snapshot
  stagingUri: docker.qubership.org/staging
  releaseUri: docker.qubership.org/release
  groupUri: docker.qubership.org/group
  snapshotRepoName: docker-snapshot
  stagingRepoName: docker-staging
  releaseRepoName: docker-release
  groupName: docker-group
"""

CONTENT_BY_DIR = {"AppDefs": APPDEF_CONTENT, "RegDefs": REGDEF_CONTENT}


class TestOverrideAppRegDefs:

    @pytest.fixture(autouse=True)
    def setup_dirs(self, tmp_path):
        self.base_dir = tmp_path / "base"
        self.env_dir  = tmp_path / "env"

        for dir_name in ["AppDefs", "RegDefs"]:
            (self.base_dir / dir_name.lower()).mkdir(parents=True)
            (self.env_dir  / dir_name).mkdir(parents=True)

    def _create_user_configs(self, filenames: list[str] = None):
        filenames = filenames or ["override.yaml"]
        for dir_name in ["AppDefs", "RegDefs"]:
            p = self.base_dir / "configuration" / dir_name.lower()
            p.mkdir(parents=True)
            for filename in filenames:
                (p / filename).write_text(CONTENT_BY_DIR[dir_name])

    def test_root_mode_copies_to_base_only(self):
        self._create_user_configs()
        override_app_reg_defs(self.base_dir, self.env_dir, "root")

        assert (self.base_dir / "appdefs" / "override.yaml").exists()
        assert (self.base_dir / "regdefs" / "override.yaml").exists()
        assert not (self.env_dir / "AppDefs" / "override.yaml").exists()
        assert not (self.env_dir / "RegDefs" / "override.yaml").exists()

    def test_dual_mode_copies_to_base_and_env(self):
        self._create_user_configs()
        override_app_reg_defs(self.base_dir, self.env_dir, "dual")

        assert (self.base_dir / "appdefs" / "override.yaml").exists()
        assert (self.base_dir / "regdefs" / "override.yaml").exists()
        assert (self.env_dir  / "AppDefs" / "override.yaml").exists()
        assert (self.env_dir  / "RegDefs" / "override.yaml").exists()

    def test_overrides_existing_file(self):
        self._create_user_configs(["app.yaml"])
        (self.base_dir / "appdefs" / "app.yaml").write_text("old data")

        override_app_reg_defs(self.base_dir, self.env_dir, "root")

        assert (self.base_dir / "appdefs" / "app.yaml").read_text() == APPDEF_CONTENT

    def test_no_user_configs_changes_nothing(self):
        override_app_reg_defs(self.base_dir, self.env_dir, "dual")

        assert list((self.base_dir / "appdefs").iterdir()) == []
        assert list((self.base_dir / "regdefs").iterdir()) == []
        assert list((self.env_dir  / "AppDefs").iterdir()) == []
        assert list((self.env_dir  / "RegDefs").iterdir()) == []

    def test_multiple_files_all_copied(self):
        self._create_user_configs(["app1.yaml", "app2.yaml"])
        override_app_reg_defs(self.base_dir, self.env_dir, "root")

        assert (self.base_dir / "appdefs" / "app1.yaml").exists()
        assert (self.base_dir / "appdefs" / "app2.yaml").exists()

    @pytest.mark.parametrize("dir_name", ["AppDefs", "RegDefs"])
    def test_invalid_override_fails(self, dir_name):
        p = self.base_dir / "configuration" / dir_name.lower()
        p.mkdir(parents=True)
        (p / "broken.yaml").write_text("name: broken\n")

        with pytest.raises(ValueError):
            override_app_reg_defs(self.base_dir, self.env_dir, "dual")

        assert not (self.base_dir / dir_name.lower() / "broken.yaml").exists()
