import os
from dataclasses import dataclass, field
from pathlib import Path
from ruyaml import CommentedMap
from envgenehelper import CRED_MACRO_PATTERN, CRED_MACRO_PROPERTY_TYPES, CredentialMode, ValidationError, check_is_cred, current_env_instance_store, dump_as_yaml_format, extract_namespace_from_application_path, extract_namespace_from_namespace_path, get_cred_list_from_param, get_schema_dir, logger, openFileAsString, readYaml, store_value_to_yaml, validate_cred_types, validate_yaml_by_scheme_or_fail, yaml, extract_external_cred

#const
CRED_TYPE_SECRET="secret"
CRED_TYPE_USERPASS="usernamePassword"
CRED_TYPE_VAULT="vaultAppRole"
CRED_TYPE_EXTERNAL="external"
TECHNICAL_CONFIG_PARAMS = "technicalConfigurationParameters"
DEFAULT_SECRET_STORE = "default_store"
JINJA_MARKERS = ("{{", "{%", "{#")
SHARED_CRED_EXTENSIONS = (".yml", ".yaml", ".yml.j2", ".yaml.j2")


@dataclass
class CredentialCollector:
    credential_mode: CredentialMode
    referenced_creds: dict = field(default_factory=dict)
    credref_ids: set = field(default_factory=set)
    local_ids_in_external: set = field(default_factory=set)
    builtin_refs: dict = field(default_factory=dict)

    def add_builtin(self, cred_id, cred_type, comment, field_name):
        self.builtin_refs.setdefault(cred_id, (comment, field_name))
        self.add(cred_id, cred_type, comment)

    def add(self, cred_id, cred_type, comment):
        self.referenced_creds.setdefault(cred_id.strip("\""), (cred_type, comment))

    def add_credref(self, cred_id, cred_property, comment):
        self.credref_ids.add(cred_id)
        self.add(cred_id, CRED_TYPE_USERPASS if cred_property else CRED_TYPE_SECRET, comment)


def processParametersAndAppend(paramTypeKey, paramsDict, collector, tenantName, cloudName="", namespaceName="", comment="") :
    if paramTypeKey not in paramsDict.keys():
        return
    processDictAndAppend(paramsDict[paramTypeKey], collector, tenantName, cloudName, namespaceName, comment, paramTypeKey)

def processDictAndAppend(params, collector, tenantName, cloudName, namespaceName, comment, param_type_key=None):
    for key, value in params.items():
        processSingleParam(params, key, value, collector, tenantName, cloudName, namespaceName, comment, param_type_key)

def processSingleParam(container, key, value, collector, tenantName, cloudName, namespaceName, comment, param_type_key=None):
    if isinstance(value, dict):
        cred_id = extract_external_cred(value)
        if cred_id:
            if param_type_key == TECHNICAL_CONFIG_PARAMS:
                raise ValidationError(f"Invalid value for key '{key}'. External credentials are not supported in '{TECHNICAL_CONFIG_PARAMS}'")
            collector.add_credref(cred_id, value.get("property"), comment)
            return
        processDictAndAppend(value, collector, tenantName, cloudName, namespaceName, comment, param_type_key)
    elif isinstance(value, list): # if is array, than iterate
        for idx, item in enumerate(value):
            processSingleParam(value, idx, item, collector, tenantName, cloudName, namespaceName, comment, param_type_key)
    elif isinstance(value, str):
        if not check_is_cred(key, value):
            return
        if collector.credential_mode == CredentialMode.EXTERNAL and param_type_key != TECHNICAL_CONFIG_PARAMS:
            rewriteMacroToCredRef(container, key, value, collector, comment)
            return
        for cred in get_cred_list_from_param(key, value, True, tenantName, cloudName, namespaceName):
            if collector.credential_mode == CredentialMode.EXTERNAL:
                collector.local_ids_in_external.add(cred["credentialsId"])
            collector.add(cred["credentialsId"], cred["type"], comment)

