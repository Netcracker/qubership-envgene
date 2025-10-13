from git_system_follower.develop.api.types import Parameters
from git_system_follower.develop.api.templates import update_template
from git_system_follower.typings.cli import ExtraParam

def main(parameters: Parameters):
    if 'git.netcracker' in parameters.system.host_domain:
        template = 'offsite'
    else:
        template = 'onsite'
    
    extras = parameters.extras or {}
    
    variables = {}
    for key, param in extras.items():
        if isinstance(param, ExtraParam):
            variables[key] = param.value
        else:
            variables[key] = param
    variables['is_force'] = 'True'
    
    print(f"Updating EnvGene project with template: {template}")
    update_template(parameters, template, variables)
