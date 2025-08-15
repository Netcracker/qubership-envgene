import click
import re

from envgenehelper import logger
from validations import validate_pipeline
from pipeline_parameters import PipelineParametersHandler

@click.group()
def cli():
    pass

def prepare_input_params() -> dict:
    pipe_params = PipelineParametersHandler()
    params_log = ("Input parameters are: ")
    params_log += pipe_params.get_params_str()
    params_log = re.sub(r'(CRED_ROTATION_PAYLOAD=)[^, ]+', r'\1***', params_log)
    logger.info(params_log)
    return pipe_params.params

@cli.command("validate_pipeline")
def validate_pipeline_command():
    params = prepare_input_params()
    validate_pipeline(params)

if __name__ == "__main__":
 cli()
