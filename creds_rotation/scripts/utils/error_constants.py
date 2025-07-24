class ErrorMessages:
    """Error message constants"""
    INVALID_JSON = "Error: Invalid configuration format.\n Failed to parse JSON content in CRED_ROTATION_PAYLOAD. Error:\n {e}"
    INCORRECT_TYPE = "Error: Invalid configuration format.\n Please provide CRED_ROTATION_PAYLOAD in json string format."
    MISSING_ENV = "Error: Missing required configuration field.\n {e} .Please set it your pipeline_vars.yml."
    INVALID_ENCRYPT_TYPE = "Error: Invalid configuration format.\n Current encryption type is Fernet. Only SOPS is supported for CRED_ROTATION_PAYLOAD and credential files encryption/decryption in cred rotation. Please find configuration at CI_PROJECT_DIR/configurations/config.yaml."
    INVALID_CRED_FIELD = "Error: Invalid configuration format.\n Credential field {cred_field} is not supported. Supported credential types for cred rotation are UsernamePassword and Secret."
    PAYLOAD_DECRYPT_ERROR = "Error: Invalid configuration format.\n Failed to decrypt content of CRED_ROTATION_PAYLOAD: {e}. May be it is not encrypted correctly. Please verify the value."
    FILE_ENCRYPT_ERROR = "Error: Invalid configuration format.\n Failed to Encrypt the credential file {file} due to {e}"
    FILE_DECRYPT_ERROR = "Error: Invalid configuration format.\n Failed to Decrypt the credential file {file} due to {e}"
    FILE_READ_ERROR = "Error: Invalid configuration format.\n Failed to read the credential file {file} due to {e}"
    EMPTY_PARAM = "Error: Termination condition encountered.\n No affected parameters found for the given CRED_ROTATION_PAYLOAD in the current environment instance. Hence Terminating the job."
    CRED_UPDATION_FALSE = "Error: Termination condition encountered.\n Affected parameters have been identified. You can find the list of affected parameters in the artifact of this job, in the file {file}." \
    " Credentials updates are skipped because CRED_ROTATION_FORCE is not enabled. Terminating the job."
    INVALID_CONTEXT = "Error: Termination condition encountered.\n Unsupported context 'pipeline' for parameter '{param_key}'. This context is not valid for application-level parameters."
    ENTITY_FILE_NOT_FOUND = "Error: File not found: Target namespace/application file not found in environment instance for parameter key {param_key}."
    NS_FILE_NOT_FOUND = "Error: File not found.\n Failed to find namespace YAML file in the directory '{file}'. Please check if the namespace file is present."
    INVALID_YAML_FILE = "Error: Invalid configuration format.\n Failed to parse YAML file {file} due to {e} \n Please check the YAML structure in the file."
    MISSING_CONTEXT = "Error: Missing required configuration field.\n Context {context} not found in {target_file} for key {param_key}. Please check the context for the parameter."
    MISSING_CRED = "Error: Missing required configuration field.\n Credential macro not found in target file {target_file} in the context '{context}'. Please verify the parameter key in target file."
    MISSING_BLOCK = "Error: Missing required configuration field.\n Section '{block}' is not found for credential id {cred_id} in the file {cred_file}. Data discrepancy found in credential file."
    PARAM_NOT_FOUND = "Error: Missing required configuration field.\n Parameter key '{target_key}' not found in environment instance for the given context under specified namespace or application in cred rotation payload."
    MISSING_KEY = "Error: Missing required configuration field.\n Missing key: {key} in {current}. Incorrect value for the parameter found while lookig for affected parameters."
    INVALID_DATA_TYPE = "Error: Invalid Data Type.\n Expected {expected} at {value}, got {type}. Incorrect value for the parameter found while lookig for affected parameters."
    OUT_OF_RANGE = "Error: Out Of Range.\n Index {index} out of bounds for key: {key}. Incorrect value for the parameter found while lookig for affected parameters."
    INVALID_PATH = "Error: Invalid path hierarchy.\n {stop_dir} is not a parent of {source_path}. Something wrong with the folder structure in environment instance. Expected structure: project_dir/environments/cluster/env."

class ErrorCodes:
    """Error code constants"""
    INVALID_CONFIG_CODE = "ENVGENE-4002"
    INVALID_INPUT_CODE = "ENVGENE-4003"
    INVALID_STATE_CODE = "ENVGENE-4004"
    INVALID_DATA_TYPE_CODE = "ENVGENE-3002"
    OUT_OF_RANGE_CODE = "ENVGENE-3003"
    FILE_NOT_FOUND_CODE = "ENVGENE-8001"
    INVALID_PATH_CODE = "ENVGENE-8003"
    



    
    
