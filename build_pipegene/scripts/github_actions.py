import click

from validations import validate_pipeline
from scripts.utils.pipeline_parameters import PipelineParametersHandler, log_pipeline_params

@click.group()
def cli():
    pass

@cli.command("validate_pipeline")
def validate_pipeline_command():
    handler = PipelineParametersHandler()
    log_pipeline_params(handler.params.copy())
    validate_pipeline(handler.params)

if __name__ == "__main__":
 cli()
