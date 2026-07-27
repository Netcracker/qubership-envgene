import click
from orchestrator import PipelineParametersHandler, resolve_env_names


@click.group(chain=True)
def pipeline():
    pass


@pipeline.command("log_params")
def log_params():
    handler = PipelineParametersHandler.from_env(resolve_env_names()[0])
    handler.log_pipeline_params()


@pipeline.command("write_dotenv")
def write_dotenv():
    handler = PipelineParametersHandler.from_env(resolve_env_names()[0])
    handler.write_dotenv()


if __name__ == "__main__":
    pipeline()
