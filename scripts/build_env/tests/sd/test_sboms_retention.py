import logging
import shutil
import time
from pathlib import Path

import pytest
from pydantic import ValidationError

from build_effective_set_generator.scripts.sboms_retention_policy import sboms_retention_policy
from envgenehelper.test_helpers import TestHelpers
from scripts.build_env.tests.base_test import BaseTest

FEATURE_TEST_DIR = "test_handle_sboms"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _files(directory: Path) -> list[str]:
    return [f.name for f in directory.iterdir() if f.is_file()]


def _files_by_mtime(app_dir: Path) -> list[str]:
    files = [f for f in app_dir.iterdir() if f.is_file()]
    files.sort(key=lambda f: f.stat().st_mtime)
    return [f.name for f in files]


def _dump_dir(directory: Path) -> str:
    if not directory.exists():
        return f"{directory} — does not exist"
    entries = sorted(directory.iterdir(), key=lambda f: f.stat().st_mtime)
    if not entries:
        return f"{directory} — empty"
    lines = [f"  {e.name} (mtime={e.stat().st_mtime:.3f}, {'dir' if e.is_dir() else f'{e.stat().st_size}B'})"
             for e in entries]
    return f"{directory}:\n" + "\n".join(lines)


class TestSbomRetention(BaseTest):

    def setup_method(self):
        self.feature_dir = self.output_dir / FEATURE_TEST_DIR
        self.feature_dir.mkdir(parents=True, exist_ok=True)

    def _prepare(self, tc_name: str, config_content: str) -> Path:
        case_dir = self.feature_dir / tc_name
        if case_dir.exists():
            shutil.rmtree(case_dir)
        case_dir.mkdir(parents=True)
        _write(case_dir / "configuration" / "config.yml", config_content)
        self.set_ci_project_dir(case_dir)
        return case_dir

    # ------------------------------------------------------------------
    # UC-SBOM-1: retention disabled — no files removed
    # ------------------------------------------------------------------

    def test_uc_sbom_1_retention_disabled_files_untouched(self):
        case_dir = self._prepare("TC-SBOM-1", "sbom_retention:\n  enabled: false\n")
        app_a_dir = case_dir / "sboms" / "app-a"
        app_a_dir.mkdir(parents=True)
        TestHelpers.create_file(app_a_dir / "app-a-1.0.sbom.json", size=100)
        TestHelpers.create_file(app_a_dir / "app-a-2.0.sbom.json", size=100)

        sboms_retention_policy()

        assert len(_files(app_a_dir)) == 2

    # ------------------------------------------------------------------
    # UC-SBOM-2: all apps below limit — nothing pruned
    # ------------------------------------------------------------------

    def test_uc_sbom_2_all_apps_below_limit_nothing_pruned(self):
        case_dir = self._prepare("TC-SBOM-2",
                                 "sbom_retention:\n  enabled: true\n  keep_versions_per_app: 10\n")
        now = time.time()
        sboms_dir = case_dir / "sboms"
        app_a_dir = sboms_dir / "app-a"
        app_a_dir.mkdir(parents=True)
        for i in range(7):
            TestHelpers.create_file(app_a_dir / f"app-a-{i}.sbom.json", 100, now + i)
        app_b_dir = sboms_dir / "app-b"
        app_b_dir.mkdir(parents=True)
        for i in range(4):
            TestHelpers.create_file(app_b_dir / f"app-b-{i}.sbom.json", 100, now + i)
        app_c_dir = sboms_dir / "app-c"
        app_c_dir.mkdir(parents=True)
        for i in range(10):
            TestHelpers.create_file(app_c_dir / f"app-c-{i}.sbom.json", 100, now + i)

        sboms_retention_policy()

        assert len(_files_by_mtime(app_a_dir)) == 7
        assert len(_files_by_mtime(app_b_dir)) == 4
        assert len(_files_by_mtime(app_c_dir)) == 10

    # ------------------------------------------------------------------
    # UC-SBOM-3: some apps exceed limit — trim to 10 newest
    # ------------------------------------------------------------------

    def test_uc_sbom_3_excess_files_pruned_to_limit(self):
        case_dir = self._prepare("TC-SBOM-3",
                                 "sbom_retention:\n  enabled: true\n  keep_versions_per_app: 10\n")
        now = time.time()
        sboms_dir = case_dir / "sboms"
        app_a_dir = sboms_dir / "app-a"
        app_a_dir.mkdir(parents=True)
        for i in range(15):
            TestHelpers.create_file(app_a_dir / f"app-a-{i}.sbom.json", 100, now + i)
        app_b_dir = sboms_dir / "app-b"
        app_b_dir.mkdir(parents=True)
        for i in range(12):
            TestHelpers.create_file(app_b_dir / f"app-b-{i}.sbom.json", 100, now + i)
        app_c_dir = sboms_dir / "app-c"
        app_c_dir.mkdir(parents=True)
        for i in range(8):
            TestHelpers.create_file(app_c_dir / f"app-c-{i}.sbom.json", 100, now + i)

        sboms_retention_policy()

        app_a_files = _files_by_mtime(app_a_dir)
        assert len(app_a_files) == 10, _dump_dir(app_a_dir)
        assert app_a_files[-1] == "app-a-14.sbom.json", f"newest must be retained; got {app_a_files}"
        assert app_a_files[0] == "app-a-5.sbom.json", f"oldest retained must be app-a-5; got {app_a_files}"

        app_b_files = _files_by_mtime(app_b_dir)
        assert len(app_b_files) == 10, _dump_dir(app_b_dir)
        assert app_b_files[-1] == "app-b-11.sbom.json", f"newest must be retained; got {app_b_files}"
        assert app_b_files[0] == "app-b-2.sbom.json", f"oldest retained must be app-b-2; got {app_b_files}"

        app_c_files = _files_by_mtime(app_c_dir)
        assert len(app_c_files) == 8, _dump_dir(app_c_dir)

    # ------------------------------------------------------------------
    # UC-SBOM-4: strict limit of 3
    # ------------------------------------------------------------------

    def test_uc_sbom_4_strict_limit_keeps_3_newest(self):
        case_dir = self._prepare("TC-SBOM-4",
                                 "sbom_retention:\n  enabled: true\n  keep_versions_per_app: 3\n")
        now = time.time()
        postgres_dir = case_dir / "sboms" / "postgres"
        postgres_dir.mkdir(parents=True)
        for i in range(10):
            TestHelpers.create_file(postgres_dir / f"postgres-{i}.sbom.json", 100, now + i)

        sboms_retention_policy()

        postgres_files = _files_by_mtime(postgres_dir)
        assert len(postgres_files) == 3, _dump_dir(postgres_dir)
        assert postgres_files[-1] == "postgres-9.sbom.json", f"newest must be retained; got {postgres_files}"
        assert postgres_files[0] == "postgres-7.sbom.json", f"oldest retained must be postgres-7; got {postgres_files}"

    # ------------------------------------------------------------------
    # UC-SBOM-5: total size exceeds limit — trim all app dirs to 1 newest
    # ------------------------------------------------------------------

    def test_uc_sbom_5_size_limit_trims_all_apps_to_one(self):
        case_dir = self._prepare("TC-SBOM-5",
                                 "sbom_retention:\n  enabled: true\n  keep_versions_per_app: 10\n")
        now = time.time()
        sboms_dir = case_dir / "sboms"
        app_a_dir = sboms_dir / "app-a"
        app_a_dir.mkdir(parents=True)
        for i in range(5):
            TestHelpers.create_file(app_a_dir / f"app-a-{i}.sbom.json", 300 * 1024 * 1024, now + i)
        app_b_dir = sboms_dir / "app-b"
        app_b_dir.mkdir(parents=True)
        for i in range(5):
            TestHelpers.create_file(app_b_dir / f"app-b-{i}.sbom.json", 100, now + i)

        sboms_retention_policy()

        app_a_files = _files_by_mtime(app_a_dir)
        assert len(app_a_files) == 1, _dump_dir(app_a_dir)
        assert app_a_files[0] == "app-a-4.sbom.json", f"only newest app-a must survive; got {app_a_files}"

        app_b_files = _files_by_mtime(app_b_dir)
        assert len(app_b_files) == 1, _dump_dir(app_b_dir)
        assert app_b_files[0] == "app-b-4.sbom.json", f"only newest app-b must survive; got {app_b_files}"

    # ------------------------------------------------------------------
    # Negative
    # ------------------------------------------------------------------

    def test_missing_sboms_dir_logs_warning_and_exits_cleanly(self, caplog):
        # UC-SBOM-NEGATIVE-1: missing sboms directory logs a warning and exits cleanly.
        case_dir = self.feature_dir / "UC-SBOM-NEGATIVE-1"
        if case_dir.exists():
            shutil.rmtree(case_dir)
        case_dir.mkdir(parents=True)
        self.set_ci_project_dir(case_dir)

        with caplog.at_level(logging.WARNING, logger="envgene"):
            sboms_retention_policy()

        assert "does not exist" in caplog.text

    def test_invalid_config_raises_validation_error(self):
        # UC-SBOM-NEGATIVE-2: invalid keep_versions_per_app type must raise ValidationError.
        case_dir = self._prepare("UC-SBOM-NEGATIVE-2",
                                 "sbom_retention:\n  enabled: true\n  keep_versions_per_app: 'invalid'\n")
        (case_dir / "sboms").mkdir(parents=True)

        with pytest.raises(ValidationError):
            sboms_retention_policy()


