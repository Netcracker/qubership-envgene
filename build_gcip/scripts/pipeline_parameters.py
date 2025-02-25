from os import getenv
from pprint import pformat

from plugin_engine import PluginEngine

def get_pipeline_parameters() -> dict:
    return {
        'ENV_NAMES': getenv("ENV_NAMES", ""),
        'ENV_BUILD': getenv("ENV_BUILDER") == "true",
        'GET_PASSPORT': getenv("GET_PASSPORT") == "true",
        'GENERATE_EFFECTIVE_SET': getenv("GENERATE_EFFECTIVE_SET", "false") == "true",
        'ENV_TEMPLATE_VERSION': getenv("ENV_TEMPLATE_VERSION", ""),
        'ENV_TEMPLATE_TEST': getenv("ENV_TEMPLATE_TEST") == "true",
        'IS_TEMPLATE_TEST': getenv("ENV_TEMPLATE_TEST") == "true",
        'IS_OFFSITE': getenv("IS_OFFSITE") == "true",
        'CI_COMMIT_REF_NAME': getenv("CI_COMMIT_REF_NAME", ""),
        'JSON_SCHEMAS_DIR': getenv("JSON_SCHEMAS_DIR", "/module/schemas"),
        'ENV_INVENTORY_GENERATION_PARAMS': {
            "SD_SOURCE_TYPE": getenv("SD_SOURCE_TYPE"),
            "SD_VERSION": getenv("SD_VERSION"),
            "SD_DATA": getenv("SD_DATA"),
            "SD_DELTA": getenv("SD_DELTA"),
            "ENV_INVENTORY_INIT": getenv("ENV_INVENTORY_INIT"),
            "ENV_SPECIFIC_PARAMETERS": getenv("ENV_SPECIFIC_PARAMS"),
            "ENV_TEMPLATE_NAME": getenv("ENV_TEMPLATE_NAME"),
            "ENV_TEMPLATE_VERSION": getenv("ENV_TEMPLATE_VERSION"),
        }
    }

class PipelineParametersHandler:
    def __init__(self, **kwargs):
        plugins_dir='/module/scripts/pipegene_plugins/pipe_parameters'
        self.params = get_pipeline_parameters()
        pipe_param_plugin = PluginEngine(plugins_dir=plugins_dir)
        if pipe_param_plugin.modules:
           pipe_param_plugin.run(pipeline_params=self.params)

    def get_params_str(self) -> str:
        result = ''
        for k, v in self.params:
            result += f"\n{k.upper()}: {pformat(v)}"
        return result
