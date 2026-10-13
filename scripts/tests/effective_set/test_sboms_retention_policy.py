import time
import pytest

from envgenehelper import cleanup_dir_by_age, is_over_size_limit
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

        TestHelpers.create_file(files[0], size=1, mtime=now - 300)
        TestHelpers.create_file(files[1], size=1, mtime=now - 200)
        TestHelpers.create_file(files[2], size=1, mtime=now - 100)

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

        TestHelpers.create_file(files[0], size=1, mtime=now - 180)
        TestHelpers.create_file(files[1], size=1, mtime=now - 120)
        TestHelpers.create_file(files[2], size=1, mtime=now - 60)

        cleanup_dir_by_age(tmp_path, keep_last=3)

        remaining = {f.name for f in tmp_path.iterdir()}
        assert remaining == {"file1.json", "file2.json", "file3.json"}

    @pytest.mark.unit
    def test_dir_not_exists_returns_false(self, tmp_path):
        missing = tmp_path / "missing"
        result = is_over_size_limit(missing, max_size_mb=1)
        assert result is False

    @pytest.mark.unit
    def test_empty_dir_returns_false(self, tmp_path):
        result = is_over_size_limit(tmp_path, max_size_mb=1)
        assert result is False

    @pytest.mark.unit
    def test_below_limit_returns_false(self, tmp_path):
        TestHelpers.create_file(tmp_path / "file.json", size=1024 * 1024)
        result = is_over_size_limit(tmp_path, max_size_mb=10)
        assert result is False

    @pytest.mark.unit
    def test_dir_exactly_at_limit_returns_false(self, tmp_path):
        TestHelpers.create_file(tmp_path / "file.json", size=1024 * 1024)
        result = is_over_size_limit(tmp_path, max_size_mb=1)
        assert result is False

    @pytest.mark.unit
    def test_dir_above_limit_returns_true(self, tmp_path):
        TestHelpers.create_file(tmp_path / "file1.json", size=1024 * 1024)
        TestHelpers.create_file(tmp_path / "file2.json", size=1024 * 1024)
        result = is_over_size_limit(tmp_path, max_size_mb=1)
        assert result is True

