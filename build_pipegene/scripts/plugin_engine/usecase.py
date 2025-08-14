import os
from importlib import import_module
from typing import Any

from envgenehelper import logger

from .engine_contract import IPluginRegistry

def filter_unwanted_directories(name: str) -> bool:
    return not ['__pycache__'].__contains__(name)

def filter_plugins_paths(plugins_package) -> list[str]:
    """
    filters out a list of unwanted directories
    :param plugins_package:
    :return: list of directories
    """
    return list(
        filter(
            filter_unwanted_directories,
            os.listdir(plugins_package)
        )
    )

class PluginUseCase:
    modules: list[type]

    def __init__(self, plugins_dir: str) -> None:
        self.plugins_dir = plugins_dir
        self.modules = list()

    def __check_loaded_plugin_state(self, plugin_module: Any):
        if len(IPluginRegistry.plugin_registries) > 0:
            latest_module = IPluginRegistry.plugin_registries[-1]
            latest_module_name = latest_module.__module__
            current_module_name = plugin_module.__name__
            if current_module_name == latest_module_name:
                logger.info(f'Successfully imported module `{current_module_name}`')
                self.modules.append(latest_module)
            else:
                logger.error(
                    f'Expected to import -> `{current_module_name}` but got -> `{latest_module_name}`'
                )
            # clear plugins from the registry when we're done with them
            IPluginRegistry.plugin_registries.clear()
        else:
            logger.error(f'No plugin found in registry for module: {plugin_module}')

    def __search_for_plugins_in(self, plugins_path: list[str], package_name: str):
        for directory in plugins_path:
            # Importing the module will cause IPluginRegistry to invoke it's __init__ fun
            import_target_module = f'.{directory}.main'
            module = import_module(import_target_module, package_name)
            self.__check_loaded_plugin_state(module)

    def discover_plugins(self, reload: bool):
        """
        Discover the plugin classes contained in Python files, given a
        list of directory names to scan.
        """
        if not reload:
            return self.modules
        self.modules.clear()
        IPluginRegistry.plugin_registries.clear()
        logger.info(f'Searching for plugins in {self.plugins_dir}')
        if not os.path.exists(self.plugins_dir):
            logger.info(f"{self.plugins_dir} dir doesn't exist, search for plugins skipped")
            return self.modules
        plugins_paths = filter_plugins_paths(self.plugins_dir)
        plugins_dir_parts = os.path.normpath(self.plugins_dir).split('/')
        cut_off_idx = plugins_dir_parts.index('pipegene_plugins')
        package_name = '.'.join(plugins_dir_parts[cut_off_idx:])
        self.__search_for_plugins_in(plugins_paths, package_name)
        return self.modules

