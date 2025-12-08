import click

from envgenehelper import logger
from gitlab_ci import build_pipeline
from validations import validate_pipeline
from pipeline_parameters import PipelineParametersHandler

@click.group(chain=True)
def gcip():
    pass

def prepare_input_params() -> dict:
    pipe_params = PipelineParametersHandler()
    return pipe_params.params

def log_pipeline_params(params: dict):
    params_str = "Input parameters are: "
    
    params_cp = params.copy()
    if params_cp.get("CRED_ROTATION_PAYLOAD"):
        params_cp["CRED_ROTATION_PAYLOAD"] = "***"
        
    for k, v in params_cp.items():
        params_str += f"\n{k.upper()}: {v}"

    logger.info(params_str)

@gcip.command("generate_pipeline")
def generate_pipeline():
    perform_generation()

def perform_generation():
    params = prepare_input_params()
    log_pipeline_params(params)
    validate_pipeline(params)
    build_pipeline(params)

if __name__ == "__main__":
    gcip()
