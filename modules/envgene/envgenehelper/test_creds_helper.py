import yaml
import pytest

from .collections_helper import dump_as_yaml_format
from .creds_helper import CONCEALED_SECRET_MASK, CRED_TYPE_SECRET, CRED_TYPE_USERPASS, CRED_TYPE_VAULT, EXTERNAL_CREDENTIAL_TYPE, check_cred_value, check_is_cred, create_cred_definition, expand_cred_macro_and_return_value, get_cred_id_and_property_from_cred_macros, get_cred_id_from_cred_macros, get_cred_list_from_param, mask_sensitive, validate_creds
from .errors import ValidationError
from envgene_shared.utils.yaml_utils import openYaml

# CONST
TEST_TENANT = "test-tenant"
TEST_CLOUD = "test-cloud"
TEST_NAMESPACE = "test-namespace"

check_is_cred_test_data = [
    ('#creds{TEST_CREDS_LOGIN, TEST_CREDS_PASSWORD}', "test-cred", True),
    ('#credscl{TEST_CREDS_CLOUD_LOGIN, TEST_CREDS_CLOUD_PASSWORD}', "test-cred-cloud", True),
    ('#credsns{TEST_CREDS_NS_LOGIN, TEST_CREDS_NS_PASSWORD}', "test-cred-namespace", True),
    ('some_string #credsns{TEST_CREDS_NS_LOGIN, TEST_CREDS_NS_PASSWORD}', "test-cred-namespace", False),
    ("USERNAME1", "${creds.get(\"velero-s3-cred\").username}", True),
    ("USERNAME2", "${cmdb.creds.get(\"velero-s3-cred\").username}", True),
    ("PASSWORD1", "${creds.get('velero-s3-cred').password} ", True),
    ("PASSWORD2", '${creds.get(\"velero-s3-cred\").username}', True),
    ("PASSWORD3", '${creds.get("velero-s3-cred").username}', True),
    ("PARAM1", "NOT_A_CRED", False),
    ("PARAM2", False, False),
    ("CIP_NETSEASY_SECRET_KEY", "${creds.get('pic-secret-key').secret}", True),
    ("VMS_CERT_IN_BASE64", '${cmdb.creds.get( "smv-cert" ).secret}', True),
    ("TEST_CMDB_CREDS_GET_VAULT_ROLE", '${cmdb.creds.get("cmdb-creds-get-vault-cred-role" ).roleId}', True),
    ("TEST_CMDB_CREDS_GET_VAULT_SECRET_ID", '${cmdb.creds.get( "cmdb-creds-get-vault-cred-secret-id").secretId}', True),
    ("TEST_CMDB_CREDS_GET_VAULT_PATH", '${cmdb.creds.get( "cmdb-creds-get-vault-cred-path" ).path}', True),
    ("TEST_CMDB_CREDS_GET_VAULT_NAMESPACE", '${cmdb.creds.get(   "cmdb-creds-get-vault-cred-namespace"  ).namespace}',
     True),
    ("TEST_CMDB_CREDS_GET_PASSWORD_USERNAME", "${cmdb.creds.get('cmdb-creds-get-username-cred').username}", True),
    ("TEST_CMDB_CREDS_GET_PASSWORD_PASSWORD", "${cmdb.creds.get('cmdb-creds-get-password-cred').password}", True),
    ("TEST_CMDB_CREDS_GET_SECRET_PARAM", "${cmdb.creds.get('cmdb-creds-get-secret').secret}", True),
    ("TEST_CREDS_GET_VAULT_ROLE", '${cmdb.creds.get("creds-get-vault-cred-role").roleId}', True),
    ("TEST_CREDS_GET_VAULT_SECRET_ID", "${cmdb.creds.get( \"creds-get-vault-cred-secret-id\").secretId}", True),
    ("TEST_CREDS_GET_VAULT_PATH", '${cmdb.creds.get( "creds-get-vault-cred-path" ).path}', True),
    ("TEST_CREDS_GET_VAULT_NAMESPACE", '${cmdb.creds.get(   "creds-get-vault-cred-namespace"  ).namespace}', True),
    ("TEST_CREDS_GET_PASSWORD_USERNAME", "${cmdb.creds.get('creds-get-username-cred').username}", True),
    ("TEST_CREDS_GET_PASSWORD_PASSWORD", "${cmdb.creds.get('creds-get-password-cred').password}", True),
    ("TEST_CREDS_GET_SECRET_PARAM", "${cmdb.creds.get('creds-get-secret').secret}", True),
    ("TEST_SHARED_CREDS_TIBCO", "${cmdb.creds.get('cotib-integration-cred').username}", True),
    ("TEST_SHARED_CREDS_SERVICE_ACTIVATOR", "${cmdb.creds.get('activator-integration-cred').password}", True),
    ("SEVERAL_CREDS",
     "[default]\n        aws_access_key_id = ${creds.get(\"velero-s3-cred\").username}\n        aws_secret_access_key = ${creds.get(\"velero-s3-cred\").password}",
     True),
    (0, "${STORAGE_RWO_CLASS}", False),
    (2, "${cmdb.creds.get('creds-get-secret').secret}", True)
]


