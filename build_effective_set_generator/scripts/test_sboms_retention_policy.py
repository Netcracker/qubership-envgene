import subprocess
import sys
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

    @pytest.mark.integration
    def test_uc_sbom_1_retention_disabled(self, tmp_path, monkeypatch):
        # 1. Arrange
        sboms_dir = tmp_path / "sboms"
        sboms_dir.mkdir()
        app_a_dir = sboms_dir / "app-a"
        app_a_dir.mkdir()

        TestHelpers.create_file(app_a_dir / "app-a-1.0.sbom.json", size=100)
        TestHelpers.create_file(app_a_dir / "app-a-2.0.sbom.json", size=100)

        config_dir = tmp_path / "configuration"
        config_dir.mkdir()
        config_file = config_dir / "config.yml"
        config_file.write_text("""
sbom_retention:
  enabled: false
""")

        monkeypatch.setenv("CI_PROJECT_DIR", str(tmp_path))
        monkeypatch.setenv("ENVGENE_INSTANCE_PATH", str(tmp_path))

        # 2. Act
        result = subprocess.run(
            [sys.executable, "sboms_retention_policy.py"],
            capture_output=True,
            text=True,
            check=True,
            cwd="F:/project/qubership-envgene/build_effective_set_generator/scripts/"
        )

        # 3. Assert
        assert "SBOM retention policy is disabled" in result.stdout
        remaining_files = {f.name for f in app_a_dir.iterdir()}
        assert remaining_files == {"app-a-1.0.sbom.json", "app-a-2.0.sbom.json"}

    @pytest.mark.integration
    def test_uc_sbom_2_within_limit_no_cleanup(self, tmp_path, monkeypatch):
        # 1. Arrange
        sboms_dir = tmp_path / "sboms"
        sboms_dir.mkdir()

        # app-a with 7 versions
        app_a_dir = sboms_dir / "app-a"
        app_a_dir.mkdir()
        for i in range(7):
            TestHelpers.create_file(app_a_dir / f"app-a-{i}.0.sbom.json", size=100, mtime=time.time() + i)

        # app-b with 4 versions
        app_b_dir = sboms_dir / "app-b"
        app_b_dir.mkdir()
        for i in range(4):
            TestHelpers.create_file(app_b_dir / f"app-b-{i}.0.sbom.json", size=100, mtime=time.time() + i)

        # app-c with 10 versions
        app_c_dir = sboms_dir / "app-c"
        app_c_dir.mkdir()
        for i in range(10):
            TestHelpers.create_file(app_c_dir / f"app-c-{i}.0.sbom.json", size=100, mtime=time.time() + i)

        config_dir = tmp_path / "configuration"
        config_dir.mkdir()
        config_file = config_dir / "config.yml"
        config_file.write_text("""
sbom_retention:
  enabled: true
  keep_versions_per_app: 10
""")

        monkeypatch.setenv("CI_PROJECT_DIR", str(tmp_path))
        monkeypatch.setenv("ENVGENE_INSTANCE_PATH", str(tmp_path))

        # 2. Act
        result = subprocess.run(
            [sys.executable, "sboms_retention_policy.py"],
            capture_output=True,
            text=True,
            check=True,
            cwd="F:/project/qubership-envgene/build_effective_set_generator/scripts/"
        )

        # 3. Assert
        assert f"SBOM retention policy is enabled for directory {sboms_dir}" in result.stdout
        assert "keep_versions_per_app=10" in result.stdout
        assert "Removing file:" not in result.stdout

        assert len(list(app_a_dir.iterdir())) == 7
        assert len(list(app_b_dir.iterdir())) == 4
        assert len(list(app_c_dir.iterdir())) == 10

    @pytest.mark.integration
    def test_uc_sbom_3_per_app_retention(self, tmp_path, monkeypatch):
        # 1. Arrange
        sboms_dir = tmp_path / "sboms"
        sboms_dir.mkdir()

        # app-a with 15 versions
        app_a_dir = sboms_dir / "app-a"
        app_a_dir.mkdir()
        for i in range(15):
            TestHelpers.create_file(app_a_dir / f"app-a-{i}.0.sbom.json", size=100, mtime=time.time() + i)

        # app-b with 12 versions
        app_b_dir = sboms_dir / "app-b"
        app_b_dir.mkdir()
        for i in range(12):
            TestHelpers.create_file(app_b_dir / f"app-b-{i}.0.sbom.json", size=100, mtime=time.time() + i)

        # app-c with 8 versions
        app_c_dir = sboms_dir / "app-c"
        app_c_dir.mkdir()
        for i in range(8):
            TestHelpers.create_file(app_c_dir / f"app-c-{i}.0.sbom.json", size=100, mtime=time.time() + i)

        config_dir = tmp_path / "configuration"
        config_dir.mkdir()
        config_file = config_dir / "config.yml"
        config_file.write_text("""
sbom_retention:
  enabled: true
  keep_versions_per_app: 10
""")

        monkeypatch.setenv("CI_PROJECT_DIR", str(tmp_path))
        monkeypatch.setenv("ENVGENE_INSTANCE_PATH", str(tmp_path))

        # 2. Act
        result = subprocess.run(
            [sys.executable, "sboms_retention_policy.py"],
            capture_output=True,
            text=True,
            check=True,
            cwd="F:/project/qubership-envgene/build_effective_set_generator/scripts/"
        )

        # 3. Assert
        assert f"SBOM retention policy is enabled for directory {sboms_dir}" in result.stdout
        assert "keep_versions_per_app=10" in result.stdout
        assert "Removing file:" in result.stdout

        assert len(list(app_a_dir.iterdir())) == 10
        assert len(list(app_b_dir.iterdir())) == 10
        assert len(list(app_c_dir.iterdir())) == 8

    @pytest.mark.integration
    def test_uc_sbom_4_custom_version_count(self, tmp_path, monkeypatch):
        # 1. Arrange
        sboms_dir = tmp_path / "sboms"
        sboms_dir.mkdir()

        # postgres with 10 versions
        postgres_dir = sboms_dir / "postgres"
        postgres_dir.mkdir()
        for i in range(10):
            TestHelpers.create_file(postgres_dir / f"postgres-{i}.0.sbom.json", size=100, mtime=time.time() + i)

        config_dir = tmp_path / "configuration"
        config_dir.mkdir()
        config_file = config_dir / "config.yml"
        config_file.write_text("""
sbom_retention:
  enabled: true
  keep_versions_per_app: 3
""")

        monkeypatch.setenv("CI_PROJECT_DIR", str(tmp_path))
        monkeypatch.setenv("ENVGENE_INSTANCE_PATH", str(tmp_path))

        # 2. Act
        result = subprocess.run(
            [sys.executable, "sboms_retention_policy.py"],
            capture_output=True,
            text=True,
            check=True,
            cwd="F:/project/qubership-envgene/build_effective_set_generator/scripts/"
        )

        # 3. Assert
        assert f"SBOM retention policy is enabled for directory {sboms_dir}" in result.stdout
        assert "keep_versions_per_app=3" in result.stdout
        assert "Removing file:" in result.stdout

        assert len(list(postgres_dir.iterdir())) == 3

    @pytest.mark.integration
    def test_uc_sbom_5_total_size_exceeded(self, tmp_path, monkeypatch):
        # 1. Arrange
        sboms_dir = tmp_path / "sboms"
        sboms_dir.mkdir()

        # app-a with 5 versions, total size > 1200 MB
        app_a_dir = sboms_dir / "app-a"
        app_a_dir.mkdir()
        for i in range(5):
            TestHelpers.create_file(app_a_dir / f"app-a-{i}.0.sbom.json", size=300 * 1024 * 1024, mtime=time.time() + i)

        # app-b with 5 versions
        app_b_dir = sboms_dir / "app-b"
        app_b_dir.mkdir()
        for i in range(5):
            TestHelpers.create_file(app_b_dir / f"app-b-{i}.0.sbom.json", size=100, mtime=time.time() + i)

        config_dir = tmp_path / "configuration"
        config_dir.mkdir()
        config_file = config_dir / "config.yml"
        config_file.write_text("""
sbom_retention:
  enabled: true
  keep_versions_per_app: 10
""")

        monkeypatch.setenv("CI_PROJECT_DIR", str(tmp_path))
        monkeypatch.setenv("ENVGENE_INSTANCE_PATH", str(tmp_path))

        # 2. Act
        result = subprocess.run(
            [sys.executable, "sboms_retention_policy.py"],
            capture_output=True,
            text=True,
            check=True,
            cwd="F:/project/qubership-envgene/build_effective_set_generator/scripts/"
        )

        # 3. Assert
        assert f"SBOM directory exceeds size limit, starting cleanup: {sboms_dir}" in result.stdout
        assert "Removing file:" in result.stdout

        assert len(list(app_a_dir.iterdir())) == 1
        assert len(list(app_b_dir.iterdir())) == 1
