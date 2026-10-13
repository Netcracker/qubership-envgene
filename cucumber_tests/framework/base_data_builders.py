import os
import time
import yaml
from abc import ABC, abstractmethod
from pathlib import Path


class BaseDataBuilder(ABC):
    """Abstract data builder with shared implementations.

    Methods that are identical across all projects (SBOM file creation,
    BG state management) are implemented here. Project-specific methods
    (artifact definitions, template descriptors) remain abstract or are
    added in concrete subclasses.
    """

    def __init__(self, workspace):
        self.workspace = workspace

    # --- Abstract methods: must be implemented by each project ---

    @abstractmethod
    def get_env_dir(self, cluster_name: str, env_name: str) -> Path:
        """Returns the physical environment directory for a specific cluster and env."""
        ...

    @abstractmethod
    def create_inventory_file(self, cluster_name: str, env_name: str, content: dict):
        """Creates env_definition.yml for a given environment."""
        ...

    # --- Concrete implementations: common to all projects ---

    @property
    def env_dir(self):
        """Returns the physical environment directory for the default test cluster/env."""
        return self.get_env_dir("test-cluster", "test-env")

    def create_mock_sboms(self, app_name: str, count: int, size_mb: float = 0):
        """Creates dummy SBOM files with different modification times.
        Optionally generates a sparse file to simulate large total size instantly."""
        app_dir = self.workspace.sboms_dir / app_name
        app_dir.mkdir(parents=True, exist_ok=True)

        base_time = time.time() - (count * 100)
        for i in range(count):
            file_path = app_dir / f"{app_name}-v{i}.sbom.json"

            if i == 0 and size_mb > 0:
                with open(file_path, "wb") as f:
                    f.seek(int(size_mb * 1024 * 1024) - 1)
                    f.write(b"\0")
            else:
                file_path.touch()

            mod_time = base_time + (i * 100)
            os.utime(file_path, (mod_time, mod_time))

    def modify_first_sbom_size(self, app_name: str, size_mb: float):
        """Finds the first generated SBOM and inflates it via sparse generation."""
        app_dir = self.workspace.sboms_dir / app_name
        target_file = list(app_dir.glob("*.sbom.json"))[0]

        with open(target_file, "r+b") as f:
            f.seek(int(size_mb * 1024 * 1024) - 1)
            f.write(b"\0")

    def set_bg_state_files(self, origin_state: str = None, peer_state: str = None, cluster: str = "test-cluster", env: str = "test-env"):
        """Creates physical state files (.origin-X, .peer-Y) in the environment directory."""
        env_dir = self.get_env_dir(cluster, env)
        if origin_state:
            (env_dir / f".origin-{origin_state}").touch()
        if peer_state:
            (env_dir / f".peer-{peer_state}").touch()

    def create_bg_namespaces(self, origin_ns: str, peer_ns: str, different_content: bool = False, cluster: str = "test-cluster", env: str = "test-env"):
        """Generates namespace folders and definition files for BG copy operations."""
        env_dir = self.get_env_dir(cluster, env)
        ns_dir = env_dir / "Namespaces"
        origin_dir = ns_dir / origin_ns
        peer_dir = ns_dir / peer_ns

        origin_dir.mkdir(parents=True, exist_ok=True)
        peer_dir.mkdir(parents=True, exist_ok=True)

        with open(origin_dir / "namespace.yml", "w") as f:
            yaml.dump({"name": origin_ns}, f)
        with open(peer_dir / "namespace.yml", "w") as f:
            yaml.dump({"name": peer_ns}, f)

        if different_content:
            with open(origin_dir / "manifest.yaml", "w") as f:
                f.write("content: origin-data")
            with open(peer_dir / "manifest.yaml", "w") as f:
                f.write("content: peer-data")
