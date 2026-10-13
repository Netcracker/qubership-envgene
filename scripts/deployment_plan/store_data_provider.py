from dpg.v1.utils.data_provider.local_client import LocalClient
from envgenehelper import current_env_instance_store


class StoreDataProvider(LocalClient):
    def _load_app_def(self, application: str) -> dict:
        return current_env_instance_store().get_yaml(self.root_dir / "appdefs", application)

    def _load_reg_def(self, registry: str) -> dict:
        return current_env_instance_store().get_yaml(self.root_dir / "regdefs", registry)
