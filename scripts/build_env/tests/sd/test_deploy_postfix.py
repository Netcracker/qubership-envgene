import json
import logging
import os
from pathlib import Path

import pytest

from envgenehelper.env_helper import Environment
from envgenehelper.test_helpers import TestHelpers
from scripts.build_env.tests.base_test import BaseTest

os.environ.setdefault("ENVIRONMENT_NAME", "env-01")
os.environ.setdefault("CLUSTER_NAME", "cluster-01")
os.environ.setdefault("CI_PROJECT_DIR", "/tmp")
os.environ.setdefault("FULL_ENV_NAME", "cluster-01/env-01")

from process_sd import handle_sd

FEATURE_TEST_DIR = "test_handle_deploy_postfix"
CLUSTER = "cluster-01"
ENV_NAME = "env-01"
FULL_ENV_NAME = f"{CLUSTER}/{ENV_NAME}"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _write_namespace(env: Environment, folder_name: str, logical_name: str) -> None:
    ns_path = Path(env.env_path) / "Namespaces" / folder_name / "namespace.yml"
    _write(ns_path, f"name: {logical_name}\n")


def _sd_json(applications: list, user_data: dict | None = None) -> str:
    sd = {"version": 1, "type": "solutionDeploy", "applications": applications}
    if user_data is not None:
        sd["userData"] = user_data
    return json.dumps([sd])


def _read_sd(env: Environment) -> dict:
    from envgenehelper import openYaml
    sd_path = Path(env.env_path) / "Inventory" / "solution-descriptor" / "sd.yaml"
    return openYaml(sd_path)


class TestHandleDeployPostfixPositive(BaseTest):
    """
    UC-CC-DP-1..2 positive paths exercised through handle_sd().
    Namespace fixtures and SD data are created programmatically — no filesystem fixtures required.
    """

    def setup_method(self):
        self.feature_dir = self.output_dir / FEATURE_TEST_DIR
        TestHelpers.clean_test_dir(self.feature_dir)
        os.environ["CLUSTER_NAME"] = CLUSTER
        os.environ["ENVIRONMENT_NAME"] = ENV_NAME
        os.environ["FULL_ENV_NAME"] = FULL_ENV_NAME
        self.set_ci_project_dir(self.feature_dir)

    def _prepare(self) -> Environment:
        return Environment(str(self.feature_dir), CLUSTER, ENV_NAME)

    # ------------------------------------------------------------------
    # TC-DP-001: UC-CC-DP-1 — exact match: logical name → folder name
    # ------------------------------------------------------------------

    def test_tc_dp_001_exact_match_postfix_replaced(self):
        # UC-CC-DP-1: deployPostfix "core-namespace" == namespace logical name → replaced
        # with folder name "core". userData removed because only useDeployPostfixAsNamespace present.
        env = self._prepare()
        _write_namespace(env, "core", "core-namespace")
        sd_data = _sd_json(
            applications=[{"version": "core-app:1.0", "deployPostfix": "core-namespace"}],
            user_data={"useDeployPostfixAsNamespace": True},
        )

        handle_sd(env, "json", "", sd_data, "", "basic-merge")

        result = _read_sd(env)
        apps = result["applications"]
        assert len(apps) == 1
        assert apps[0]["version"] == "core-app:1.0"
        assert apps[0]["deployPostfix"] == "core"
        assert "userData" not in result

    # ------------------------------------------------------------------
    # TC-DP-002: UC-CC-DP-2 — BG Domain: origin and peer namespaces both replaced
    # ------------------------------------------------------------------

    def test_tc_dp_002_bg_domain_origin_and_peer_replaced(self):
        # UC-CC-DP-2: SD has two apps — one for origin, one for peer. Both deployPostfixes
        # match their logical names (folder name == logical name for BG domain namespaces).
        env = self._prepare()
        _write_namespace(env, "bss-origin", "bss-origin")
        _write_namespace(env, "bss-peer", "bss-peer")
        sd_data = _sd_json(
            applications=[
                {"version": "origin-app:1.0", "deployPostfix": "bss-origin"},
                {"version": "peer-app:1.0", "deployPostfix": "bss-peer"},
            ],
            user_data={"useDeployPostfixAsNamespace": True},
        )

        handle_sd(env, "json", "", sd_data, "", "basic-merge")

        result = _read_sd(env)
        apps = result["applications"]
        assert len(apps) == 2
        versions = {a["version"] for a in apps}
        postfixes = {a["deployPostfix"] for a in apps}
        assert versions == {"origin-app:1.0", "peer-app:1.0"}
        assert postfixes == {"bss-origin", "bss-peer"}
        assert "userData" not in result

    # ------------------------------------------------------------------
    # TC-DP-003: UC-CC-DP-1 — multiple namespaces, all replaced
    # ------------------------------------------------------------------

    def test_tc_dp_003_multiple_namespaces_all_replaced(self):
        # UC-CC-DP-1: two apps with distinct deployPostfixes — each maps to its folder name.
        env = self._prepare()
        _write_namespace(env, "core", "core-namespace")
        _write_namespace(env, "bss", "bss-namespace")
        sd_data = _sd_json(
            applications=[
                {"version": "core-app:1.0", "deployPostfix": "core-namespace"},
                {"version": "bss-app:1.0", "deployPostfix": "bss-namespace"},
            ],
            user_data={"useDeployPostfixAsNamespace": True},
        )

        handle_sd(env, "json", "", sd_data, "", "basic-merge")

        result = _read_sd(env)
        apps = result["applications"]
        assert len(apps) == 2
        postfix_map = {a["version"]: a["deployPostfix"] for a in apps}
        assert postfix_map["core-app:1.0"] == "core"
        assert postfix_map["bss-app:1.0"] == "bss"
        assert "userData" not in result

    # ------------------------------------------------------------------
    # TC-DP-004: flag absent — SD passes through unchanged
    # ------------------------------------------------------------------

    def test_tc_dp_004_no_flag_sd_unchanged(self):
        # Backward compat: without useDeployPostfixAsNamespace the deployPostfix values
        # must reach the output sd.yaml exactly as provided.
        env = self._prepare()
        _write_namespace(env, "core", "core-namespace")
        sd_data = _sd_json(
            applications=[{"version": "core-app:1.0", "deployPostfix": "core-namespace"}],
        )

        handle_sd(env, "json", "", sd_data, "", "basic-merge")

        result = _read_sd(env)
        apps = result["applications"]
        assert len(apps) == 1
        assert apps[0]["version"] == "core-app:1.0"
        assert apps[0]["deployPostfix"] == "core-namespace"


