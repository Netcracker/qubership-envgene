import pytest
from cProfile import Profile

from build_env.appregdef_render import write_app_reg_defs
from envgene_shared.utils.yaml_utils import validate_yaml_by_scheme_or_fail

RENDERED_DEFS = {
    "AppDefs": {
        "file": {
            "name": "file",
            "registryName": "registry",
            "artifactId": "artifact",
            "groupId": "group",
            "supportParallelDeploy": False,
            "deployParameters": {},
            "technicalConfigurationParameters": {},
        }
    },
    "RegDefs": {
        "file": {
            "name": "file",
            "credentialsId": "credentials",
            "mavenConfig": {
                "releaseGroup": "release",
                "repositoryDomainName": "repository",
                "snapshotGroup": "snapshot",
                "targetRelease": "release",
                "targetSnapshot": "snapshot",
                "targetStaging": "staging",
            },
            "dockerConfig": {
                "groupName": "group",
                "groupUri": "group",
                "releaseRepoName": "release",
                "releaseUri": "release",
                "snapshotRepoName": "snapshot",
                "snapshotUri": "snapshot",
                "stagingRepoName": "staging",
                "stagingUri": "staging",
            },
        }
    },
}


class TestWriteAppRegDefs:

    @pytest.fixture(autouse=True)
    def setup_dirs(self, tmp_path):
        self.base_dir = tmp_path / "base"
        self.env_dir = tmp_path / "env"

    def test_invalid_placement_mode(self):
        with pytest.raises(ValueError, match="Unknown 'app_reg_defs_placement'"):
            write_app_reg_defs(self.base_dir, RENDERED_DEFS, self.env_dir, "invalid")

    def test_root_mode_moves_to_root_only(self):
        write_app_reg_defs(self.base_dir, RENDERED_DEFS, self.env_dir, "root")

        assert (self.base_dir / "appdefs" / "file.yml").exists()
        assert (self.base_dir / "regdefs" / "file.yml").exists()
        assert not (self.env_dir / "AppDefs").exists()
        assert not (self.env_dir / "RegDefs").exists()

    def test_dual_mode_moves_to_root_and_copies_to_env(self):
        profile = Profile()
        profile.runcall(write_app_reg_defs, self.base_dir, RENDERED_DEFS, self.env_dir, "dual")

        calls = {entry.code: entry.callcount for entry in profile.getstats()}
        assert calls[validate_yaml_by_scheme_or_fail.__code__] == 2
        assert (self.base_dir / "appdefs" / "file.yml").exists()
        assert (self.base_dir / "regdefs" / "file.yml").exists()
        assert (self.env_dir / "AppDefs" / "file.yml").exists()
        assert (self.env_dir / "RegDefs" / "file.yml").exists()
        assert (self.base_dir / "appdefs" / "file.yml").read_bytes() == (self.env_dir / "AppDefs" / "file.yml").read_bytes()
        assert (self.base_dir / "regdefs" / "file.yml").read_bytes() == (self.env_dir / "RegDefs" / "file.yml").read_bytes()

    def test_preserves_existing_files(self):
        stale = self.base_dir / "appdefs"
        stale.mkdir(parents=True)
        (stale / "old.yaml").write_text("stale")

        write_app_reg_defs(self.base_dir, RENDERED_DEFS, self.env_dir, "root")

        assert (stale / "old.yaml").exists()
        assert (stale / "file.yml").exists()

    def test_not_preserves_existing_files_on_env(self):
        stale = self.env_dir / "AppDefs"
        stale.mkdir(parents=True)
        (stale / "old.yaml").write_text("stale")

        write_app_reg_defs(self.base_dir, RENDERED_DEFS, self.env_dir, "dual")

        assert not (stale / "old.yaml").exists()
        assert (stale / "file.yml").exists()

    def test_root_mode_removes_env_dirs(self):
        stale = self.env_dir / "RegDefs"
        stale.mkdir(parents=True)
        (stale / "old.yaml").write_text("stale")

        write_app_reg_defs(self.base_dir, RENDERED_DEFS, self.env_dir, "root")

        assert not stale.exists()