def rewriteMacroToCredRef(container, key, value, collector, comment):
    if isinstance(key, str) and key.replace(" ", "").startswith("#creds"):
        raise ValidationError(f"Deprecated credential macro in key '{key}' with credId '{value}' is not supported in "
                              "external credential mode. Use ${{creds.get('<credId>').username}} or a credRef")
    macros = [m for m in CRED_MACRO_PATTERN.finditer(value) if m.group(2) in CRED_MACRO_PROPERTY_TYPES]
    if not macros:
        raise ValidationError(f"Can't parse credential macro in parameter '{key}'")
    if len(macros) > 1:
        raise ValidationError(f"Parameter '{key}' has multiple credential references {[m.group(1) for m in macros]}. "
                              "In external credential mode a value must be exactly one reference. "
                              "Move each reference into a dedicated parameter")
    cred_id, cred_property = macros[0].group(1), macros[0].group(2)
    if value.strip() != macros[0].group(0):
        raise ValidationError(f"Parameter '{key}' embeds credential reference '{cred_id}' in other text. "
                              "In external credential mode a value must be exactly one reference. "
                              "Move the reference into a dedicated parameter")
    cred_type = CRED_MACRO_PROPERTY_TYPES[cred_property]
    if cred_type == CRED_TYPE_VAULT:
        raise ValidationError(f"Parameter '{key}' reads '{cred_property}' of credential '{cred_id}'. "
                              "vaultAppRole credentials can't be external. "
                              "Provide the Secret Store access through environment or CI configuration")
    cred_ref = CommentedMap()
    cred_ref["$type"] = "credRef"
    cred_ref["credId"] = cred_id
    if cred_type == CRED_TYPE_USERPASS:
        cred_ref["property"] = cred_property
    container[key] = cred_ref
    logger.debug(f"Replaced local macro for parameter {key}:{value} with '{cred_ref}'")
    collector.add(cred_id, cred_type, comment)

def field_for_credentials(content, field_name, owner):
    if field_name not in content:
        raise ValueError(f"Field '{field_name}' is missing in {owner}. It is needed to create Credentials.")
    return content[field_name]


def checkCredAndAppend(credName, collector, secretType, comment="", field_name=""):
    if credName:
        collector.add_builtin(credName, secretType, comment, field_name)

def getTenantCreds(tenantContent, tenantName, collector):
    tenantComment = f"tenant {tenantName}"
    checkCredAndAppend(field_for_credentials(tenantContent, "credential", tenantComment), collector, CRED_TYPE_SECRET,
                       tenantComment, "credential")
    #process deployParameters
    processParametersAndAppend("deployParameters", tenantContent, collector, tenantName, comment=tenantComment)
    processParametersAndAppend("environmentParameters",
                               field_for_credentials(tenantContent, "globalE2EParameters", tenantComment), collector,
                               tenantName, comment=tenantComment)

def reject_misplaced_references(collector):
    if collector.credential_mode == CredentialMode.EXTERNAL:
        if collector.local_ids_in_external:
            raise ReferenceError(f"Found local credential macros in external cred only environment."
                                 f"Credential IDs are  {sorted(collector.local_ids_in_external)}")
    elif collector.credref_ids:
        raise ReferenceError(f"Found external credential references in parameters in local cred only environment. "
                             f"Credential IDs are {collector.credref_ids}")

def warn_unused_external_creds(env_creds_map, collector):
    unused_creds = [
        cred_name
        for cred_name, cred_config in env_creds_map.items()
        if cred_config.get("type") == CRED_TYPE_EXTERNAL
        and cred_name not in collector.referenced_creds
    ]
    if unused_creds:
        logger.warning(f"Following external credentials:\n{unused_creds}\n"
            f"exist in external credential source but are not referred in environment"
        )


