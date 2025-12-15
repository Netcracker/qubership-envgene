import click

from gitlab_ci import build_pipeline
from validations import validate_pipeline
from scripts.utils.pipeline_parameters import PipelineParametersHandler
from scripts.utils.log_pipe_params import log_pipeline_params

@click.group(chain=True)
def gcip():
    pass

@gcip.command("generate_pipeline")
def generate_pipeline():
    perform_generation()

def perform_generation():
    handler = PipelineParametersHandler()
    log_pipeline_params(handler.params.copy())
    validate_pipeline(handler.params)
    build_pipeline(handler.params)

if __name__ == "__main__":
    gcip()
