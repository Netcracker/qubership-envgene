import copy
import shutil
from pathlib import Path

import pytest

from build_env.env_template.set_template_version import update_version
from envgene_shared.utils.yaml_utils import readYaml, writeYamlToFile
from envgenehelper.business_helper import NamespaceRole, parse_bg_ns_target
from envgenehelper.models import TemplateVersionUpdateMode
from scripts.tests.base_test import BaseTest

INVENTORY = "Inventory"
ENV_DEFINITION = "env_definition.yml"
INITIAL_ENV_DEFINITION = {
    "envTemplate": {
        "artifact": "bgd:v1.0.0",
        "bgNsArtifacts": {
            "origin": "bgd:v1.1.0-origin",
            "peer": "bgd:v1.0.0-peer",
        },
    },
    "generatedVersions": {
        "generateEnvironmentLatestVersion": "bgd:v1.0.0",
    },
}


@pytest.fixture
def bgd_env_dir():
    work_root = BaseTest.output_dir / "set_template_version"
    env_dir = work_root / "environments" / "bgd-cluster" / "bgd-env"
    shutil.rmtree(work_root, ignore_errors=True)
    inventory_dir = env_dir / INVENTORY
    inventory_dir.mkdir(parents=True)
    writeYamlToFile(inventory_dir / ENV_DEFINITION, INITIAL_ENV_DEFINITION)
    yield env_dir
    shutil.rmtree(work_root, ignore_errors=True)


def _read_inventory(env_dir: Path) -> dict:
    return readYaml(env_dir / INVENTORY / ENV_DEFINITION, safe_load=True)


def _snapshot_inventory(env_dir: Path) -> dict:
    return copy.deepcopy(_read_inventory(env_dir))


@pytest.mark.unit
class TestSetTemplateVersionBgNsTarget:
    def test_persistent_without_bg_ns_target_updates_artifact_only(self, bgd_env_dir: Path):
        before = _snapshot_inventory(bgd_env_dir)
        update_version(
            bgd_env_dir,
            "tpl:v2",
            TemplateVersionUpdateMode.PERSISTENT,
            bg_ns_target=None,
        )
        after = _read_inventory(bgd_env_dir)

        assert after["envTemplate"]["artifact"] == "tpl:v2"
        assert after["envTemplate"]["bgNsArtifacts"]["origin"] == before["envTemplate"]["bgNsArtifacts"]["origin"]
        assert after["envTemplate"]["bgNsArtifacts"]["peer"] == before["envTemplate"]["bgNsArtifacts"]["peer"]

    def test_persistent_peer_updates_peer_only(self, bgd_env_dir: Path):
        before = _snapshot_inventory(bgd_env_dir)
        update_version(
            bgd_env_dir,
            "tpl:v9",
            TemplateVersionUpdateMode.PERSISTENT,
            bg_ns_target=NamespaceRole.PEER,
        )
        after = _read_inventory(bgd_env_dir)

        assert after["envTemplate"]["bgNsArtifacts"]["peer"] == "tpl:v9"
        assert after["envTemplate"]["artifact"] == before["envTemplate"]["artifact"]
        assert after["envTemplate"]["bgNsArtifacts"]["origin"] == before["envTemplate"]["bgNsArtifacts"]["origin"]

    def test_persistent_origin_updates_origin_only(self, bgd_env_dir: Path):
        before = _snapshot_inventory(bgd_env_dir)
        update_version(
            bgd_env_dir,
            "tpl:v8",
            TemplateVersionUpdateMode.PERSISTENT,
            bg_ns_target=NamespaceRole.ORIGIN,
        )
        after = _read_inventory(bgd_env_dir)

        assert after["envTemplate"]["bgNsArtifacts"]["origin"] == "tpl:v8"
        assert after["envTemplate"]["artifact"] == before["envTemplate"]["artifact"]
        assert after["envTemplate"]["bgNsArtifacts"]["peer"] == before["envTemplate"]["bgNsArtifacts"]["peer"]

    def test_persistent_peer_creates_bg_ns_artifacts_when_missing(self, bgd_env_dir: Path):
        inventory_path = bgd_env_dir / INVENTORY / ENV_DEFINITION
        inventory = _read_inventory(bgd_env_dir)
        del inventory["envTemplate"]["bgNsArtifacts"]
        writeYamlToFile(inventory_path, inventory)
        before_artifact = inventory["envTemplate"]["artifact"]

        update_version(
            bgd_env_dir,
            "tpl:v3",
            TemplateVersionUpdateMode.PERSISTENT,
            bg_ns_target=NamespaceRole.PEER,
        )
        after = _read_inventory(bgd_env_dir)

        assert after["envTemplate"]["artifact"] == before_artifact
        assert after["envTemplate"]["bgNsArtifacts"] == {"peer": "tpl:v3"}

    def test_temporary_leaves_env_template_fields_and_writes_generated_version(self, bgd_env_dir: Path):
        before = _snapshot_inventory(bgd_env_dir)
        update_version(
            bgd_env_dir,
            "tpl:tmp",
            TemplateVersionUpdateMode.TEMPORARY,
            bg_ns_target=NamespaceRole.PEER,
        )
        after = _read_inventory(bgd_env_dir)

        assert after["envTemplate"]["artifact"] == before["envTemplate"]["artifact"]
        assert after["envTemplate"]["bgNsArtifacts"] == before["envTemplate"]["bgNsArtifacts"]
        assert after["generatedVersions"]["generateEnvironmentLatestVersion"] == "tpl:tmp"

    def test_invalid_bg_ns_target_fails(self):
        with pytest.raises(ValueError, match="BG_NS_TARGET must be 'origin' or 'peer'"):
            parse_bg_ns_target("candidate")