def getCloudCreds(cloudContent, tenantName, cloudName, collector):
    cloudComment = f"cloud {cloudName}"
    checkCredAndAppend(cloudContent["defaultCredentialsId"], collector, CRED_TYPE_SECRET, cloudComment,
                       "defaultCredentialsId")
    checkCredAndAppend(cloudContent["maasConfig"]["credentialsId"], collector, CRED_TYPE_USERPASS, cloudComment,
                       "maasConfig.credentialsId")
    checkCredAndAppend(cloudContent["vaultConfig"]["credentialsId"], collector, CRED_TYPE_SECRET, cloudComment,
                       "vaultConfig.credentialsId")
    checkCredAndAppend(cloudContent["consulConfig"]["tokenSecret"], collector, CRED_TYPE_SECRET, cloudComment,
                       "consulConfig.tokenSecret")
    for i in field_for_credentials(cloudContent, "dbaasConfigs", cloudComment):
        checkCredAndAppend(i["credentialsId"], collector, CRED_TYPE_USERPASS, cloudComment,
                           "dbaasConfigs[].credentialsId")

    #process deployParameters
    processParametersAndAppend("deployParameters", cloudContent, collector, tenantName, cloudName, comment=cloudComment)
    #process e2eParameters
    processParametersAndAppend("e2eParameters", cloudContent, collector, tenantName, cloudName, comment=cloudComment)
    #process technicalConfigurationParameters
    processParametersAndAppend("technicalConfigurationParameters", cloudContent, collector, tenantName, cloudName, comment=cloudComment)

def get_bg_domain_creds(content, name, collector):
    bg_domain_comment = f"bg domain {name}"
    checkCredAndAppend(content["controllerNamespace"]["credentials"], collector, CRED_TYPE_USERPASS, bg_domain_comment,
                       "controllerNamespace.credentials")

def getNamespaceCreds(namespaceContent, tenantName, cloudName, namespaceName, collector):
    namespaceComment = f"namespace {namespaceName}"
    checkCredAndAppend(field_for_credentials(namespaceContent, "credentialsId", namespaceComment), collector,
                       CRED_TYPE_SECRET, namespaceComment, "credentialsId")
    #process deployParameters
    processParametersAndAppend("deployParameters", namespaceContent, collector, tenantName, cloudName, namespaceName, comment=namespaceComment)
    #process e2eParameters
    processParametersAndAppend("e2eParameters", namespaceContent, collector, tenantName, cloudName, namespaceName, comment=namespaceComment)
    #process technicalConfigurationParameters
    processParametersAndAppend("technicalConfigurationParameters", namespaceContent, collector, tenantName, cloudName, namespaceName, comment=namespaceComment)

def getApplicationCreds(appContent, tenantName, cloudName, collector, namespaceName=""):
    appName = appContent["name"]
    if namespaceName :
        comment = f"namespace {namespaceName} application {appName}"
    else:
        comment = f"cloud {cloudName} application {appName}"
    #process deployParameters
    processParametersAndAppend("deployParameters", appContent, collector, tenantName, cloudName, namespaceName, comment=comment)
    #process technicalConfigurationParameters
    processParametersAndAppend("technicalConfigurationParameters", appContent, collector, tenantName, cloudName, namespaceName, comment=comment)

def writeCredToYaml(credItem, credsYaml) :
    cred = credItem["cred"]
    comment = credItem["comment"]  # Reserved for provenance metadata; separate files planned.
    newCred = yaml.load("{}")
    #newCred.insert(1, "credentialsId", cred["credentialsId"])
    newCred.insert(1, "type", cred["type"])
    if (cred["type"] == CRED_TYPE_USERPASS) :
        data = yaml.load("{}")
        data.insert(1, "username", "envgeneNullValue")
        data.insert(1, "password", "envgeneNullValue")
        newCred["data"] = data
    elif (cred["type"] == CRED_TYPE_SECRET):
        data = yaml.load("{}")
        data.insert(1, "secret", "envgeneNullValue")
        newCred["data"] = data
    elif (cred["type"] == CRED_TYPE_VAULT):
        data = yaml.load("{}")
        data.insert(1, "roleId", "envgeneNullValue")
        data.insert(1, "secretId", "envgeneNullValue")
        data.insert(1, "path", "envgeneNullValue")
        data.insert(1, "namespace", "envgeneNullValue")
        newCred["data"] = data
    store_value_to_yaml(credsYaml, cred["credentialsId"], newCred)
    return credsYaml

