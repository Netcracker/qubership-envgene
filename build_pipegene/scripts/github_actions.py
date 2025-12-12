import click

from envgenehelper import logger
from validations import validate_pipeline
from pipeline_parameters import PipelineParametersHandler

@click.group()
def cli():
    pass

def prepare_input_params() -> dict:
    pipe_params = PipelineParametersHandler()
    return pipe_params.params

@cli.command("validate_pipeline")
def validate_pipeline_command():
    params = prepare_input_params()
    validate_pipeline(params)

if __name__ == "__main__":
 cli()
