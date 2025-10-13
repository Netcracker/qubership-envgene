from git_system_follower.develop.api.types import Parameters
from git_system_follower.develop.api.templates import create_template
from git_system_follower.typings.cli import ExtraParam

def main(parameters: Parameters):
    # Select template based on project type
    if 'git.netcracker' in parameters.system.host_domain:
        template = 'offsite'  # External project - use GitHub Actions
    else:
        template = 'onsite'   # Internal project - use GitLab CI
    
    extras = parameters.extras or {}
    
    # Convert ExtraParams to a dictionary of values
    variables = {}
    for key, param in extras.items():
        if isinstance(param, ExtraParam):
            variables[key] = param.value
        else:
            variables[key] = param
    variables['is_force'] = 'True'
    
    print(f"Creating EnvGene project with template: {template}")
    print(f"Project type: {'External (GitHub Actions)' if template == 'offsite' else 'Internal (GitLab CI)'}")
    print(f"Variables: {variables}")
    
    create_template(parameters, template, variables)