@pytest.mark.parametrize("param_key, param_value, is_cred", check_is_cred_test_data)
def test_check_is_cred(param_key, param_value, is_cred):
    assert check_is_cred(param_key,
                         param_value) == is_cred, f"Param {param_key}={param_value} expected cred parsing result should be: {is_cred}"


get_cred_list_from_param_test_data = [
    ('#creds{TEST_CREDS_LOGIN, TEST_CREDS_PASSWORD}', "test-cred",
     [create_cred_definition("test-cred", CRED_TYPE_USERPASS)]),
    ('#creds{TEST_CREDS_LOGIN,TEST_CREDS_PASSWORD}', "test-cred",
     [create_cred_definition("test-cred", CRED_TYPE_USERPASS)]),
    ('#credscl{TEST_CREDS_CLOUD_LOGIN, TEST_CREDS_CLOUD_PASSWORD}', "test-cred-cloud",
     [create_cred_definition(f"{TEST_TENANT}-{TEST_CLOUD}-test-cred-cloud", CRED_TYPE_USERPASS)]),
    ('#credsns{TEST_CREDS_NS_LOGIN, TEST_CREDS_NS_PASSWORD}', "test-cred-namespace",
     [create_cred_definition(f"{TEST_TENANT}-{TEST_CLOUD}-{TEST_NAMESPACE}-test-cred-namespace", CRED_TYPE_USERPASS)]),
    ("USERNAME1", "${creds.get(\"velero-s3-cred\").username}",
     [create_cred_definition("velero-s3-cred", CRED_TYPE_USERPASS)]),
    ("USERNAME2", "${cmdb.creds.get(\"velero-s3-cred\").username}",
     [create_cred_definition("velero-s3-cred", CRED_TYPE_USERPASS)]),
    ("PASSWORD1", "${creds.get('velero-s3-cred').password} ",
     [create_cred_definition("velero-s3-cred", CRED_TYPE_USERPASS)]),
    ("PASSWORD2", '${creds.get(\"velero-s3-cred\").username}',
     [create_cred_definition("velero-s3-cred", CRED_TYPE_USERPASS)]),
    ("PASSWORD3", '${creds.get("velero-s3-cred").username}',
     [create_cred_definition("velero-s3-cred", CRED_TYPE_USERPASS)]),
    ("CIP_NETSEASY_SECRET_KEY", "${creds.get('pic-secret-key').secret}",
     [create_cred_definition("pic-secret-key", CRED_TYPE_SECRET)]),
    ("VMS_CERT_IN_BASE64", '${cmdb.creds.get( "smv-cert" ).secret}',
     [create_cred_definition("smv-cert", CRED_TYPE_SECRET)]),
    ("TEST_CMDB_CREDS_GET_VAULT_ROLE", '${cmdb.creds.get("cmdb-creds-get-vault-cred-role" ).roleId}',
     [create_cred_definition("cmdb-creds-get-vault-cred-role", CRED_TYPE_VAULT)]),
    ("TEST_CMDB_CREDS_GET_VAULT_SECRET_ID", '${cmdb.creds.get( "cmdb-creds-get-vault-cred-secret-id").secretId}',
     [create_cred_definition("cmdb-creds-get-vault-cred-secret-id", CRED_TYPE_VAULT)]),
    ("TEST_CMDB_CREDS_GET_VAULT_PATH", '${cmdb.creds.get( "cmdb-creds-get-vault-cred-path" ).path}',
     [create_cred_definition("cmdb-creds-get-vault-cred-path", CRED_TYPE_VAULT)]),
    ("TEST_CMDB_CREDS_GET_VAULT_NAMESPACE", '${cmdb.creds.get(   "cmdb-creds-get-vault-cred-namespace"  ).namespace}',
     [create_cred_definition("cmdb-creds-get-vault-cred-namespace", CRED_TYPE_VAULT)]),
    ("TEST_CMDB_CREDS_GET_PASSWORD_USERNAME", "${cmdb.creds.get('cmdb-creds-get-username-cred').username}",
     [create_cred_definition("cmdb-creds-get-username-cred", CRED_TYPE_USERPASS)]),
    ("TEST_CMDB_CREDS_GET_PASSWORD_PASSWORD", "${cmdb.creds.get('cmdb-creds-get-password-cred').password}",
     [create_cred_definition("cmdb-creds-get-password-cred", CRED_TYPE_USERPASS)]),
    ("TEST_CMDB_CREDS_GET_SECRET_PARAM", "${cmdb.creds.get('cmdb-creds-get-secret').secret}",
     [create_cred_definition("cmdb-creds-get-secret", CRED_TYPE_SECRET)]),
    ("SEVERAL_CREDS",
     "[default]\n        aws_access_key_id = ${creds.get(\"velero-s3-cred\").username}\n        aws_secret_access_key = ${creds.get(\"velero-s3-cred-password\").password}",
     [create_cred_definition("velero-s3-cred", CRED_TYPE_USERPASS),
      create_cred_definition("velero-s3-cred-password", CRED_TYPE_USERPASS)]),
    (2, "${cmdb.creds.get('creds-get-secret').secret}", [create_cred_definition("creds-get-secret", CRED_TYPE_SECRET)]),
]


