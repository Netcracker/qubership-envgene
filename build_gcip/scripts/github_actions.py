import os
from pprint import pformat
from dataclasses import fields

import click

from envgenehelper import logger
from validations import validate_pipeline
from pipeline_parameters import PipelineParametersHandler

@click.group()
def cli():
    pass

def prepare_input_params() -> PipelineParametersDataClass:
    pipe_params = PipelineParametersHandler()
    params_log = (f"Input parameters are: ")
    params_log += pipe_params.get_params_str()
    logger.info(params_log)
    return pipe_params.params

@cli.command("validate_pipeline")
def validate_pipeline_command():
    params = prepare_input_params()
    validate_pipeline(params)

if __name__ == "__main__":
 cli()
