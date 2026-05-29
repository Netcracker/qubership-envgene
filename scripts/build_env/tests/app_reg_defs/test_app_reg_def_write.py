import pytest

from appregdef_render import write_app_reg_defs

class TestWriteAppRegDefs:

    @pytest.fixture(autouse=True)
    def setup_dirs(self, tmp_path):
        self.base_dir   = tmp_path / "base"
        self.render_dir = tmp_path / "render"
        self.env_dir    = tmp_path / "env"

    def _create_source_dirs(self):
        for d in ["AppDefs", "RegDefs"]:
            (self.render_dir / d).mkdir(parents=True)
            (self.render_dir / d / "file.yaml").write_text("data")

    def test_invalid_placement_mode(self):
        with pytest.raises(ValueError, match="Unknown 'app_reg_defs_placement'"):
            write_app_reg_defs(self.base_dir, self.render_dir, self.env_dir, "invalid")

    def test_root_mode_moves_to_root_only(self):
        self._create_source_dirs()
        write_app_reg_defs(self.base_dir, self.render_dir, self.env_dir, "root")

        assert (self.base_dir / "appdefs").exists()
        assert (self.base_dir / "regdefs").exists()
        assert not (self.env_dir / "AppDefs").exists()
        assert not (self.env_dir / "RegDefs").exists()

    def test_dual_mode_moves_to_root_and_copies_to_env(self):
        self._create_source_dirs()
        write_app_reg_defs(self.base_dir, self.render_dir, self.env_dir, "dual")

        assert (self.base_dir / "appdefs").exists()
        assert (self.base_dir / "regdefs").exists()
        assert (self.env_dir / "AppDefs").exists()
        assert (self.env_dir / "RegDefs").exists()

    def test_cleans_stale_dirs_before_writing(self):
        (self.env_dir  / "AppDefs").mkdir(parents=True)
        (self.base_dir / "appdefs").mkdir(parents=True)

        write_app_reg_defs(self.base_dir, self.render_dir, self.env_dir, "dual")

        assert not (self.env_dir  / "AppDefs").exists()
        assert not (self.base_dir / "appdefs").exists()