class TestSbomMigration(BaseTest):
    """UC-SBOM-MIG: migration from flat to per-application SBOM layout."""

    def setup_method(self):
        self.feature_dir = self.output_dir / FEATURE_TEST_DIR / "migration"
        self.feature_dir.mkdir(parents=True, exist_ok=True)

    def _prepare(self, tc_name: str) -> Path:
        case_dir = self.feature_dir / tc_name
        if case_dir.exists():
            shutil.rmtree(case_dir)
        case_dir.mkdir(parents=True)
        _write(case_dir / "configuration" / "config.yml",
               "sbom_retention:\n  enabled: true\n  keep_versions_per_app: 10\n")
        self.set_ci_project_dir(case_dir)
        return case_dir

    def test_flat_legacy_files_removed_per_app_files_untouched(self, caplog):
        # UC-SBOM-MIG-1: flat SBOM files directly under /sboms/ are deleted on first run.
        # Per-application subdirectory files must not be touched.
        case_dir = self._prepare("UC-SBOM-MIG-1")
        sboms_dir = case_dir / "sboms"
        sboms_dir.mkdir()

        flat_app_a = sboms_dir / "app-a-1.0.sbom.json"
        flat_app_b = sboms_dir / "app-b-2.3.sbom.json"
        TestHelpers.create_file(flat_app_a, size=100)
        TestHelpers.create_file(flat_app_b, size=100)

        app_a_dir = sboms_dir / "app-a"
        app_a_dir.mkdir()
        existing_new_layout_file = app_a_dir / "app-a-1.0.sbom.json"
        TestHelpers.create_file(existing_new_layout_file, size=100)

        with caplog.at_level(logging.INFO, logger="envgene"):
            sboms_retention_policy()

        assert not flat_app_a.exists(), f"flat app-a SBOM must be removed;\n{_dump_dir(sboms_dir)}"
        assert not flat_app_b.exists(), f"flat app-b SBOM must be removed;\n{_dump_dir(sboms_dir)}"
        remaining_flat = [f for f in sboms_dir.iterdir() if f.is_file()]
        assert remaining_flat == [], f"unexpected flat files remain:\n{_dump_dir(sboms_dir)}"
        assert existing_new_layout_file.exists(), \
            f"per-app layout file must not be deleted;\n{_dump_dir(app_a_dir)}"
        assert "legacy" in caplog.text.lower() or "Removing" in caplog.text, \
            f"expected removal log entry; captured log:\n{caplog.text}"


