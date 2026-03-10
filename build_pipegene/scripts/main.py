import click

from gitlab_ci import build_pipeline
from validations import validate_pipeline
from scripts.utils.pipeline_parameters import PipelineParametersHandler
import os
from os import listdir
from datetime import datetime

@click.group(chain=True)
def gcip():
    pass

@gcip.command("generate_pipeline")
def generate_pipeline():
    print_workspace_debug()
    perform_generation()

def print_workspace_debug():
    project_dir = os.getenv("CI_PROJECT_DIR", os.getcwd())

    print(f"PIPELINE={os.getenv('CI_PIPELINE_ID')}")
    print(f"JOB={os.getenv('CI_JOB_NAME')}")
    print(f"CI_PROJECT_DIR={project_dir}")
    print(f"GIT_STRATEGY={os.getenv('GIT_STRATEGY')}")
    print(f"GIT_CHECKOUT={os.getenv('GIT_CHECKOUT')}")
    print(f"Job start time: {datetime.now()}")

    print("==== Workspace contents ====")
    try:
        for item in sorted(os.listdir(project_dir)):
            path = os.path.join(project_dir, item)
            print(item, "DIR" if os.path.isdir(path) else "FILE")
    except Exception as e:
        print(f"Error listing project dir: {e}")

    tmp_dir = os.path.join(project_dir, "tmp")

    print("==== TMP contents ====")
    if os.path.exists(tmp_dir):
        for item in sorted(os.listdir(tmp_dir)):
            print(item)
    else:
        print("tmp missing")

def perform_generation():
    handler = PipelineParametersHandler()
    handler.log_pipeline_params()
    validate_pipeline(handler.params)
    build_pipeline(handler.params)

if __name__ == "__main__":
    gcip()