@pytest.mark.parametrize("param_key, param_value, expected", get_cred_list_from_param_test_data)
def test_get_cred_list_from_param(param_key, param_value, expected):
    assert get_cred_list_from_param(param_key, param_value, True, TEST_TENANT, TEST_CLOUD,
                                    TEST_NAMESPACE) == expected, f"Param {param_key}={param_value} expected cred list result should be: {dump_as_yaml_format(expected)}"


get_cred_list_from_yaml_test_data = [
    ("test_data/test_cred_param.yaml")
]


@pytest.mark.parametrize("yaml_file", get_cred_list_from_yaml_test_data)
def test_get_cred_list_from_yaml(yaml_file):
    testYaml = openYaml(yaml_file)
    for key in testYaml:
        param_key = key
        param_value = testYaml[key]["test_value"]
        expected = testYaml[key]["expected_result"]
        assert get_cred_list_from_param(param_key, param_value, True, TEST_TENANT, TEST_CLOUD,
                                        TEST_NAMESPACE) == expected, f"Param {param_key}={param_value} expected cred list result should be: {dump_as_yaml_format(expected)}"


get_cred_id_from_cred_macros_test_data = [
    ("${creds.get(\"velero-s3-cred\").username}", "velero-s3-cred"),
    ("${cmdb.creds.get(\"velero-s3-cred\").username}", "velero-s3-cred"),
    ("${creds.get('velero-s3-cred').password} ", "velero-s3-cred"),
    ('${creds.get(\"velero-s3-cred\").username}', "velero-s3-cred"),
    ('${creds.get("velero-s3-cred").username}', "velero-s3-cred"),
    ("", ""),
    (" ", ""),
    ("\"\"", ""),
    ("''", ""),
    ("${creds.get('pic-secret-key').secret}", "pic-secret-key"),
    ('${cmdb.creds.get( "smv-cert" ).secret}', "smv-cert"),
    ('${cmdb.creds.get("cmdb-creds-get-vault-cred-role" ).roleId}', "cmdb-creds-get-vault-cred-role"),
    ('${cmdb.creds.get( "cmdb-creds-get-vault-cred-secret-id").secretId}', "cmdb-creds-get-vault-cred-secret-id"),
    ('${cmdb.creds.get( "cmdb-creds-get-vault-cred-path" ).path}', "cmdb-creds-get-vault-cred-path"),
    ('${cmdb.creds.get(   "cmdb-creds-get-vault-cred-namespace"  ).namespace}', "cmdb-creds-get-vault-cred-namespace"),
    ("${cmdb.creds.get('cmdb-creds-get-username-cred').username}", "cmdb-creds-get-username-cred"),
    ("${cmdb.creds.get('cmdb-creds-get-password-cred').password}", "cmdb-creds-get-password-cred"),
    ("${cmdb.creds.get('cmdb-creds-get-secret').secret}", "cmdb-creds-get-secret"),
    ('${cmdb.creds.get("creds-get-vault-cred-role").roleId}', "creds-get-vault-cred-role"),
    ("${cmdb.creds.get( \"creds-get-vault-cred-secret-id\").secretId}", "creds-get-vault-cred-secret-id"),
    ('${cmdb.creds.get( "creds-get-vault-cred-path" ).path}', "creds-get-vault-cred-path"),
    ('${cmdb.creds.get(   "creds-get-vault-cred-namespace"  ).namespace}', "creds-get-vault-cred-namespace"),
    ("${cmdb.creds.get('creds-get-username-cred').username}", "creds-get-username-cred"),
    ("${cmdb.creds.get('creds-get-password-cred').password}", "creds-get-password-cred"),
    ("${cmdb.creds.get('creds-get-secret').secret}", "creds-get-secret"),
    ("${cmdb.creds.get('cotib-integration-cred').username}", "cotib-integration-cred"),
    ("${cmdb.creds.get('activator-integration-cred').password}", "activator-integration-cred"),
]


