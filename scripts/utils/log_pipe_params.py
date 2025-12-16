import json
from envgenehelper import logger
from scripts.utils.pipeline_parameters import PipelineParametersHandler


def log_pipeline_params(params: dict):
   params_str = "Input parameters are: "
   
   if params.get("CRED_ROTATION_PAYLOAD"): 
       params["CRED_ROTATION_PAYLOAD"] = "***"

   for k, v in params.items():
        try:
            parsed = json.loads(v)
            params[k] = json.dumps(parsed, separators=(",", ":"))
        except (TypeError, ValueError):
            pass

        params_str += f"\n{k.upper()}: {params[k]}"

   logger.info(params_str)

    
if __name__ == '__main__':
    handler = PipelineParametersHandler()
    params = handler.params.copy()
    log_pipeline_params(params)