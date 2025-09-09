from os import *

import click
import re

from envgenehelper import logger
from gitlab_ci import build_pipeline
from validations import validate_pipeline
from pipeline_parameters import PipelineParametersHandler

@click.group(chain=True)
def gcip():
    pass

def prepare_input_params() -> dict:
    pipe_params = PipelineParametersHandler()
    params_log = (f"Input parameters are: ")
    params_log += pipe_params.get_params_str()
    params_log = params_log = re.sub(r"(CRED_ROTATION_PAYLOAD:\s*)\(.*?\)", r"\1***", params_log, flags=re.DOTALL)
    logger.info(params_log)
    #PIPELINE_PARAMS = pipe_params.params
    return pipe_params.params

@gcip.command("generate_pipeline")
def generate_pipeline():
    perform_generation()

def perform_generation():
    params = prepare_input_params()
    validate_pipeline(params)
    build_pipeline(params)

if __name__ == "__main__":
    gcip()
