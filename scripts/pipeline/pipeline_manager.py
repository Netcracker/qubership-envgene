import click
from orchestrator import PipelineParametersHandler


@click.group(chain=True)
def pipeline():
    pass


@pipeline.command("log_params")
def log_params():
    handler = PipelineParametersHandler.from_env()
    handler.log_pipeline_params()


@pipeline.command("write_dotenv")
def write_dotenv():
    handler = PipelineParametersHandler.from_env()
    handler.write_dotenv()


if __name__ == "__main__":
    pipeline()