@pytest.mark.parametrize("param_value, expected_cred_id", get_cred_id_from_cred_macros_test_data)
def test_get_cred_id_from_cred_macros(param_value, expected_cred_id):
    assert get_cred_id_from_cred_macros(
        param_value) == expected_cred_id, f"Param {param_value} expected cred parsing result should be: {expected_cred_id}"


get_cred_list_from_param_without_update_test_data = [
    ('#creds{TEST_CREDS_LOGIN, TEST_CREDS_PASSWORD}', "test-cred",
     [create_cred_definition("test-cred", CRED_TYPE_USERPASS)]),
    ('#credscl{TEST_CREDS_CLOUD_LOGIN, TEST_CREDS_CLOUD_PASSWORD}', "test-cred-cloud",
     [create_cred_definition(f"test-cred-cloud", CRED_TYPE_USERPASS)]),
    ('#credsns{TEST_CREDS_NS_LOGIN, TEST_CREDS_NS_PASSWORD}', "test-cred-namespace",
     [create_cred_definition(f"test-cred-namespace", CRED_TYPE_USERPASS)]),
    ("USERNAME1", "${creds.get(\"velero-s3-cred\").username}",
     [create_cred_definition("velero-s3-cred", CRED_TYPE_USERPASS)]),
]


@pytest.mark.parametrize("param_key, param_value, expected", get_cred_list_from_param_without_update_test_data)
def test_get_cred_list_from_param_without_update(param_key, param_value, expected):
    assert get_cred_list_from_param(param_key,
                                    param_value) == expected, f"Param {param_key}={param_value} expected cred list result should be: {dump_as_yaml_format(expected)}"


