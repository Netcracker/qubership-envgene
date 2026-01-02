import re
from pathlib import Path

from envgenehelper import crypt, getenv_with_error

from .logger import logger

# const
CRED_TYPE_SECRET = "secret"
CRED_TYPE_USERPASS = "usernamePassword"
CRED_TYPE_VAULT = "vaultAppRole"

CRED_VALUE_TYPE_USERNAME = "username"
CRED_VALUE_TYPE_PASSWORD = "password"
CRED_VALUE_TYPE_SECRET = "secret"
CONCEALED_SECRET_MASK = "*****"


def check_is_cred(param_key, param_value):
    if isinstance(param_value, str):
        # if we are iterationg through array, than cred macros can't be in key (it is integer)
        credKey = param_key.replace(" ", "") if isinstance(param_key, str) else ""
        credValue = param_value.replace("'", "\"")
        if re.match(r'#creds{(.+)\s*,\s*(.+)}', credKey) or re.match(r'#credscl{(.+)\s*,\s*(.+)}', credKey) or re.match(
                r'#credsns{(.+)\s*,\s*(.+)}', credKey):
            return True
        elif re.search(r'\${.*creds\.get.*\.username}', credValue) or re.search(r'\${.*creds\.get.*\.password}',
                                                                                credValue):
            return True
        elif re.search(r'\${.*creds\.get.*\.secret}', credValue):
            return True
        elif re.search(r'\${.*creds\.get.*\.roleId}', credValue) or re.search(r'\${.*creds\.get.*\.secretId}',
                                                                              credValue) \
                or re.search(r'\${.*creds\.get.*\.path}', credValue) or re.search(r'\${.*creds\.get.*\.namespace}',
                                                                                  credValue):
            return True
    return False


def create_cred_definition(cred_id, cred_type):
    cred = {}
    cred["credentialsId"] = cred_id
    cred["type"] = cred_type
    return cred


def get_cred_list_from_param(param_key, param_value, update_cred_id=False, tenant_name="", cloud_name="",
                             namespace_name=""):
    # as param value can contain multiple creds (e.g. json format or multiline string) we are returning list
    result = []
    _process_cred_in_string(param_key, param_value, tenant_name, cloud_name, namespace_name, result, update_cred_id)
    return result


def _process_cred_in_string(param_key, param_value, tenant_name, cloud_name, namespace_name, cred_list, update_cred_id):
    while check_is_cred(param_key, param_value):
        credDef, param_key, param_value = _get_cred_from_string(param_key, param_value, tenant_name, cloud_name,
                                                                namespace_name, update_cred_id)
        cred_list.append(credDef)


def _get_cred_from_string(param_key, param_value, tenant_name, cloud_name, namespace_name, update_cred_id):
    credId = ""
    credType = ""
    if isinstance(param_value, str):
        # if we are iterationg through array, than cred macros can't be in key (it is integer)
        credKey = param_key.replace(" ", "") if isinstance(param_key, str) else ""
        credValue = param_value.replace("'", "\"")
        if re.match(r'#creds{(.+)\s*,\s*(.+)}', credKey):
            credId = credValue
            credType = CRED_TYPE_USERPASS
        elif re.match(r'#credscl{(.+)\s*,\s*(.+)}', credKey):
            credId = tenant_name + "-" + cloud_name + "-" + credValue if update_cred_id else credValue
            credType = CRED_TYPE_USERPASS
        elif re.match(r'#credsns{(.+)\s*,\s*(.+)}', credKey):
            if update_cred_id:
                if not namespace_name:
                    logger.error(
                        f"Namespace level cred {credValue} is defined not on NAMESPACE level. Parameter: {param_key}={param_value}")
                    raise ReferenceError(f"Error during credentials preparation. See logs above.")
                credId = tenant_name + "-" + cloud_name + "-" + namespace_name + "-" + credValue
            else:
                credId = credValue
            credType = CRED_TYPE_USERPASS
        elif re.search(r'\${.*creds\.get.*\.username}', credValue) or re.search(r'\${.*creds\.get.*\.password}',
                                                                                credValue):
            credId = _get_cred_id_from_cred_macros(credValue)
            credType = CRED_TYPE_USERPASS
        elif re.search(r'\${.*creds\.get.*\.secret}', credValue):
            credId = _get_cred_id_from_cred_macros(credValue)
            credType = CRED_TYPE_SECRET
        elif re.search(r'\${.*creds\.get.*\.roleId}', credValue) or re.search(r'\${.*creds\.get.*\.secretId}',
                                                                              credValue) \
                or re.search(r'\${.*creds\.get.*\.path}', credValue) or re.search(r'\${.*creds\.get.*\.namespace}',
                                                                                  credValue):
            credId = _get_cred_id_from_cred_macros(credValue)
            credType = CRED_TYPE_VAULT
    if (credId):
        returnKey = ""
        returnValue = _remove_first_cred_from_input(credValue)
        return create_cred_definition(credId, credType), returnKey, returnValue
    else:
        logger.error(f"Can't parse cred from param: {param_key}={param_value}")
        raise ReferenceError(f"Error during credentials preparation. See logs above.")


def _get_cred_id_from_cred_macros(value):
    match = re.search(r'.*\${.*creds\.get\((.*)\).*}.*', value)
    if (match):
        return match.group(1).strip().strip("\\\"").strip("\"")
    else:
        logger.error(f"Can't obtain credId from: {value}")
        raise ReferenceError(f"Error during credentials preparation. See logs above.")


