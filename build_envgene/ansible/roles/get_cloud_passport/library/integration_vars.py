from ansible.module_utils.basic import *
from integration_loader.loader import IntergrationConfigLoader


def main():
    module = AnsibleModule(
        argument_spec=dict(
            var=dict(required=True, type='dict',
                     options={'cp_discovery': {
                         'type': 'dict',
                         'required': True,
                         'options': {
                             'gitlab': {
                                 'type': 'dict',
                                 'required': True,
                                 'options': {
                                     'branch': {
                                         'type': 'str',
                                         'required': True},
                                     'project': {
                                         'type': 'str',
                                         'required': True},
                                     'token': {
                                         'type': 'str',
                                         'required': True}
                                 }
                             }
                         }
                     },
                         'self_token': {
                             'type': 'str',
                             'required': True}
                     }
                     )
        ),
        supports_check_mode=True
    )
    var = module.params['var']
    integration = IntergrationConfigLoader(var)
    module.exit_json(changed=False, ansible_facts=integration.to_dict())


if __name__ == '__main__':
    main()