def add_local_placeholders(credsYaml, collector):
    count = 0
    for cred_id, (cred_type, comment) in collector.referenced_creds.items():
        if cred_id not in credsYaml:
            count = count + 1
            writeCredToYaml({"cred": {"credentialsId": cred_id, "type": cred_type}, "comment": comment}, credsYaml)
    logger.info("%s credentials created" % count)

def reject_undeclared_builtin_creds(credsYaml, collector):
    undeclared = {cred_id: reference for cred_id, reference in collector.builtin_refs.items()
                  if cred_id not in credsYaml}
    if not undeclared:
        return
    references = "\n".join(f"  - {comment}, field: '{field_name}', credId: '{cred_id}'"
                           for cred_id, (comment, field_name) in undeclared.items())
    raise ValidationError(
        "Following built-in credential references point to credIds that no source declares. In external credential mode "
        f"EnvGene does not auto-generate them:\n{references}\n"
        "Declare each credId in the Credential Template, the Cloud Passport credentials file, or a Shared "
        "Credentials File, for example:\n"
        f"{next(iter(undeclared))}:\n"
        "  type: external\n"
        f"  secretStore: {DEFAULT_SECRET_STORE}\n"
        "  remoteRefPath: <path in the Secret Store>")

def add_generated_external_creds(credsYaml, collector, render_context):
    missing_creds = {cred_id: reference for cred_id, reference in collector.referenced_creds.items()
                     if cred_id not in credsYaml}
    if not missing_creds:
        return
    current_env = render_context.ctx.current_env
    remote_ref_path = f"{current_env['cloud']}/{current_env['name']}"
    for cred_id, (cred_type, comment) in missing_creds.items():
        cred = CommentedMap()
        cred["type"] = CRED_TYPE_EXTERNAL
        cred["secretStore"] = DEFAULT_SECRET_STORE
        cred["remoteRefPath"] = remote_ref_path
        if cred_type == CRED_TYPE_USERPASS:
            cred["properties"] = [{"name": "username"}, {"name": "password"}]
        store_value_to_yaml(credsYaml, cred_id, cred, comment)
    logger.info(f"Generated external credentials: {list(missing_creds)}")


def findSharedCredentials(cred_names, env_dir, instances_dir) -> dict:
    pending_names = set(cred_names)
    found_paths = {}    
    if not pending_names:
        return found_paths
    
    levels = [
        Path(env_dir) / "Inventory",
        Path(env_dir).parent,
        Path(instances_dir),
    ]    
    cred_dir_names = ["credentials", "Credentials", "shared-credentials"]
    
    for level in levels:
        for dir_name in cred_dir_names:
            directory = level / dir_name
            if not directory.is_dir():
                continue                
            for cred_name in list(pending_names):
                for ext in SHARED_CRED_EXTENSIONS:
                    potential_file = directory / f"{cred_name}{ext}"                    
                    if potential_file.is_file():
                        found_paths[cred_name] = potential_file
                        pending_names.remove(cred_name)
                        logger.info(f"Shared credentials '{cred_name}' found in '{potential_file}'")
                        break                        
                if not pending_names:
                    return found_paths                    
    if pending_names:
        raise FileNotFoundError(f"Shared credentials with keys {sorted(pending_names)} not found.")


def readSharedCreds(envDir, instancesDir, inventoryYaml, render_context) :
    shared_sources = []
    if ("sharedMasterCredentialFiles" in inventoryYaml["envTemplate"]) :
        sharedDictFileNames = inventoryYaml["envTemplate"]["sharedMasterCredentialFiles"]
        logger.info(f"Inventory shared master creds list: \n{dump_as_yaml_format(sharedDictFileNames)}")
        credFilePaths = findSharedCredentials(sharedDictFileNames, envDir, instancesDir)
        for credFileName in sharedDictFileNames :
            credFilePath = credFilePaths[credFileName]
            credText = openFileAsString(credFilePath)
            credYaml = readYaml(credText, context=f"File: {credFilePath}")
            if any(marker in credText for marker in JINJA_MARKERS):
                credYaml = render_context.render_from_obj_to_obj(credYaml)
            logger.info(f"Read {len(credYaml)} shared master credentials from {credFilePath}")
            shared_sources.append((credYaml, f"shared credentials: {credFilePath.name}"))
    return shared_sources

