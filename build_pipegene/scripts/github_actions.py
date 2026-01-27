import click

from validations import validate_pipeline
from scripts.utils.pipeline_parameters import PipelineParametersHandler

@click.group()
def cli():
    pass

@cli.command("validate_pipeline")
def validate_pipeline_command():
    handler = PipelineParametersHandler()
    handler.log_pipeline_params()
    validate_pipeline(handler.params)

if __name__ == "__main__":
 cli()
