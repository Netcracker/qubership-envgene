import click

from gitlab_ci import build_pipeline
from scripts.utils.pipeline_parameters import PipelineParametersHandler
from envgenehelper.validations import validate_pipeline


@click.group(chain=True)
def gcip():
    pass

@gcip.command("generate_pipeline")
def generate_pipeline():
    perform_generation()

def perform_generation():
    handler = PipelineParametersHandler()
    handler.log_pipeline_params()
    validate_pipeline(handler.params)
    build_pipeline(handler.params, handler.sensitive_params)

if __name__ == "__main__":
    gcip()