def create_credentials(envDir, instancesDir, inventoryYaml, credential_sources, render_context) :
    env_instance_store = current_env_instance_store()
    credential_mode = env_instance_store.credential_mode
    logger.info(f"Start to create credentials: envDir={envDir}, instancesDir={instancesDir}, mode={credential_mode}")
    credsSchema = f"{get_schema_dir()}/credential.schema.json"
    collector = CredentialCollector(credential_mode)
    #tenant
    envDir = Path(envDir)
    tenantFileName = envDir / "tenant.yml"
    logger.info(f"Processing tenant")
    tenantYaml = env_instance_store.get(tenantFileName)
    tenantName = tenantYaml["name"]
    getTenantCreds(tenantYaml, tenantName, collector)
    #cloud
    cloudFileName = envDir / "cloud.yml"
    logger.info(f"Processing cloud")
    cloudYaml = env_instance_store.get(cloudFileName)
    cloudName = cloudYaml["name"]
    getCloudCreds(cloudYaml, tenantName, cloudName, collector)
    #bgd object
    bgdFileName = envDir / "bg_domain.yml"
    logger.info(f"Processing bg domain")
    if env_instance_store.exists(bgdFileName):
        bgd_yaml = env_instance_store.get(bgdFileName)
        get_bg_domain_creds(bgd_yaml, bgd_yaml["name"], collector)
    else:
        logger.info("Bg domain doesn't exist")
    # iterate through cloud applications and create cred definitions
    applications = env_instance_store.list(envDir / "Applications" / "*.yml")
    for appPath in applications :
        getApplicationCreds(env_instance_store.get(appPath), tenantName, cloudName, collector)
    # iterate through namespaces and create cred definitions
    namespaceNameMap = {}
    namespaces = sorted(env_instance_store.list(envDir / "Namespaces" / "*" / "namespace.yml"), key=str)
    for namespacePath in namespaces :
        namespaceYaml = env_instance_store.get(namespacePath)
        namespaceKey = extract_namespace_from_namespace_path(namespacePath)
        namespaceName = namespaceYaml["name"]
        namespaceNameMap[namespaceKey] = namespaceName
        getNamespaceCreds(namespaceYaml, tenantName, cloudName, namespaceName, collector)
    # iterate through namespace applications and create cred definitions
    applications = sorted(env_instance_store.list(envDir / "Namespaces" / "*" / "Applications" / "*.yml"), key=str)
    for appPath in applications :
        namespaceKey = extract_namespace_from_application_path(appPath)
        namespaceName = namespaceNameMap[namespaceKey]
        getApplicationCreds(env_instance_store.get(appPath), tenantName, cloudName, collector, namespaceName)

    reject_misplaced_references(collector)
    credYamlPath = envDir / "Credentials" / "credentials.yml"
    if credential_mode == CredentialMode.LOCAL and env_instance_store.exists(credYamlPath):
        env_creds_map = env_instance_store.get(credYamlPath)
    else:
        env_creds_map = yaml.load("{}")
    logger.info(f'"Saving credentials to file: {credYamlPath}')
    sources_by_precedence = [*credential_sources, *readSharedCreds(envDir, instancesDir, inventoryYaml, render_context)]
    for source_creds, source_comment in sources_by_precedence:
        for cred_id, cred in source_creds.items():
            store_value_to_yaml(env_creds_map, cred_id, cred, source_comment)
    if credential_mode == CredentialMode.EXTERNAL:
        reject_undeclared_builtin_creds(env_creds_map, collector)
        add_generated_external_creds(env_creds_map, collector, render_context)
    else:
        add_local_placeholders(env_creds_map, collector)
    validate_cred_types(env_creds_map, credential_mode, credYamlPath)
    warn_unused_external_creds(env_creds_map, collector)
    validate_yaml_by_scheme_or_fail(input_yaml_content=env_creds_map, schema_file_path=credsSchema)
    env_instance_store.put(credYamlPath, env_creds_map)
    env_instance_store.beautify(credYamlPath, credsSchema)
