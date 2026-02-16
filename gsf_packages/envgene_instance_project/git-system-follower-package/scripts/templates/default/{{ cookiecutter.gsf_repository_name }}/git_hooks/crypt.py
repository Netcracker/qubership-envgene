from cryptography.fernet import Fernet
from os import getenv,listdir,path,walk,makedirs,path,remove,environ
import click
import json
import ruyaml
import jschon
import jschon_tools
import jsonschema
import logging
import subprocess
import sys
logging.basicConfig(format = u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s', level = logging.INFO)

SECRET_KEY_ID = "SECRET_KEY"
FERNET_ID = "Fernet"
SOPS_ID = "SOPS"
ENVGENE_AGE_PUBLIC_KEY_ID = "ENVGENE_AGE_PUBLIC_KEY"
ENVGENE_AGE_PRIVATE_KEY_ID = "SOPS_AGE_KEY_FILE"
UNENCRYPTED_REGEX_STR = "^type$"

def create_yaml_processor() -> ruyaml.main.YAML:
    def _null_representer(self: ruyaml.representer.BaseRepresenter, data: None) -> ruyaml.Any:
        return self.represent_scalar('tag:yaml.org,2002:null', 'null')

    yaml = ruyaml.main.YAML()
    yaml.preserve_quotes = True  
    yaml.width = 200  
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.Representer.add_representer(type(None), _null_representer)
    return yaml

def open_yaml(file_path):
    logging.debug(f"Open yaml file: {file_path}")
    with open(file_path, mode="r", encoding="utf-8") as f:
        result_yaml = yaml.load(f.read())
    return result_yaml

def write_yaml_to_file(file_path, contents):
    logging.debug(f"Writing yaml to file: {file_path}")
    makedirs(path.dirname(file_path), exist_ok=True)
    with open(file_path, mode="w+") as f:
        yaml.dump(contents, f)
    return

@click.group(chain=True)
def cmdb_prepare():
    pass

def decode_sensitive(cipher:Fernet, sensitive_data) -> str:
    for key, data in sensitive_data.items():
        if key != "type" and key != "credentialsId" and data:
            if isinstance(data, dict):
                decode_sensitive(cipher, data)
            elif 'encrypted:AES256_Fernet' in data:
                sensitive_data[key] = cipher.decrypt(data.replace('[encrypted:AES256_Fernet]','').encode('utf-8')).decode('utf-8')
    return sensitive_data

def decode_sensitive_sops(cred_file):
    dir_path = path.dirname(path.realpath(cred_file))
    decrypted_file = path.join(dir_path, 'tmp')
    command = f'sops --decrypt {cred_file}  > {decrypted_file}'
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0 and "metadata not found" not in result.stderr:
        logging.info(f'The error occurred while SOPS decryption: {result.stderr}')
        remove(decrypted_file)
        sys.exit(1)
    file_content = open_yaml(decrypted_file)
    remove(decrypted_file)
    return file_content

def decrypt_file(secret_key, age_private_key_file, cred_file, crypt_backend):
    if not getenv(ENVGENE_AGE_PRIVATE_KEY_ID):
        environ[ENVGENE_AGE_PRIVATE_KEY_ID] = age_private_key_file
    logging.debug(f'Try to read {cred_file} file')
    sensitive_data = open_yaml(cred_file)
    logging.debug(f'Try to validate data from {cred_file} file')
    script_path = path.realpath(path.dirname(__file__))
    config_path = f"{script_path}/../configuration/config.yml"
    validateConfigFile(config_path, crypt_backend, secret_key,"","decrypt")
    logging.debug(f'Try to decrypt data from {cred_file} file')
    if crypt_backend == SOPS_ID:
        decrypted_data = decode_sensitive_sops(cred_file)
    else:
        cipher = Fernet(secret_key)
        if isinstance(sensitive_data, dict):
            decrypted_data = decode_sensitive(cipher, sensitive_data)
            logging.debug(f'Try to write data to {cred_file} file')
        else:
            logging.info(f'The {cred_file} is empty or has no dict struct')
    if decrypted_data is not None:
        write_yaml_to_file(cred_file, decrypted_data)
        logging.info(f'The {cred_file} file has been decrypted')
    else:
        logging.info(f'The {cred_file} file has not been decrypted')

@cmdb_prepare.command("decrypt_cred_file")
@click.option('--file_path', '-f', 'file_path', default = "", help="Path to file with creds")
@click.option('--secret_key', '-s', 'secret_key', default = getenv(SECRET_KEY_ID, ''), help="Set secret_key for encrypt cred files (Fernet)")
@click.option('--age_private_key_file', '-k', 'age_private_key_file', default = getenv(ENVGENE_AGE_PRIVATE_KEY_ID, ''), help="Private key file location for cred files decryption (SOPS)")
@click.option('--crypt_backend', '-c', 'crypt_backend', default = '', help="Set crypt_backend for encrypt cred files")
@click.option('--deployers', '-d', 'deployers', multiple=True, default = [getenv(key="DEPLOYERS",default="environments")], help="Path to deployer dir")
def decrypt_common_cred(secret_key, age_private_key_file, deployers, file_path, crypt_backend):
    if crypt_backend == '':
        crypt_backend = get_crypt_backend()
    logging.info(f"Crypt crypt_backend={crypt_backend}")
    if file_path:
        decrypt_file(secret_key, age_private_key_file, file_path, crypt_backend)
    else:
        for deployer in deployers:
            if getenv('ENV_NAME'):
                env_name = getenv('ENV_NAME')
                for envs_path, dirs, files in walk(f"{getenv(key='CI_PROJECT_DIR',default='.')}/{deployer}"):
                    if env_name in dirs:
                        env_path = path.join(envs_path, env_name)
                        for cred_file in listdir(f'{env_path}/Credentials'):
                            path_to_cred_file = path.join(env_path, 'Credentials', cred_file, crypt_backend)
                            decrypt_file(secret_key, age_private_key_file, path_to_cred_file, crypt_backend)
            else:
                for envs_path, dirs, files in walk(f"{getenv(key='CI_PROJECT_DIR',default='.')}/{deployer}"):
                    if 'credentials' in envs_path.lower():
                        for cred_file in listdir(envs_path):
                            path_to_cred_file = path.join(envs_path, cred_file)
                            decrypt_file(secret_key, age_private_key_file, path_to_cred_file, crypt_backend)

def encrypt_sensitive(cipher, sensitive_data):
    for key, data in sensitive_data.items():
        if key != "type" and data and 'encrypted:AES256_Fernet' not in data:
            if isinstance(data, dict):
                encrypt_sensitive(cipher, data)
            else:
                sensitive_data[key] = f"[encrypted:AES256_Fernet]{cipher.encrypt(data.encode('utf-8')).decode('utf-8')}"
    return sensitive_data

def encrypt_sensitive_sops(cred_file, age_public_key):
    dir_path = path.dirname(path.realpath(cred_file))
    encrypted_file = path.join(dir_path, 'tmp')
    command = f'sops --encrypt --age {age_public_key} --unencrypted-regex {UNENCRYPTED_REGEX_STR} {cred_file} > {encrypted_file}'
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0 and "metadata not found" not in result.stderr:
        logging.info(f'The error occurred while SOPS encryption: {result.stderr}')
        remove(encrypted_file)
        sys.exit(1)
    file_content = open_yaml(encrypted_file)
    remove(encrypted_file)
    return file_content

def get_crypt_enabled() :
    script_path = path.realpath(path.dirname(__file__))
    config_path = f"{script_path}/../configuration/config.yml"
    if path.exists(config_path) :
        config_yaml = open_yaml(config_path)
        if "crypt" in config_yaml : 
            return config_yaml["crypt"]
    return True

def get_crypt_backend() :
    script_path = path.realpath(path.dirname(__file__))
    config_path = f"{script_path}/../configuration/config.yml"
    if path.exists(config_path) :
        config_yaml = open_yaml(config_path)
        if "crypt_backend" in config_yaml :
            return config_yaml["crypt_backend"]
    return FERNET_ID

def encrypt_file(secret_key, age_public_key, cred_file, crypt_enabled, crypt_backend):
    if (crypt_enabled) : 
        logging.info(f'Try to read {cred_file} file')
        sensitive_data = open_yaml(cred_file)
        logging.debug(f'Try to validate data from {cred_file} file')
        script_path = path.realpath(path.dirname(__file__))
        config_path = f"{script_path}/../configuration/config.yml"
        validateConfigFile(config_path, crypt_backend, secret_key, age_public_key, "encrypt")
        logging.info(f'Try to encrypt data from {cred_file} file')
        if isinstance(sensitive_data, dict):
            if crypt_backend == SOPS_ID:
                encrypted_data = encrypt_sensitive_sops(cred_file, age_public_key)
            else:
                cipher = Fernet(secret_key)
                encrypted_data = encrypt_sensitive(cipher, sensitive_data)
            logging.info(f'Try to write data to {cred_file} file')
            write_yaml_to_file(cred_file, encrypted_data)
            if crypt_backend != SOPS_ID:
                sortYaml(cred_file)
            logging.info(f'The {cred_file} file has been encrypted')
        else:
            logging.info(f'The {cred_file} is empty or has no dict struct')

@cmdb_prepare.command("encrypt_cred_file")
@click.option('--file_path', '-f', 'file_path', default = '', help="Path to file with creds")
@click.option('--secret_key', '-s', 'secret_key', default = getenv(SECRET_KEY_ID, ''), help="Set secret_key for encrypt cred files (Fernet)")
@click.option('--age_public_key', '-p', 'age_public_key', default = getenv(ENVGENE_AGE_PUBLIC_KEY_ID, ''), help="Set age_public_key for encrypt cred files (SOPS)")
@click.option('--crypt_backend', '-c', 'crypt_backend', default = '', help="Set crypt_backend for encrypt cred files")
@click.option('--deployers', '-d', 'deployers', multiple=True, default = [getenv(key="DEPLOYERS",default="environments")], help="Path to deployer dir")
def encrypt_common_cred(secret_key, age_public_key, deployers, file_path, crypt_backend):
    if crypt_backend == '':
        crypt_backend = get_crypt_backend()
    crypt_enabled = get_crypt_enabled()
    logging.info(f"Crypt enabled={crypt_enabled}")
    logging.info(f"Crypt crypt_backend={crypt_backend}")
    if file_path:
        encrypt_file(secret_key, age_public_key, file_path, crypt_enabled, crypt_backend)
    else:
        for deployer in deployers:
            if getenv('ENV_NAME'):
                env_name = getenv('ENV_NAME')
                logging.info(f"ENV_NAME={env_name}")
                for envs_path, dirs, files in walk(f"{getenv(key='CI_PROJECT_DIR',default='.')}/{deployer}"):
                    if env_name in dirs:
                        env_path = path.join(envs_path, env_name)
                        for cred_file in listdir(f'{env_path}/Credentials'):
                            path_to_cred_file = path.join(env_path, 'Credentials', cred_file)
                            encrypt_file(secret_key, age_public_key, path_to_cred_file, crypt_enabled, crypt_backend)
            else:
                for envs_path, dirs, files in walk(f"{getenv(key='CI_PROJECT_DIR',default='.')}/{deployer}"):
                    if 'credentials' in envs_path.lower():
                        for cred_file in listdir(envs_path):
                            path_to_cred_file = path.join(envs_path, cred_file)
                            encrypt_file(secret_key, age_public_key, path_to_cred_file, crypt_enabled, crypt_backend)

def sortYaml(yaml_file):
    script_path = path.realpath(path.dirname(__file__))
    schema_path = f'{script_path}/credential.schema.json'
    with open(schema_path, 'r') as f:
        schema_data = json.load(f)
    logging.debug(f'Checking yaml with schema: {schema_path}')
    with open(yaml_file, 'r') as f:
        resultYaml = yaml.load(f.read())
    jsonschema.validate(resultYaml, schema_data)
    sort_data = jschon_tools.process_json_doc(
        schema_data=schema_data,
        doc_data=resultYaml,
        sort=True,
    )
    write_yaml_to_file(yaml_file, sort_data)

def validateConfigFile(yaml_file, crypt_backend, secret_key, age_public_key, mode):

    script_path = path.realpath(path.dirname(__file__))
    schema_path = f'{script_path}/config.schema.json'
    with open(schema_path, 'r') as f:
        schema_data = json.load(f)
    logging.debug(f'Checking yaml with schema: {schema_path}')
    with open(yaml_file, 'r') as f:
        resultYaml = yaml.load(f.read())
    jsonschema.validate(resultYaml, schema_data)

    if crypt_backend == FERNET_ID and not secret_key:
        raise Exception(f'Following CI/CD variables are not set: \n{SECRET_KEY_ID}.\nThis variable is mandatory for crypt_backend: {FERNET_ID}')
    empty_parameters = []
    if crypt_backend == SOPS_ID and mode == "encrypt" and not age_public_key:
        empty_parameters.append(ENVGENE_AGE_PUBLIC_KEY_ID)
    if crypt_backend == SOPS_ID and mode == "decrypt" and not getenv(ENVGENE_AGE_PRIVATE_KEY_ID,""):
        empty_parameters.append(ENVGENE_AGE_PRIVATE_KEY_ID)

    if empty_parameters:
        raise Exception(f'Following CI/CD variables are not set: \n{empty_parameters}.\nThese variables are mandatory for crypt_backend: {SOPS_ID}')

if __name__ == '__main__':
    jschon.create_catalog('2020-12')
    yaml = create_yaml_processor()
    cmdb_prepare()
