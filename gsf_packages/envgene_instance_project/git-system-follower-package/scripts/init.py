from git_system_follower.develop.api.types import Parameters
from git_system_follower.develop.api.cicd_variables import CICDVariable, create_variable
from git_system_follower.develop.api.templates import create_template, update_template, get_template_names

def main(parameters: Parameters):
    templates = get_template_names(parameters)
    if not templates:
        raise ValueError('There are no templates in the package')

    if len(templates) > 1:
        template = parameters.extras.get('TEMPLATE')
        if template is None:
            raise ValueError('There are more than 1 template in the package, '
                             'specify which one you want to use with the TEMPLATE variable')
    else:
        template = templates[0]

    variables = parameters.extras.copy()
    variables.pop('TEMPLATE', None)
    
    if parameters.used_template:
        update_template(parameters, variables, is_force=True)
    else:
        create_template(parameters, template, variables)

    print(parameters.extras)
    print(parameters._Parameters__system_params)
    
    CICD_VARIABLES = [
        {'name': 'DOCKER_REGISTRY', 'value': 'reg2', 'masked': False},
        {'name': 'SECRET_KEY', 'value': 'initial_value', 'masked': True},
        {'name': 'GITLAB_TOKEN', 'value': 'initial_value', 'masked': True},
        {'name': 'ENVGENE_AGE_PRIVATE_KEY', 'value': 'initial_value', 'masked': True},
        {'name': 'ENVGENE_AGE_PUBLIC_KEY', 'value': 'initial_value', 'masked': True},
        {'name': 'PUBLIC_AGE_KEYS', 'value': 'initial_value', 'masked': True},
        {'name': 'IS_OFFSITE', 'value': 'true', 'masked': False},
        {'name': 'GITLAB_RUNNER_TAG_NAME', 'value': 'initial_value', 'masked': False},
        {'name': 'RUNNER_SCRIPT_TIMEOUT', 'value': 'initial_value', 'masked': False},
    ]
    
    for var_config in CICD_VARIABLES:
        var_name = var_config['name']
        var_data = parameters.extras.get(var_name)
        
        if var_data is not None:
            if isinstance(var_data, (list, tuple)) and len(var_data) >= 2:
                value = var_data[0] if var_data[0] else var_config.get('value')
                masked_flag = var_data[1].lower() if len(var_data) > 1 else None
            elif isinstance(var_data, str):
                parts = var_data.strip().split(None, 1)
                value = parts[0] if parts else var_config.get('value')
                masked_flag = parts[1].lower() if len(parts) > 1 else None
            else:
                value = str(var_data) if var_data else var_config.get('value')
                masked_flag = None
            
            if masked_flag:
                masked_flag_lower = masked_flag.lower()
                if 'no' in masked_flag_lower and 'masked' in masked_flag_lower:
                    masked = False
                elif 'masked' in masked_flag_lower:
                    masked = True
                else:
                    masked = var_config['masked']
            else:
                masked = var_config['masked']
        else:
            value = var_config.get('value')
            masked = var_config['masked']
        
        if not value or (isinstance(value, str) and not value.strip()):
            continue
        
        create_variable(
            parameters,
            CICDVariable(
                name=var_config['name'],
                value=value,
                env='*',
                masked=masked
            ),
            is_force=True
        )
