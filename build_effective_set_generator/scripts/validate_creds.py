from envgenehelper import  getenv_with_error, findAllYamlsInDir, openYaml
from envgenehelper.logger import logger
from envgenehelper.errors import  ValidationError



def checkCredValueAndReturnError(credId: str, credValue: dict) -> str:
    result = ""
    type = credValue["type"]
    data = credValue["data"]
    match type:
        case "usernamePassword":
            if isEnvgeneNullValue(data["username"]) or isEnvgeneNullValue(data["password"]):
                result = f"credId: {credId} - username or password is not set"
        case "secret":
            if isEnvgeneNullValue(data["secret"]):
                result = f"credId: {credId} - secret is not set"
        case "vaultAppRole":
            if isEnvgeneNullValue(data["secretId"]):
                result = f"credId: {credId} - secretId is not set"
        case _:
            result = ""
    return result

def isEnvgeneNullValue(value: object) -> bool:
    if not isinstance(value, str):
        return False
    if value.lower() == "envgenenullvalue":
        return True
    return False

def validateCreds(creds_path: str):
    credsErrors =[]
    credsYamls = findAllYamlsInDir(creds_path)
    logger.info(f"Validating credential before effective set generation")
    for credListPath in credsYamls :
        credListYaml = openYaml(credListPath)
        for key, value in credListYaml.items() :
            errorCheck = checkCredValueAndReturnError(key, value)
            if errorCheck :
                credsErrors.append(errorCheck)
    if(credsErrors):
        if len(credsErrors) > 0:
            errorMessage = "Error while validating credentials: \n"
            for err in credsErrors:
                errorMessage += f"\t{err}\n"
            raise ValidationError(errorMessage, "ENVGENE-4002")



if __name__ == "__main__":
    environment_name = getenv_with_error('ENVIRONMENT_NAME')
    cluster_name = getenv_with_error('CLUSTER_NAME')
    work_dir = getenv_with_error('CI_PROJECT_DIR')
    creds_path = f"{work_dir}/environments/{cluster_name}/{environment_name}/Credentials"
    validateCreds(creds_path)
    logger.info(f"Validation of credentials is completed")