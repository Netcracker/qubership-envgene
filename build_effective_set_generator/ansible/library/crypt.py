from ansible.module_utils.basic import *
from envgenehelper import decrypt_file, encrypt_file

def main():
    module = AnsibleModule(
      argument_spec=dict(
          crypt_type=dict(required=True, type='str'),
          source_file=dict(required=True, type='str', no_log=True),
          secret_key=dict(type='str',  no_log=True),
          public_key=dict(type='str', no_log=True),
          crypt_backend=dict(type='str'),
          in_place=dict(default=False, type='bool'),
          minimize_diff=dict(default=False, type='bool'),
          old_encrypted_file=dict(required=False, type="str", no_log=True),
      ),
      supports_check_mode=True
    )
    if module.check_mode:
       module.exit_json(changed=False)
    crypt_type = module.params['crypt_type']
    secret_key = module.params['secret_key']
    source_file = module.params['source_file']
    public_key = module.params['public_key']
    crypt_backend = module.params['crypt_backend']
    in_place = module.params['in_place']
    minimize_diff = module.params['minimize_diff']
    old_encrypted_file = module.params['old_encrypted_file']
    if crypt_type == 'encrypt':
        crypt_func = encrypt_file
    else:
        crypt_func = decrypt_file
    result = crypt_func(source_file, secret_key=secret_key, in_place=in_place, public_key=public_key, crypt_backend=crypt_backend, minimize_diff=minimize_diff, old_file_path=old_encrypted_file)
    module.exit_json(changed=True, result=result)

if __name__ == '__main__':
  main()
