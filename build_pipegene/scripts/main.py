import click

from gitlab_ci import build_pipeline
from validations import validate_pipeline
from pipeline_parameters import PipelineParametersHandler

@click.group(chain=True)
def gcip():
    pass

@gcip.command("generate_pipeline")
def generate_pipeline():
    perform_generation()

def perform_generation():
    handler = PipelineParametersHandler()
    handler.log_params()
    validate_pipeline(handler.params)
    build_pipeline(handler.params)

if __name__ == "__main__":
    gcip()