get_cred_id_and_property_from_cred_macros_test_data = [
    ("${creds.get(\"velero-s3-cred\").username}", "velero-s3-cred", "username"),
    ("envgen.creds.get('cloud-deployer-username-cred').secret", "cloud-deployer-username-cred", "secret"),
    ("envgen.creds.get('cloud-deployer-username-cred').username", "cloud-deployer-username-cred", "username"),
    ("envgen.creds.get('cloud-deployer-username-cred').password", "cloud-deployer-username-cred", "password"),
    ("${cmdb.creds.get('cloud-deployer-username-cred').password}", "cloud-deployer-username-cred", "password"),
]


@pytest.mark.parametrize("cred_macros, expected_cred_id, expected_property",
                         get_cred_id_and_property_from_cred_macros_test_data)
def test_get_cred_id_and_property_from_cred_macros(cred_macros, expected_cred_id, expected_property):
    cred_id, cred_property = get_cred_id_and_property_from_cred_macros(cred_macros)
    assert cred_id == expected_cred_id, f"Invalid cred_id in cred macros {cred_macros}, expected {expected_cred_id}, got {cred_id}"
    assert cred_property == expected_property, f"Invalid cred property in cred macros {cred_macros}, expected {expected_property}, got {cred_property}"


expand_cred_macro_and_return_param_map_test_data = [
    ("USERNAME1", "${creds.get(\"ci-atp-auth-cred\").username}", "ci-atp-auth-user"),
    ("PASSWORD1", "${creds.get('ci-atp-auth-cred').password} ", "ci-atp-auth-password"),
    ("USERNAME2", "${cmdb.creds.get(\"cmdb-creds\").username}",
     "[encrypted:AES256_Fernet]gAAAAABly1j-qcE3_bG0HrnbtPi8ACfcEenXixMQK7tARsI_arZRDri8fEhg5UWfNvirHaOm1oiFO9ds3PfiXMn3ygdhnCV_zQ=="),
    ("PASSWORD2", "${creds.get('cmdb-creds').password} ",
     "[encrypted:AES256_Fernet]gAAAAABly1j-N4FzSjUH4FnQPrRny1RdxXliVw50dOLVOO6FAFx4LjICIQG8fPwqDh8bPiiGZVGWbGerIGW9YafwdjEc_Ig_L8e2P48NOuUUBnVCjvs3ZK6QviIsbBVBgh-9FA0pwfHA"),
    (
        "SEVERAL_CREDS",
        "[default]\n        aws_access_key_id = ${creds.get(\"velero-s3-cred\").username}\n        aws_secret_access_key = ${creds.get(\"velero-s3-cred\").password}",
        "[default]\n        aws_access_key_id = velero-s3-cred-user\n        aws_secret_access_key = velero-s3-cred-password"
    ),
    (2, "${cmdb.creds.get('test-not-rewrite-cred').secret}", "DO_NOT_REWRITE_SECRET"),
]


@pytest.mark.parametrize("param_key, param_value, expected", expand_cred_macro_and_return_param_map_test_data)
def test_get_cred_list_from_param_without_update(param_key, param_value, expected):
    credsYaml = openYaml("test_data/test_credentials.yaml")
    assert expand_cred_macro_and_return_value(param_key, param_value,
                                              credsYaml) == expected, f"Param {param_key}={param_value} expected expanded cred should be: {dump_as_yaml_format(expected)}"


def test_mask_sensitive_creds():
    creds = openYaml("test_data/test_crypt.yaml")
    creds_masked = mask_sensitive(creds)

    assert creds_masked.get("first_cred").get("data").get("secret") == CONCEALED_SECRET_MASK
    assert creds_masked.get("second_cred").get("data").get("password") == CONCEALED_SECRET_MASK
    assert creds_masked.get("second_cred").get("data").get("username") == CONCEALED_SECRET_MASK


