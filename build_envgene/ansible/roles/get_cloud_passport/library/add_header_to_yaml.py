from ansible.module_utils.basic import *
from envgenehelper.yaml_helper import addHeaderToYaml

def main():
    module = AnsibleModule(
      argument_spec=dict(
          path=dict(required=True, type='str'),
          text=dict(required=True, type='str')
      ),
      supports_check_mode=True
    )
    if module.check_mode:
       module.exit_json(changed=False)
    path = module.params['path']
    text = module.params['text']
    addHeaderToYaml(path, text)
    with open(path, mode="r", encoding="utf-8") as file:
        result = file.read()
    module.exit_json(changed=True, result=result)

if __name__ == '__main__':
  main()