class TestHandleDeployPostfixNegative(BaseTest):
    """
    UC-CC-DP-3 / UC-CC-DP-4 negative paths: handle_sd() must call exit(1) when
    deployPostfix cannot be matched to any namespace in the environment.
    """

    def setup_method(self):
        self.feature_dir = self.output_dir / FEATURE_TEST_DIR / "negative"
        TestHelpers.clean_test_dir(self.feature_dir)
        os.environ["CLUSTER_NAME"] = CLUSTER
        os.environ["ENVIRONMENT_NAME"] = ENV_NAME
        os.environ["FULL_ENV_NAME"] = FULL_ENV_NAME
        self.set_ci_project_dir(self.feature_dir)

    def _prepare(self) -> Environment:
        return Environment(str(self.feature_dir), CLUSTER, ENV_NAME)

    def _sd_data_with_postfix(self, postfix: str) -> str:
        return json.dumps([{
            "version": 1,
            "type": "solutionDeploy",
            "applications": [{"version": "app:1.0", "deployPostfix": postfix}],
            "userData": {"useDeployPostfixAsNamespace": True},
        }])

    # ------------------------------------------------------------------
    # UC-CC-DP-3: no exact match → exit(1)
    # ------------------------------------------------------------------

    def test_unknown_postfix_exits_with_code_1(self, caplog):
        # UC-CC-DP-3: deployPostfix "unknown-namespace" does not match any namespace
        # logical name → handle_sd must call exit(1).
        env = self._prepare()
        _write_namespace(env, "core", "core-namespace")
        sd_data = self._sd_data_with_postfix("unknown-namespace")

        with caplog.at_level(logging.ERROR, logger="envgene"):
            with pytest.raises(SystemExit) as exc_info:
                handle_sd(env, "json", "", sd_data, "", "basic-merge")

        assert exc_info.value.code == 1
        assert "No replacement found" in caplog.text
        assert "unknown-namespace" in caplog.text

    def test_case_mismatch_postfix_exits_with_code_1(self, caplog):
        # UC-CC-DP-3: matching is case-sensitive — "Core-Namespace" ≠ "core-namespace".
        env = self._prepare()
        _write_namespace(env, "core", "core-namespace")
        sd_data = self._sd_data_with_postfix("Core-Namespace")

        with caplog.at_level(logging.ERROR, logger="envgene"):
            with pytest.raises(SystemExit) as exc_info:
                handle_sd(env, "json", "", sd_data, "", "basic-merge")

        assert exc_info.value.code == 1

    # ------------------------------------------------------------------
    # UC-CC-DP-4: BG domain namespaces present but wrong postfix used → exit(1)
    # ------------------------------------------------------------------

    def test_bg_base_name_without_suffix_exits_with_code_1(self, caplog):
        # UC-CC-DP-4: only "bss-origin" and "bss-peer" exist; SD uses bare "bss" → no match.
        env = self._prepare()
        _write_namespace(env, "bss-origin", "bss-origin")
        _write_namespace(env, "bss-peer", "bss-peer")
        sd_data = json.dumps([{
            "version": 1,
            "type": "solutionDeploy",
            "applications": [{"version": "bss-app:1.0", "deployPostfix": "bss"}],
            "userData": {"useDeployPostfixAsNamespace": True},
        }])

        with caplog.at_level(logging.ERROR, logger="envgene"):
            with pytest.raises(SystemExit) as exc_info:
                handle_sd(env, "json", "", sd_data, "", "basic-merge")

        assert exc_info.value.code == 1

    def test_missing_peer_side_exits_with_code_1(self, caplog):
        # UC-CC-DP-4: "bss-peer" namespace does not exist; SD references it → exit(1).
        env = self._prepare()
        _write_namespace(env, "core", "core-namespace")  # only "core" namespace exists
        sd_data = json.dumps([{
            "version": 1,
            "type": "solutionDeploy",
            "applications": [{"version": "peer-app:1.0", "deployPostfix": "bss-peer"}],
            "userData": {"useDeployPostfixAsNamespace": True},
        }])

        with caplog.at_level(logging.ERROR, logger="envgene"):
            with pytest.raises(SystemExit):
                handle_sd(env, "json", "", sd_data, "", "basic-merge")
