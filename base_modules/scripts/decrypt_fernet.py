import logging


from yaml import safe_load, safe_dump
import click
from cryptography.fernet import Fernet

logging.basicConfig(format = '%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s', level = logging.INFO)
ENCRYPTED_CONST = 'encrypted:AES256_Fernet'

@click.group(chain=True)
def cmdb_prepare():
    pass


@cmdb_prepare.command("decrypt_cred_file")
@click.option('--file_path', '-f', 'file_path', required=True, help="Path to creds file")
@click.option('--secret_key', '-s', 'secret_key', required=True,
               help="Set secret_key for encrypt cred files")
def decrypt_file(secret_key, file_path):
    ''' {getenv('CI_PROJECT_DIR')}/ansible/inventory/group_vars/{getenv('env_name')}/appdeployer_cmdb/Tenants/{getenv('tenant_name')}/Credentials'''
    logging.debug('Try to read %s file', file_path)
    with open(file_path, mode="r", encoding="utf-8") as sensitive:
        sensitive_data = safe_load(sensitive)

    is_encrypted = check_if_file_is_encrypted(sensitive_data)
    if is_encrypted:
        if not secret_key:
            logging.error(f'Variable "{secret_key}" is not specified')
            exit(1)
        cipher = Fernet(secret_key)
        logging.debug('Try to decrypt data from %s file', file_path)
        if isinstance(sensitive_data, dict):
            decrypted_data = decode_sensitive(cipher, sensitive_data)
            logging.debug('Try to write data to %s file', file_path)
            with open(file_path, mode="w") as sensitive:
                safe_dump(decrypted_data, sensitive, default_flow_style=False)
                logging.info('The %s file has been decrypted', file_path)
        else:
            logging.info('The %s is empty or has no dict struct or not encrypted', file_path)
    else:
        logging.info('File is not encrypted')

def check_if_file_is_encrypted(sensitive_data) -> bool:
    for key, data in sensitive_data.items():
        if key != "type" and key != "credentialsId" and data:
            if isinstance(data, dict):
                if check_if_file_is_encrypted(data):
                    return True
            elif isinstance(data, str):
                if ENCRYPTED_CONST in data:
                    return True
            elif isinstance(data, list):
                for item in data:
                    if ENCRYPTED_CONST in item:
                        return True

    return False



def decode_sensitive(cipher:Fernet, sensitive_data) -> str:
    for key, data in sensitive_data.items():
        if key != "type" and key != "credentialsId" and data:
            if isinstance(data, dict):
                decode_sensitive(cipher, data)
            elif isinstance(data, list):
                _list = []
                for item in data:
                    if ENCRYPTED_CONST in item:
                        _list.append(
                            cipher.decrypt(item.replace(
                                f'[{ENCRYPTED_CONST}]','').encode('utf-8')).decode('utf-8'))
                sensitive_data[key] = _list
            elif ENCRYPTED_CONST in data:
                sensitive_data[key] = cipher.decrypt(
                    data.replace(f'[{ENCRYPTED_CONST}]','').encode('utf-8')).decode('utf-8')
    return sensitive_data


if __name__ == "__main__":
    # yaml = create_yaml_processor()
    cmdb_prepare()
