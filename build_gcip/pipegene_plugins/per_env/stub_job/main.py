from plugin_engine import PluginCore

class ImportJobPlugin(PluginCore):
    def __init__(self, params, pipeline_helper, pipeline) -> None:
        super().__init__(params, pipeline_helper, pipeline)

    def invoke(self) -> None:
        pass  # This is a stub that does nothing
    

