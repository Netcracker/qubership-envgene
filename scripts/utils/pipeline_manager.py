from pipeline_parameters import PipelineParametersHandler

import click


@click.group(chain=True)
def pipeline():
    pass


@pipeline.command("log_params")
def log_params():
    handler = PipelineParametersHandler()
    handler.log_pipeline_params()


# for setting in parameters for static pipeline
@pipeline.command("init_params")
def init_pipeline():
    handler = PipelineParametersHandler()
    handler.init_pipe_params()


@pipeline.command("write_dotenv")
def write_dotenv():
    handler = PipelineParametersHandler()
    handler.write_dotenv()


if __name__ == "__main__":
    pipeline()
