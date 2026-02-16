import pytest


class TestSortParamsetsWithSameName:

    @staticmethod
    def sort_paramsets_with_same_name(entries: list[dict]) -> list[dict]:
        def sort_key(e):
            path = e["filePath"]
            if "from_template" in path:
                return 0, path
            elif "from_instance" in path:
                return 2, path
            return 1, path
        return sorted(entries, key=sort_key)

    def test_all_three_levels(self):
        entries = [
            {"filePath": "/tmp/render/parameters/from_instance/test.yml", "envSpecific": True},
            {"filePath": "/tmp/render/parameters/test.yml", "envSpecific": False},
            {"filePath": "/tmp/render/parameters/from_template/test.yml", "envSpecific": False},
        ]
        sorted_entries = self.sort_paramsets_with_same_name(entries)
        assert "from_template" in sorted_entries[0]["filePath"]
        assert "from_instance" not in sorted_entries[1]["filePath"]
        assert "from_instance" in sorted_entries[2]["filePath"]

    def test_template_and_instance(self):
        entries = [
            {"filePath": "/tmp/render/parameters/from_instance/test.yml", "envSpecific": True},
            {"filePath": "/tmp/render/parameters/from_template/test.yml", "envSpecific": False},
        ]
        sorted_entries = self.sort_paramsets_with_same_name(entries)
        assert "from_template" in sorted_entries[0]["filePath"]
        assert "from_instance" in sorted_entries[1]["filePath"]

    def test_multiple_files_sorted_alphabetically(self):
        entries = [
            {"filePath": "/tmp/render/parameters/from_template/z_params.yml", "envSpecific": False},
            {"filePath": "/tmp/render/parameters/from_template/a_params.yml", "envSpecific": False},
            {"filePath": "/tmp/render/parameters/from_template/m_params.yml", "envSpecific": False},
        ]
        sorted_entries = self.sort_paramsets_with_same_name(entries)
        paths = [e["filePath"] for e in sorted_entries]
        assert paths == sorted(paths)

    def test_real_world_dcl_e2e(self):
        entries = [
            {"filePath": "/tmp/render/parameters/from_instance/DCL_E2E_parameters.yaml", "envSpecific": True},
            {"filePath": "/tmp/render/parameters/from_template/e2e/dcl.yaml", "envSpecific": False},
        ]
        sorted_entries = self.sort_paramsets_with_same_name(entries)
        assert "from_template" in sorted_entries[0]["filePath"]
        assert "from_instance" in sorted_entries[1]["filePath"]

    def test_empty_list(self):
        assert len(self.sort_paramsets_with_same_name([])) == 0
