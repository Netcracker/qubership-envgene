import os
import shutil
import sys
from pathlib import Path

from scripts.build_env.tests.base_test import BaseTest

os.environ.setdefault("ENVIRONMENT_NAME", "env-01")
os.environ.setdefault("CLUSTER_NAME", "cluster-01")

_ESE_SCRIPTS = Path(__file__).resolve().parents[4] / "build_effective_set_generator" / "scripts"
if str(_ESE_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_ESE_SCRIPTS))

import effective_set_entrypoint as _ese
from effective_set_entrypoint import _run_forward_merge, _run_reverse_merge
from envgenehelper.effective_set_helper import ES_MAPPING_FILE, ESGenerationContext
from envgenehelper.yaml_helper import openYaml

FEATURE_TEST_DIR = "test_mapping_consistency"

_CONTEXTS = ("deployment", "runtime", "cleanup")


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _mapping_str(entries: dict) -> str:
    return "".join(f"{k}: {v}\n" for k, v in entries.items())


def _mapping_path(es_dir: Path, ctx: str) -> Path:
    return es_dir / ctx / ES_MAPPING_FILE


def _write_all_mappings(es_dir: Path, deployment_entries: dict) -> None:
    """Write matching deployment/runtime/cleanup mapping.yaml files from a deployment-keyed dict."""
    for ctx in _CONTEXTS:
        entries = {k: v.replace("/deployment/", f"/{ctx}/") for k, v in deployment_entries.items()}
        _write(_mapping_path(es_dir, ctx), _mapping_str(entries))


def _read_mapping(es_dir: Path, ctx: str) -> dict:
    return dict(openYaml(_mapping_path(es_dir, ctx)))


def _es_dir(base: Path) -> Path:
    es = base / "effective-set"
    for ctx in _CONTEXTS:
        (es / ctx).mkdir(parents=True, exist_ok=True)
    return es


# ---------------------------------------------------------------------------
# UC-ES-RUN-3 / UC-ES-CLN-3: reverse-merge removes key from all three mappings
# ---------------------------------------------------------------------------

class TestMappingConsistencyOnReverseMerge(BaseTest):
    """
    UC-ES-RUN-3 / UC-ES-CLN-3 — when a namespace is removed during partial reverse
    merge, _run_reverse_merge removes its key from deployment, runtime, and cleanup
    mapping.yaml in a single pass, preserving cross-context key alignment.

    Note — UC-ES-DEP-A14 (initial full-generation of mapping.yaml): the files are
    written entirely by the Java Calculator.  End-to-end verification lives in
    CmdbCliTest.java (build_effective_set_generator/effective-set-generator/
    src/test/java/.../CmdbCliTest.java).
    """

    def setup_method(self):
        self.feature_dir = self.output_dir / FEATURE_TEST_DIR / "reverse"
        if self.feature_dir.exists():
            shutil.rmtree(self.feature_dir)
        self.feature_dir.mkdir(parents=True)

    def test_deleted_namespace_key_removed_from_all_three_mappings(self):
        # UC-ES-RUN-3 / UC-ES-CLN-3: "pg" absent from full SD →
        # "pl-01-pg" removed from deployment, runtime, and cleanup mapping.yaml;
        # "pl-01-monitoring" preserved in all three.
        # Key matching is substring-based: deployPostfix "pg" ⊂ "pl-01-pg".
        es_dir = _es_dir(self.feature_dir)
        _write_all_mappings(es_dir, {
            "pl-01-pg": "/environments/cluster-01/pl-01/effective-set/deployment/pg",
            "pl-01-monitoring": "/environments/cluster-01/pl-01/effective-set/deployment/monitoring-origin",
        })
        sd_path = self.feature_dir / "sd.yaml"
        _write(sd_path,
               "version: 2.1\ntype: deploy\napplications:\n"
               "  - version: 'MONITORING:0.91.0'\n    deployPostfix: monitoring\n")
        delta_sd_path = self.feature_dir / "delta_sd.yaml"
        _write(delta_sd_path,
               "version: 2.1\ntype: deploy\napplications:\n"
               "  - version: 'postgres:1.0'\n    deployPostfix: pg\n")

        _run_reverse_merge(es_dir, delta_sd_path, sd_path)

        for ctx in _CONTEXTS:
            mapping = _read_mapping(es_dir, ctx)
            assert "pl-01-pg" not in mapping, (
                f"pl-01-pg must be removed from {ctx}/mapping.yaml after reverse merge"
            )
            assert "pl-01-monitoring" in mapping, (
                f"pl-01-monitoring must be preserved in {ctx}/mapping.yaml"
            )

    def test_namespace_key_preserved_when_still_in_full_sd(self):
        # UC-ES-RUN-3: deployPostfix "pg" IS in full SD → key must NOT be removed
        # from any mapping file (dp in sd_postfixes guard).
        es_dir = _es_dir(self.feature_dir / "keep")
        _write_all_mappings(es_dir, {
            "pl-01-pg": "/environments/cluster-01/pl-01/effective-set/deployment/pg",
        })
        sd_path = self.feature_dir / "sd_keep.yaml"
        _write(sd_path,
               "version: 2.1\ntype: deploy\napplications:\n"
               "  - version: 'postgres:1.0'\n    deployPostfix: pg\n")
        delta_sd_path = self.feature_dir / "delta_keep.yaml"
        _write(delta_sd_path,
               "version: 2.1\ntype: deploy\napplications:\n"
               "  - version: 'postgres:1.0'\n    deployPostfix: pg\n")

        _run_reverse_merge(es_dir, delta_sd_path, sd_path)

        for ctx in _CONTEXTS:
            mapping = _read_mapping(es_dir, ctx)
            assert "pl-01-pg" in mapping, (
                f"pl-01-pg must survive in {ctx}/mapping.yaml when dp still in full SD"
            )

    def test_missing_mapping_file_does_not_raise(self):
        # UC-ES-RUN-3: absent mapping.yaml is skipped with a warning — no exception.
        # Only deployment and runtime files present; cleanup/mapping.yaml is absent.
        es_dir = _es_dir(self.feature_dir / "missing")
        for ctx in ("deployment", "runtime"):
            _write(_mapping_path(es_dir, ctx),
                   "pl-01-pg: /environments/cluster-01/pl-01/effective-set/deployment/pg\n")
        sd_path = self.feature_dir / "sd_missing.yaml"
        _write(sd_path, "version: 2.1\ntype: deploy\napplications: []\n")
        delta_sd_path = self.feature_dir / "delta_missing.yaml"
        _write(delta_sd_path,
               "version: 2.1\ntype: deploy\napplications:\n"
               "  - version: 'postgres:1.0'\n    deployPostfix: pg\n")

        _run_reverse_merge(es_dir, delta_sd_path, sd_path)  # must not raise


