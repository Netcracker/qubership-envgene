from pathlib import Path

from envgenehelper import openYaml, open_current_env_instance_store
from scripts.build_env.render_config_env import EnvGenerator


TEST_DATA_DIR = (
    Path(__file__).resolve().parents[3]
    / "test_data"
    / "test_environments"
    / "composite-topology"
)


class TestCompositeTopology:

    def _compute_composite_topology(self, test_dir):
        generator = EnvGenerator()
        generator.ctx.current_env_dir = str(test_dir)
        generator.ctx.current_env = {}
        with open_current_env_instance_store(test_dir) as env_instance_store:
            for object_path in test_dir.glob("*.yml"):
                env_instance_store.put(object_path, openYaml(object_path))
            generator.compute_composite_topology()
        return generator.ctx.current_env["composite_topology"]

    def test_no_composite_structure(self, tmp_path):
        assert self._compute_composite_topology(tmp_path) == {}

    def test_baseline_only(self):
        test_dir = TEST_DATA_DIR / "baseline-only"
        assert self._compute_composite_topology(test_dir) == {
            "baseline": {
                "originNamespace": "env-1-core",
            }
        }

    def test_namespace_baseline_and_satellites(self):
        test_dir = TEST_DATA_DIR / "namespace-baseline-satellites"
        assert self._compute_composite_topology(test_dir) == {
            "baseline": {
                "originNamespace": "env-1-core",
            },
            "satellites": [
                {
                    "originNamespace": "env-1-oss",
                },
                {
                    "originNamespace": "env-1-bss",
                },
            ],
        }

    def test_bgdomain_baseline(self):
        test_dir = TEST_DATA_DIR / "bgdomain-baseline"
        assert self._compute_composite_topology(test_dir) == {
            "baseline": {
                "originNamespace": "env-1-bss-origin",
                "peerNamespace": "env-1-bss-peer",
                "controllerNamespace": "env-1-controller",
            },
             "satellites": [
                            {
                                "originNamespace": "env-1-data-management",
                            }
                        ],
        }

    def test_bgdomain_satellite(self):
        test_dir = TEST_DATA_DIR / "bgdomain-satellite"
        assert self._compute_composite_topology(test_dir) == {
            "baseline": {
                "originNamespace": "env-1-core",
            },
            "satellites": [
                {
                    "originNamespace": "env-1-bss-origin",
                    "peerNamespace": "env-1-bss-peer",
                    "controllerNamespace": "env-1-controller",
                }
            ],
        }

    def test_bgdomain_baseline_and_satellites(self):
        test_dir = TEST_DATA_DIR / "bgdomain-baseline-satellites"
        assert self._compute_composite_topology(test_dir) == {
            "baseline": {
                "originNamespace": "env-1-bss-origin",
                "peerNamespace": "env-1-bss-peer",
                "controllerNamespace": "env-1-controller",
            },
            "satellites": [
                {
                    "originNamespace": "env-1-bss-origin",
                    "peerNamespace": "env-1-bss-peer",
                    "controllerNamespace": "env-1-controller",
                }
            ],
        }
