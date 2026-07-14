from .local_client import LocalClient
from .middleware import DataProviderInterface
from pathlib import Path

def get_data_provider(root_dir: Path = None) -> DataProviderInterface:
    return LocalClient(root_dir=root_dir)