# ---------------------------------------------------------------------------
# UC-ES-DEP-A14 / UC-ES-RUN-3 / UC-ES-CLN-3: forward-merge preserves old entries
# ---------------------------------------------------------------------------

class TestMappingConsistencyOnForwardMerge(BaseTest):
    """
    UC-ES-DEP-A14 / UC-ES-RUN-3 / UC-ES-CLN-3 — during partial forward merge,
    _run_forward_merge reads existing mapping entries before the CLI run, then
    merges them with the new entries written by the Java Calculator, so namespaces
    from previous runs are preserved across all three context mapping files.
    """

    def setup_method(self):
        self.feature_dir = self.output_dir / FEATURE_TEST_DIR / "forward"
        if self.feature_dir.exists():
            shutil.rmtree(self.feature_dir)
        self.feature_dir.mkdir(parents=True)
        for var in ("EFFECTIVE_SET_CONFIG", "DEPLOYMENT_SESSION_ID", "CUSTOM_PARAMS"):
            os.environ.pop(var, None)

    def teardown_method(self):
        for var in ("EFFECTIVE_SET_CONFIG", "DEPLOYMENT_SESSION_ID", "CUSTOM_PARAMS"):
            os.environ.pop(var, None)

    def test_old_and_new_entries_both_present_in_all_three_mappings_after_forward_merge(
            self, monkeypatch):
        # UC-ES-DEP-A14 / UC-ES-RUN-3 / UC-ES-CLN-3:
        # - old entry (pre-existing namespace, not in current delta SD) is preserved.
        # - new entry (written by Java CLI for the delta namespace) is added.
        # Both keys appear in deployment, runtime, and cleanup mapping.yaml.
        OLD = {"pl-01-old": "/environments/cluster-01/pl-01/effective-set/deployment/old"}
        NEW = {"pl-01-new": "/environments/cluster-01/pl-01/effective-set/deployment/new"}

        es_dir = _es_dir(self.feature_dir)
        _write_all_mappings(es_dir, OLD)

        def fake_run(cmd, shell=True, check=True):
            # Simulate Java CLI overwriting mapping files with new-namespace entries only.
            _write_all_mappings(es_dir, NEW)

        monkeypatch.setattr(_ese.subprocess, "run", fake_run)

        delta_sd_path = self.feature_dir / "delta_fwd.yaml"
        _write(delta_sd_path,
               "version: 2.1\ntype: deploy\napplications:\n"
               "  - version: 'new-app:1.0'\n    deployPostfix: new\n")

        _run_forward_merge(es_dir, "cluster-01/env-01", delta_sd_path)

        for ctx in _CONTEXTS:
            mapping = _read_mapping(es_dir, ctx)
            assert "pl-01-old" in mapping, (
                f"pre-existing key pl-01-old must survive in {ctx}/mapping.yaml after forward merge"
            )
            assert "pl-01-new" in mapping, (
                f"new key pl-01-new from CLI run must appear in {ctx}/mapping.yaml after forward merge"
            )