class TestSbomRetentionBackwardCompat(BaseTest):
    """Backward compatibility: old/incomplete config shapes must not crash the policy."""

    def setup_method(self):
        self.feature_dir = self.output_dir / FEATURE_TEST_DIR / "backward_compat"
        self.feature_dir.mkdir(parents=True, exist_ok=True)

    def _prepare(self, case_name: str, config_content: str) -> tuple[Path, Path]:
        case_dir = self.feature_dir / case_name
        if case_dir.exists():
            shutil.rmtree(case_dir)
        case_dir.mkdir(parents=True)
        _write(case_dir / "configuration" / "config.yml", config_content)
        self.set_ci_project_dir(case_dir)
        sboms_dir = case_dir / "sboms"
        sboms_dir.mkdir()
        return case_dir, sboms_dir

    def test_no_config_file_disables_policy(self, caplog):
        # Old repos may have no configuration/config.yml — policy must disable silently.
        case_dir = self.feature_dir / "no-config-file"
        if case_dir.exists():
            shutil.rmtree(case_dir)
        case_dir.mkdir(parents=True)
        self.set_ci_project_dir(case_dir)
        sboms_dir = case_dir / "sboms"
        sboms_dir.mkdir()
        app_dir = sboms_dir / "app-a"
        app_dir.mkdir()
        TestHelpers.create_file(app_dir / "app-a-1.0.sbom.json", size=100)

        with caplog.at_level(logging.INFO, logger="envgene"):
            sboms_retention_policy()

        assert "disabled" in caplog.text.lower(), \
            f"expected 'disabled' log; got:\n{caplog.text}"
        assert len(_files(app_dir)) == 1, \
            f"files must be untouched when config is absent;\n{_dump_dir(app_dir)}"

    def test_no_sbom_retention_section_disables_policy(self, caplog):
        # config.yml exists but has no sbom_retention key — policy must disable.
        case_dir, sboms_dir = self._prepare("no-sbom-retention-section",
                                            "some_other_key: value\n")
        app_dir = sboms_dir / "app-a"
        app_dir.mkdir()
        TestHelpers.create_file(app_dir / "app-a-1.0.sbom.json", size=100)

        with caplog.at_level(logging.INFO, logger="envgene"):
            sboms_retention_policy()

        assert "disabled" in caplog.text.lower(), \
            f"expected 'disabled' log; got:\n{caplog.text}"
        assert len(_files(app_dir)) == 1, \
            f"files must be untouched when section is absent;\n{_dump_dir(app_dir)}"

    def test_enabled_without_keep_versions_skips_per_app_pruning(self, caplog):
        # keep_versions_per_app is optional — per-app pruning must be skipped.
        case_dir, sboms_dir = self._prepare("enabled-no-keep-versions",
                                            "sbom_retention:\n  enabled: true\n")
        app_dir = sboms_dir / "app-a"
        app_dir.mkdir()
        for i in range(5):
            TestHelpers.create_file(app_dir / f"app-a-{i}.sbom.json", size=100)

        with caplog.at_level(logging.INFO, logger="envgene"):
            sboms_retention_policy()

        assert len(_files(app_dir)) == 5, \
            f"all files must survive when keep_versions_per_app is absent;\n{_dump_dir(app_dir)}"

    def test_keep_versions_zero_raises_validation_error(self):
        # keep_versions_per_app: 0 is invalid (gt=0 constraint) — must raise ValidationError.
        case_dir, sboms_dir = self._prepare("keep-versions-zero",
                                            "sbom_retention:\n  enabled: true\n  keep_versions_per_app: 0\n")
        app_dir = sboms_dir / "app-a"
        app_dir.mkdir()
        for i in range(3):
            TestHelpers.create_file(app_dir / f"app-a-{i}.sbom.json", size=100)

        with pytest.raises(ValidationError):
            sboms_retention_policy()


