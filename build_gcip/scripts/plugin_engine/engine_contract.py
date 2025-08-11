from types import ModuleType

from gcip import Pipeline

class IPluginRegistry(type):
    plugin_registries: list[type] = list()

    def __init__(cls, name, bases, attrs):
        super().__init__(cls)
        if name != 'PluginCore':
            IPluginRegistry.plugin_registries.append(cls)

class PluginCore(object, metaclass=IPluginRegistry):
    def __init__(self) -> None:
        pass

    def invoke(self) -> None:
        pass
