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
        _write(tmp_path / "tmp" / "envgene-regdefv2-adapter" / "RegDefs" / "r.yml", b"r")
        _write(tmp_path / "tmp" / "envgene-regdefv2-adapter" / "pubreg_params.yaml", b"secret")

        dest = tmp_path / "dest"
        copy_scope(tmp_path, dest)

        assert (dest / "environments" / "env1" / "env_definition.yml").read_bytes() == b"e"
        assert (dest / "templates" / "common" / "t.yml").read_bytes() == b"t"
        assert (dest / "app-artifacts" / "app" / "1.0" / "dd.json").read_bytes() == b"d"
        assert not (dest / "app-artifacts" / "app" / "1.0" / "dd.zip").exists()
        assert (dest / "tmp" / "envgene-regdefv2-adapter" / "RegDefs" / "r.yml").read_bytes() == b"r"
        assert not (dest / "tmp" / "envgene-regdefv2-adapter" / "pubreg_params.yaml").exists()
        assert not (dest / "tmp" / "templates").exists()
        assert not (dest / "tmp" / "app-artifacts").exists()
