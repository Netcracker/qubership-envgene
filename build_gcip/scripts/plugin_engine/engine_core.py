from types import ModuleType

from gcip import Pipeline
from envgenehelper import logger
from .usecase import PluginUseCase

class PluginEngine:
    def __init__(self, plugins_dir: str, params: dict, pipeline_helper: ModuleType, pipeline: Pipeline) -> None:
        self.use_case = PluginUseCase(plugins_dir)
        self.params = params
        self.pipeline_helper = pipeline_helper
        self.pipeline = pipeline

    def start(self) -> None:
        self.__reload_plugins()
        self.__invoke_plugins()

    def __reload_plugins(self) -> None:
        """Reset the list of all plugins and initiate the walk over the main
        provided plugin package to load all available plugins
        """
        self.use_case.discover_plugins(True)

    def __invoke_plugins(self):
        """Apply all of the plugins on the argument supplied to this function
        """
        for module in self.use_case.modules:
            plugin = self.use_case.register_plugin(module=module, params=self.params, pipeline_helper=self.pipeline_helper, pipeline=self.pipeline)
            delegate = self.use_case.hook_plugin(plugin)
            delegate()