def get_cred_id_from_cred_macros(value):
    if (value):
        credValue = value.replace("'", "\"").strip().strip("\\\"").strip("\"")
        return _get_cred_id_from_cred_macros(credValue) if credValue else ""
    return ""


def _remove_first_cred_from_input(value):
    return re.sub(r'\${.*creds\.get\(.*\).*}', "", value, 1)


# #creds, #credscl, #credsns macroses are not supported
# vault creds are not supported
def expand_cred_macro_and_return_value(param_key, param_value, env_creds):
    credValue = param_value.strip()
    credKey = param_key.replace(" ", "") if isinstance(param_key, str) else ""
    if re.match(r'#creds{(.+)\s*,\s*(.+)}', credKey) or re.match(r'#credscl{(.+)\s*,\s*(.+)}', credKey) or re.match(
            r'#credsns{(.+)\s*,\s*(.+)}', credKey):
        logger.error(f"Credential macros for parameter is not supported: {param_key}={param_value}")
        raise ReferenceError(f"Error during credentials preparation. See logs above.")
    elif re.search(r'\${.*creds\.get.*\.roleId}', credValue) or re.search(r'\${.*creds\.get.*\.secretId}', credValue) \
            or re.search(r'\${.*creds\.get.*\.path}', credValue) or re.search(r'\${.*creds\.get.*\.namespace}',
                                                                              credValue):
        logger.error(f"Credential macros for parameter is not supported: {param_key}={param_value}")
        raise ReferenceError(f"Error during credentials preparation. See logs above.")
    credList = get_cred_list_from_param(param_key, param_value)
    for cred in credList:
        credId = cred["credentialsId"]
        if match := re.search(r'\${.*creds\.get.*(' + re.escape(credId) + r').*\.username}', credValue):
            value = get_value_from_cred(credId, CRED_VALUE_TYPE_USERNAME, env_creds)
            credValue = credValue.replace(match.group(0), value)
        elif match := re.search(r'\${.*creds\.get.*(' + re.escape(credId) + r').*\.password}', credValue):
            value = get_value_from_cred(credId, CRED_VALUE_TYPE_PASSWORD, env_creds)
            credValue = credValue.replace(match.group(0), value)
        elif match := re.search(r'\${.*creds\.get.*(' + re.escape(credId) + r').*\.secret}', credValue):
            value = get_value_from_cred(credId, CRED_VALUE_TYPE_SECRET, env_creds)
            credValue = credValue.replace(match.group(0), value)
        else:
            logger.error(f"Macros for credentialsId {credId} is not found in parameter: {param_key}={param_value}")
            raise ReferenceError(f"Error during credentials preparation. See logs above.")
    return credValue


def get_value_from_cred(cred_id, cred_val_type, env_creds):
    if cred_id in env_creds:
        credData = env_creds[cred_id]
        return credData["data"][cred_val_type]
    else:
        logger.error(f"Credential for env {cred_id} is not found in environment credentials.")
        raise ReferenceError(f"Credential for env {cred_id} is not found in environment credentials.")


def check_is_envgen_cred(value):
    credValue = value.strip().replace("'", "\"")
    if re.search(r'envgen\.creds\.get.*\.username', credValue) or re.search(r'envgen\.creds\.get.*\.password',
                                                                            credValue):
        return True
    elif re.search(r'envgen\.creds\.get.*\.secret', credValue):
        return True
    return False


def get_cred_id_and_property_from_cred_macros(value):
    credValue = value.replace("'", "\"").strip().strip("\\\"").strip("\"")
    pattern = r'.*\${.*creds\.get\((.*)\).(\w+)}.*'
    # if it is not a cred we assume it is envgen cred
    if check_is_envgen_cred(credValue):
        pattern = r'envgen\.creds\.get\((.*)\).(\w+)'

    match = re.search(pattern, credValue)
    if (match):
        credId = match.group(1).strip().strip("\\\"").strip("\"")
        credProperty = match.group(2).strip().strip("\\\"").strip("\"")
        return credId, credProperty
    else:
        logger.error(f"Can't obtain credId from: {value}")
        raise ReferenceError(f"Error during credentials preparation. See logs above.")


def mask_sensitive(data: dict,
                   keys_to_mask=(CRED_VALUE_TYPE_SECRET, CRED_VALUE_TYPE_PASSWORD, CRED_VALUE_TYPE_USERNAME)) -> dict:
    masked = {}
    for k, v in data.items():
        if isinstance(v, dict):
            masked[k] = mask_sensitive(v, keys_to_mask)
        elif any(key in k.lower() for key in keys_to_mask):
            masked[k] = CONCEALED_SECRET_MASK
        else:
            masked[k] = v
    return masked


def fetch_cred_value(val, cred_config) -> str:
    match = re.search(r".*\('([^']+)'\)\.(\w+)", val)
    if match:
        cred_name = match.group(1)
        cred_property = match.group(2)
        return cred_config[cred_name]["data"][cred_property]
    else:
        raise ValueError(f"Value '{val}' does not match expected format")


def get_cred_config():
    base_dir = getenv_with_error('CI_PROJECT_DIR')
    cred_config = crypt.decrypt_file(Path(f"{base_dir}/configuration/credentials/credentials.yml"))
    return cred_config
