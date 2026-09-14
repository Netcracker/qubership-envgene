from publish_artifacts.scope import copy_scope


def _write(path, content=b"x" * 100):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


class TestCopyScope:
    def test_copies_included_paths_and_relocates_tmp_subsets(self, tmp_path):
        _write(tmp_path / "environments" / "env1" / "env_definition.yml", b"e")
        _write(tmp_path / "tmp" / "templates" / "common" / "t.yml", b"t")
        _write(tmp_path / "tmp" / "app-artifacts" / "app" / "1.0" / "dd.json", b"d")
        _write(tmp_path / "tmp" / "app-artifacts" / "app" / "1.0" / "dd.zip", b"z")

        dest = tmp_path / "dest"
        copy_scope(tmp_path, dest)

        assert (dest / "environments" / "env1" / "env_definition.yml").read_bytes() == b"e"
        assert (dest / "templates" / "common" / "t.yml").read_bytes() == b"t"
        assert (dest / "app-artifacts" / "app" / "1.0" / "dd.json").read_bytes() == b"d"
        assert not (dest / "app-artifacts" / "app" / "1.0" / "dd.zip").exists()
        assert not (dest / "tmp").exists()