class TestSbomRetentionEdgeCases(BaseTest):
    """Edge cases and boundary conditions for sboms_retention_policy."""

    def setup_method(self):
        self.feature_dir = self.output_dir / FEATURE_TEST_DIR / "edge_cases"
        self.feature_dir.mkdir(parents=True, exist_ok=True)

    def _prepare(self, case_name: str, config_content: str) -> tuple[Path, Path]:
        case_dir = self.feature_dir / case_name
        if case_dir.exists():
            shutil.rmtree(case_dir)
        case_dir.mkdir(parents=True)
        _write(case_dir / "configuration" / "config.yml", config_content)
        self.set_ci_project_dir(case_dir)
        sboms_dir = case_dir / "sboms"
        sboms_dir.mkdir()
        return case_dir, sboms_dir

    def test_size_exactly_at_limit_does_not_trigger_size_cleanup(self, caplog):
        # is_over_size_limit uses strict `>` — exactly at limit must NOT trigger cleanup.
        from envgenehelper.constants import CI_JOB_ARTIFACT_MAX_SIZE_MB
        case_dir, sboms_dir = self._prepare(
            "size-at-limit",
            "sbom_retention:\n  enabled: true\n  keep_versions_per_app: 10\n")
        app_dir = sboms_dir / "app-a"
        app_dir.mkdir()
        exact_bytes = CI_JOB_ARTIFACT_MAX_SIZE_MB * 1024 * 1024
        TestHelpers.create_file(app_dir / "app-a-1.0.sbom.json", size=exact_bytes)

        with caplog.at_level(logging.INFO, logger="envgene"):
            sboms_retention_policy()

        assert len(_files(app_dir)) == 1, \
            f"file at exact size limit must not be deleted;\n{_dump_dir(app_dir)}"
        assert "exceeds size limit" not in caplog.text, \
            "size limit cleanup must not run when size == limit"

    def test_empty_app_subdir_does_not_raise(self):
        # cleanup_dir_by_age on an empty directory must exit cleanly.
        case_dir, sboms_dir = self._prepare(
            "empty-app-dir",
            "sbom_retention:\n  enabled: true\n  keep_versions_per_app: 3\n")
        app_dir = sboms_dir / "app-a"
        app_dir.mkdir()

        sboms_retention_policy()

        assert _files(app_dir) == [], \
            f"empty app dir must remain empty;\n{_dump_dir(app_dir)}"

    def test_app_subdir_with_only_subdirectories_not_deleted(self):
        # cleanup_dir_by_age filters with is_file() — nested subdirs must survive.
        case_dir, sboms_dir = self._prepare(
            "app-dir-with-subdirs",
            "sbom_retention:\n  enabled: true\n  keep_versions_per_app: 1\n")
        app_dir = sboms_dir / "app-a"
        app_dir.mkdir()
        nested = app_dir / "nested-dir"
        nested.mkdir()
        now = time.time()
        TestHelpers.create_file(app_dir / "app-a-1.0.sbom.json", size=100, mtime=now)
        TestHelpers.create_file(app_dir / "app-a-2.0.sbom.json", size=100, mtime=now + 1)

        sboms_retention_policy()

        assert nested.exists(), \
            f"nested subdirectory must not be deleted by cleanup;\n{_dump_dir(app_dir)}"
        assert len(_files(app_dir)) == 1, \
            f"only 1 file must remain per keep_versions_per_app=1;\n{_dump_dir(app_dir)}"
