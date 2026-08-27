from pathlib import Path

from scripts.build_env.render_config_env import EnvGenerator


TEST_DATA_DIR = (
    Path(__file__).resolve().parents[4]
    / "test_data"
    / "test_environments"
    / "composite-topology"
)


class TestCompositeTopology:

    def _create_generator(self, test_dir):
        generator = EnvGenerator()
        generator.ctx.current_env_dir = str(test_dir)
        generator.ctx.current_env = {}
        return generator

    def test_no_composite_structure(self, tmp_path):
        generator = self._create_generator(tmp_path)

        generator.compute_composite_topology()

        assert generator.ctx.current_env["composite_topology"] == {}

    def test_baseline_only(self):
        test_dir = TEST_DATA_DIR / "baseline-only"

        generator = self._create_generator(test_dir)

        generator.compute_composite_topology()

        assert generator.ctx.current_env["composite_topology"] == {
            "baseline": {
                "originNamespace": "env-1-core",
            }
        }

    def test_namespace_baseline_and_satellites(self):
        test_dir = TEST_DATA_DIR / "namespace-baseline-satellites"

        generator = self._create_generator(test_dir)

        generator.compute_composite_topology()

        assert generator.ctx.current_env["composite_topology"] == {
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

        generator = self._create_generator(test_dir)

        generator.compute_composite_topology()

        assert generator.ctx.current_env["composite_topology"] == {
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

        generator = self._create_generator(test_dir)

        generator.compute_composite_topology()

        assert generator.ctx.current_env["composite_topology"] == {
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

        generator = self._create_generator(test_dir)

        generator.compute_composite_topology()

        assert generator.ctx.current_env["composite_topology"] == {
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
