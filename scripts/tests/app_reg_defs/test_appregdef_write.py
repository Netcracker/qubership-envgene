import pytest

from build_env.appregdef_render import write_app_reg_defs
from envgenehelper import open_current_env_instance_store

RENDERED_DEFS = {
    "AppDefs": {"file": {"name": "file"}},
    "RegDefs": {"file": {"name": "file"}},
}


class TestWriteAppRegDefs:

    @pytest.fixture(autouse=True)
    def setup_dirs(self, tmp_path):
        self.base_dir = tmp_path / "base"
        self.env_dir = tmp_path / "env"
        with open_current_env_instance_store(self.env_dir, base_dir=self.base_dir) as env_instance_store:
            self.env_instance_store = env_instance_store
            yield

    def _write(self, placement_mode):
        write_app_reg_defs(self.base_dir, RENDERED_DEFS, self.env_dir, placement_mode)
        self.env_instance_store.flush()

    def test_invalid_placement_mode(self):
        with pytest.raises(ValueError, match="Unknown 'app_reg_defs_placement'"):
            write_app_reg_defs(self.base_dir, RENDERED_DEFS, self.env_dir, "invalid")

    def test_root_mode_moves_to_root_only(self):
        self._write("root")

        assert (self.base_dir / "appdefs" / "file.yml").exists()
        assert (self.base_dir / "regdefs" / "file.yml").exists()
        assert not (self.env_dir / "AppDefs").exists()
        assert not (self.env_dir / "RegDefs").exists()

    def test_dual_mode_moves_to_root_and_copies_to_env(self):
        self._write("dual")

        assert (self.base_dir / "appdefs" / "file.yml").exists()
        assert (self.base_dir / "regdefs" / "file.yml").exists()
        assert (self.env_dir / "AppDefs" / "file.yml").exists()
        assert (self.env_dir / "RegDefs" / "file.yml").exists()

    def test_not_preserves_existing_files_on_root(self):
        stale = self.base_dir / "appdefs"
        stale.mkdir(parents=True)
        (stale / "old.yaml").write_text("stale")

        self._write("root")

        assert not (stale / "old.yaml").exists()
        assert (stale / "file.yml").exists()

    def test_nothing_on_disk_before_flush(self):
        write_app_reg_defs(self.base_dir, RENDERED_DEFS, self.env_dir, "dual")

        assert not (self.base_dir / "appdefs").exists()
        assert self.env_instance_store.get(self.base_dir / "appdefs" / "file.yml") == {"name": "file"}
        assert self.env_instance_store.get(self.env_dir / "AppDefs" / "file.yml") == {"name": "file"}

    def test_not_preserves_existing_files_on_env(self):
        stale = self.env_dir / "AppDefs"
        stale.mkdir(parents=True)
        (stale / "old.yaml").write_text("stale")

        self._write("dual")

        assert not (stale / "old.yaml").exists()
        assert (stale / "file.yml").exists()

    def test_root_mode_removes_env_dirs(self):
        stale = self.env_dir / "RegDefs"
        stale.mkdir(parents=True)
        (stale / "old.yaml").write_text("stale")

        self._write("root")

        assert not stale.exists()
