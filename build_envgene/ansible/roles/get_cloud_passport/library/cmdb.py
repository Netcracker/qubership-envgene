from ansible.module_utils.basic import *
from yaml import safe_load, safe_dump
from envgenehelper.yaml_helper import beautifyYaml

def preparation(sensitive_data):
    for key, value in sensitive_data.items():
        if value["type"] == "usernamePassword":
            sensitive_data[key] = {
                                    "type": value["type"],
                                    "data": {
                                        "username": value["username"],
                                        "password": value["password"]
                                        }
                                    }
        elif value["type"] == "secret":
            for k,v in value.items():
                if k != "type":
                    sensitive_data[key] = {
                                            "type": value["type"],
                                            "data": {
                                                "secret": v
                                                }
                                            }
    return sensitive_data

def main():
    module = AnsibleModule(
      argument_spec=dict(
          cred_file=dict(required=True, type='str')
      ),
      supports_check_mode=True
    )
    if module.check_mode:
       module.exit_json(changed=False)
    cred_file = module.params['cred_file']
    with open(cred_file, mode="r", encoding="utf-8") as file:
        sensitive_data = safe_load(file)
    updated_data = preparation(sensitive_data)
    with open(cred_file, mode="w", encoding="utf-8") as file:
        safe_dump(updated_data,file)
    creds_schema="/build_env/schemas/credential.schema.json"
    beautifyYaml(cred_file, creds_schema)
    with open(cred_file, mode="r", encoding="utf-8") as file:
        beautified_data = safe_load(file)
    module.exit_json(changed=True, result=beautified_data)

if __name__ == '__main__':
  main()
