import os
import sys
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

    def __search_for_plugins_in(self, plugins_paths: list[str]):
        plugins_paths.sort()
        for directory in plugins_paths:
            try:
                logger.info(f"Checking plugin dir: {directory}")
                main_py_path = os.path.join(self.plugins_dir, directory, 'main.py')
                logger.info(f"Expected main.py path: {main_py_path}")
                logger.info(f"Exists: {os.path.exists(main_py_path)}")
                plugin_dir_parent = os.path.dirname(self.plugins_dir)
                logger.info(f"plugin_dir_parent: {plugin_dir_parent}")
                logger.info(f"plugins_dir: {self.plugins_dir}")
                logger.info(f"Current sys.path (first 3): {sys.path[:3]} ... total={len(sys.path)}")

                plugins_dir_name = os.path.basename(self.plugins_dir)
                module_name = f"{plugins_dir_name}.{directory}.main"
                logger.info(f"Computed module name: {module_name}")

                # Construct the full path to the main.py file
                if not os.path.exists(main_py_path):
                    logger.warning(f"main.py not found in {directory}, skipping")
                    continue

                # Add the plugin directory to sys.path temporarily
                plugin_dir_parent = os.path.dirname(self.plugins_dir)
                if plugin_dir_parent not in sys.path:
                    sys.path.insert(0, plugin_dir_parent)
                    added_to_path = True
                else:
                    added_to_path = False

                # Create module name from the plugins directory structure
                plugins_dir_name = os.path.basename(self.plugins_dir)
                module_name = f"{plugins_dir_name}.{directory}.main"

                logger.info(f"Attempting to import: {module_name}")
                module = import_module(module_name)
                self.__check_loaded_plugin_state(module)

                # Clean up sys.path if we added to it
                if added_to_path:
                    sys.path.remove(plugin_dir_parent)

            except ImportError as e:
                logger.error(f"Failed to import plugin {directory}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error loading plugin {directory}: {e}")

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
        self.__search_for_plugins_in(plugins_paths)
        return self.modules
