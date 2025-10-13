from git_system_follower.develop.api.types import Parameters
from git_system_follower.develop.api.templates import delete_template

def main(parameters: Parameters):
    print(f"Deleting EnvGene project: {parameters.system.repository_name}")
    delete_template(parameters)
