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

    create_variable(
        parameters,
        CICDVariable(
            name='SECRET_KEY',
            value='test_value',
            env='*',
            masked=True
        ),
        is_force=True
    )
    create_variable(
        parameters,
        CICDVariable(
            name='GITLAB_TOKEN',
            value='test_value',
            env='*',
            masked=True
        ),
        is_force=True
    )
    create_variable(
        parameters,
        CICDVariable(
            name='ENVGENE_AGE_PRIVATE_KEY',
            value='test_value',
            env='*',
            masked=True
        ),
        is_force=True
    )
    create_variable(
        parameters,
        CICDVariable(
            name='ENVGENE_AGE_PUBLIC_KEY',
            value='test_value',
            env='*',
            masked=True
        ),
        is_force=True
    )
    create_variable(
        parameters,
        CICDVariable(
            name='PUBLIC_AGE_KEYS',
            value='test_value',
            env='*',
            masked=True
        ),
        is_force=True
    )
    create_variable(
        parameters,
        CICDVariable(
            name='IS_OFFSITE',
            value='test_value',
            env='*',
            masked=False
        ),
        is_force=True
    )
    create_variable(
        parameters,
        CICDVariable(
            name='GITLAB_RUNNER_TAG_NAME',
            value='test_value',
            env='*',
            masked=False
        ),
        is_force=True
    )
    create_variable(
        parameters,
        CICDVariable(
            name='RUNNER_SCRIPT_TIMEOUT',
            value='test_value',
            env='*',
            masked=False
        ),
        is_force=True
    )