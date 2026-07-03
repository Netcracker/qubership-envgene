from abc import ABC, abstractmethod
from pathlib import Path
from tests.framework.base_data_builders import BaseDataBuilder
class BaseWorkspace(ABC):
    """Abstract workspace contract for shared BDD step definitions.

    Any project using the envgene BDD test framework must provide
    a concrete implementation of this class. The shared step definitions
    interact with the workspace exclusively through this interface.
    """

    @property
    @abstractmethod
    def base_dir(self) -> Path:
        """Root directory of the test workspace."""
        ...

    @property
    @abstractmethod
    def sboms_dir(self) -> Path:
        """Directory where SBOM files are stored."""
        ...

    @property
    @abstractmethod
    def config_data(self) -> dict:
        """Current configuration data (in-memory representation of config.yml)."""
        ...

    @config_data.setter
    @abstractmethod
    def config_data(self, value: dict):
        ...

    @property
    @abstractmethod
    def stdout(self) -> str:
        """Captured stdout from the last pipeline run."""
        ...

    @property
    @abstractmethod
    def stderr(self) -> str:
        """Captured stderr from the last pipeline run."""
        ...

    @property
    @abstractmethod
    def returncode(self) -> int:
        """Return code from the last pipeline run."""
        ...

    @property
    @abstractmethod
    def builder(self) -> 'BaseDataBuilder':
        """DataBuilder instance for creating test data on disk."""
        ...

    @abstractmethod
    def run_pipeline(self, extra_env: dict = None):
        """Execute the pipeline with optional extra environment variables."""
        ...