# ===================== envgeneNullValue validation (UC-NVV-2/3/4) =====================
#
# Credential scope of the use cases in docs/use-cases/envgene-null-value-validation.md.

def _cred(cred_type, **data):
    return {"type": cred_type, "data": data}


@pytest.mark.parametrize(
    "cred_id, cred, expected",
    [
        ("db-cred", _cred("usernamePassword", username="u", password="p"), ""),
        ("db-cred", _cred("usernamePassword", username="envgeneNullValue", password="p"),
         "credId: db-cred - username or password is not set"),
        ("db-cred", _cred("usernamePassword", username="u", password="envgeneNullValue"),
         "credId: db-cred - username or password is not set"),
        ("consul-cred", _cred("secret", secret="s"), ""),
        ("consul-cred", _cred("secret", secret="envgeneNullValue"),
         "credId: consul-cred - secret is not set"),
        ("vault-cred", _cred(CRED_TYPE_VAULT, secretId="envgeneNullValue"),
         "credId: vault-cred - secretId is not set"),
        ("ext-cred", _cred(EXTERNAL_CREDENTIAL_TYPE, name="x"), ""),
    ],
    ids=["userpass-resolved", "userpass-null-username", "userpass-null-password",
         "secret-resolved", "secret-null", "vault-null", "external-ignored"],
)
def test_check_cred_value_null_detection(cred_id, cred, expected):
    assert check_cred_value(cred_id, cred) == expected


def _write_creds(creds_dir, credentials):
    creds_dir.mkdir(parents=True, exist_ok=True)
    (creds_dir / "credentials.yml").write_text(yaml.dump(credentials), encoding="utf-8")


RESOLVED_CREDS = {
    "dbaas-cluster-dba-cred": _cred("usernamePassword", username="dbaas-user", password="dbaas-password"),
    "consul-admin-cred": _cred("secret", secret="consul-admin-secret"),
}


def test_validate_creds_pass_when_resolved(tmp_path):
    creds_dir = tmp_path / "Credentials"
    _write_creds(creds_dir, RESOLVED_CREDS)
    validate_creds(str(creds_dir))


def test_unresolved_credential_blocks_pipeline(tmp_path):
    creds = dict(RESOLVED_CREDS)
    creds["dbaas-cluster-dba-cred"] = _cred("usernamePassword",
                                            username="envgeneNullValue", password="envgeneNullValue")
    creds_dir = tmp_path / "Credentials"
    _write_creds(creds_dir, creds)

    with pytest.raises(ValidationError) as exc_info:
        validate_creds(str(creds_dir))

    message = str(exc_info.value)
    assert "Error while validating credentials:" in message
    assert "credId: dbaas-cluster-dba-cred - username or password is not set" in message
    assert "consul-admin-cred" not in message


def test_multiple_unresolved_credentials_reported_together(tmp_path):
    creds = {
        "dbaas-cluster-dba-cred": _cred("usernamePassword",
                                        username="envgeneNullValue", password="envgeneNullValue"),
        "consul-admin-cred": _cred("secret", secret="envgeneNullValue"),
    }
    creds_dir = tmp_path / "Credentials"
    _write_creds(creds_dir, creds)

    with pytest.raises(ValidationError) as exc_info:
        validate_creds(str(creds_dir))

    message = str(exc_info.value)
    assert message.count("Error while validating credentials:") == 1
    assert "credId: dbaas-cluster-dba-cred - username or password is not set" in message
    assert "credId: consul-admin-cred - secret is not set" in message


def test_validate_creds_matching_is_case_insensitive(tmp_path):
    creds_dir = tmp_path / "Credentials"
    _write_creds(creds_dir, {"consol-cred": _cred("secret", secret="ENVGeneNullValue")})

    with pytest.raises(ValidationError) as exc_info:
        validate_creds(str(creds_dir))

    assert "credId: consol-cred - secret is not set" in str(exc_info.value)
