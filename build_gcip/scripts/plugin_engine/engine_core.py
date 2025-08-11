from envgenehelper import logger
from .usecase import PluginUseCase

class PluginEngine:
    def __init__(self, plugins_dir: str, **kwargs) -> None:
        self.plugins_to_invoke = []
        self.modules = PluginUseCase(plugins_dir).discover_plugins(True)
        for module in self.modules:
            registered_plugin = module(**kwargs)
            self.plugins_to_invoke.append(registered_plugin.invoke)

    def run(self, *args, **kwargs):
        results = []
        for plugin_to_invoke in self.plugins_to_invoke:
            results.append(plugin_to_invoke(*args, **kwargs))
        return results
