import click

from pipeline.pipeline_parameters import PipelineParametersHandler


@click.group(chain=True)
def pipeline():
    pass


def _prepare_handler() -> PipelineParametersHandler:
    return PipelineParametersHandler.from_env()


@pipeline.command("log_params")
def log_params():
    _prepare_handler().log_pipeline_params()


@pipeline.command("write_dotenv")
def write_dotenv():
    _prepare_handler().write_dotenv()


if __name__ == "__main__":
    pipeline()
