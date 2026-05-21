import time

import pytest
from envgenehelper import cleanup_dir_by_age, cleanup_dir_by_size
from envgenehelper.test_helpers import TestHelpers


class TestSBOMSRetentionPolicy:

    @pytest.mark.unit
    def test_cleanup_dir_by_age_removes_old_files(self, tmp_path):
        now = time.time()
        files = [
            tmp_path / "old.json",
            tmp_path / "mid.json",
            tmp_path / "new.json",
        ]
        TestHelpers.create_file(files[0], mtime=now - 300)
        TestHelpers.create_file(files[1], mtime=now - 200)
        TestHelpers.create_file(files[2], mtime=now - 100)

        cleanup_dir_by_age(tmp_path, keep_last=2)

        remaining = {f.name for f in tmp_path.iterdir()}
        assert remaining == {"mid.json", "new.json"}

    @pytest.mark.unit
    def test_cleanup_dir_by_age_keep_all(self, tmp_path):
        now = time.time()
        files = [
            tmp_path / "file1.json",
            tmp_path / "file2.json",
            tmp_path / "file3.json",
        ]
        TestHelpers.create_file(files[0], mtime=now - 180)
        TestHelpers.create_file(files[1], mtime=now - 120)
        TestHelpers.create_file(files[2], mtime=now - 60)

        cleanup_dir_by_age(tmp_path, keep_last=3)

        remaining = {f.name for f in tmp_path.iterdir()}
        assert remaining == {"file1.json", "file2.json", "file3.json"}

    @pytest.mark.unit
    def test_cleanup_dir_by_size_within_limit(self, tmp_path):
        files = [
            tmp_path / "file1.json",
            tmp_path / "file2.json",
            tmp_path / "file3.json",
        ]
        for f in files:
            TestHelpers.create_file(f, size=1024)

        cleanup_dir_by_size(tmp_path, max_size_mb=10)

        remaining = {f.name for f in tmp_path.iterdir()}
        assert remaining == {"file1.json", "file2.json", "file3.json"}

    @pytest.mark.unit
    def test_cleanup_dir_by_size_exceeds(self, tmp_path):
        files = [
            tmp_path / "file1.json",
            tmp_path / "file2.json",
            tmp_path / "file3.json",
        ]
        for f in files:
            TestHelpers.create_file(f, size=1024 * 1024)

        cleanup_dir_by_size(tmp_path, max_size_mb=2)

        remaining = {f.name for f in tmp_path.iterdir()}
        assert remaining == set()
