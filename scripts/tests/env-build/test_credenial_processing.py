from collections import OrderedDict
import textwrap

import pytest

from build_env.create_credentials import create_credentials
from build_env.render_config_env import EnvGenerator
from envgenehelper import CredentialMode, ValidationError, open_current_env_instance_store
from envgenehelper.yaml_helper import readYaml

TENANT = """name: tenant
credential: tenant-cred
deployParameters: {}
globalE2EParameters:
  environmentParameters: {}
"""

CLOUD = """name: cloud
defaultCredentialsId: cloud-cred
maasConfig:
  credentialsId: ""
vaultConfig:
  credentialsId: ""
consulConfig:
  tokenSecret: ""
dbaasConfigs:
  - credentialsId: dbaas-cred
deployParameters: {}
e2eParameters: {}
technicalConfigurationParameters: {}
"""

NAMESPACE = """name: env-app
credentialsId: ns-cred
deployParameters:
{deploy}
e2eParameters:
{e2e}
technicalConfigurationParameters:
{technical}
"""

EMPTY = "  {}"
EXTERNAL_DB = {
    "type": "external",
    "remoteRefPath": "template/db",
    "properties": [{"name": "username"}, {"name": "password"}],
}


def run_create_credentials(tmp_path, mode, deploy=EMPTY, e2e=EMPTY, technical=EMPTY, sources=(), existing=None,
                           shared_files=None):
    env_dir = tmp_path / "environments" / "cluster" / "env"
    shared_names = []
    for file_name, text in (shared_files or {}).items():
        shared_dir = env_dir / "Inventory" / "credentials"
        shared_dir.mkdir(parents=True, exist_ok=True)
        (shared_dir / file_name).write_text(text)
        shared_names.append(file_name.split(".")[0])
    inventory = readYaml("inventory: {}\nenvTemplate: {}\n")
    inventory["envTemplate"]["sharedMasterCredentialFiles"] = shared_names
    namespace_path = env_dir / "Namespaces" / "app" / "namespace.yml"
    creds_path = env_dir / "Credentials" / "credentials.yml"
    with open_current_env_instance_store(env_dir, mode) as store:
        store.put(env_dir / "tenant.yml", readYaml(TENANT))
        store.put(env_dir / "cloud.yml", readYaml(CLOUD))
        store.put(namespace_path, readYaml(NAMESPACE.format(deploy=deploy, e2e=e2e, technical=technical)))
        if existing:
            store.put(creds_path, readYaml(existing))
        render_context = EnvGenerator()
        render_context.ctx.current_env = OrderedDict(cloud="cloud-01", name="env-01")
        create_credentials(env_dir, tmp_path / "environments", inventory, list(sources), render_context)
        return store.get(creds_path), store.get(namespace_path), store, creds_path


def test_external_mode_keeps_declared_and_generates_undeclared(tmp_path):
    deploy = "  DB: ${creds.get('cred-a').password}\n  TOKEN: ${creds.get('cred-b').secret}"
    template_creds = readYaml(textwrap.dedent("""\
    cred-a:
      type: external
      remoteRefPath: template/a
      properties:
        - name: username
        - name: password
    """))

    creds, _, _, _ = run_create_credentials(tmp_path, CredentialMode.EXTERNAL, deploy=deploy,
                                            sources=[(template_creds, "template")])

    assert creds["cred-a"]["remoteRefPath"] == "template/a"
    assert creds["cred-b"] == {"type": "external", "secretStore": "default_store", "remoteRefPath": "cloud-01/env-01"}


def test_external_mode_generated_entry_has_both_properties_for_username_macro(tmp_path):
    creds, _, _, _ = run_create_credentials(tmp_path, CredentialMode.EXTERNAL,
                                            deploy="  USER: ${creds.get('report').username}")

    assert creds["report"]["properties"] == [{"name": "username"}, {"name": "password"}]


def test_external_mode_generates_entries_for_built_in_references(tmp_path):
    creds, _, _, _ = run_create_credentials(tmp_path, CredentialMode.EXTERNAL)

    assert {"tenant-cred", "cloud-cred", "dbaas-cred", "ns-cred"} <= set(creds)
    assert "properties" not in creds["cloud-cred"]
    assert creds["dbaas-cred"]["properties"] == [{"name": "username"}, {"name": "password"}]


def test_local_mode_has_no_external_entries(tmp_path):
    creds, _, _, _ = run_create_credentials(tmp_path, CredentialMode.LOCAL,
                                            deploy="  TOKEN: ${creds.get('cred-b').secret}")

    assert creds["cred-b"]["type"] == "secret"
    assert all(cred["type"] != "external" for cred in creds.values())


@pytest.mark.parametrize("present, expected", [
    (("template", "passport", "shared"), "shared"),
    (("template", "passport"), "passport"),
    (("passport", "shared"), "shared"),
    (("template", "shared"), "shared"),
    (("template",), "template"),
])
def test_external_mode_precedence(tmp_path, present, expected):
    def source(name):
        return readYaml(f"db:\n  type: external\n  remoteRefPath: {name}\n"), name

    sources = [source(name) for name in ("template", "passport") if name in present]
    shared_files = {"shared.yml": "db:\n  type: external\n  remoteRefPath: shared\n"} if "shared" in present else None

    creds, _, _, _ = run_create_credentials(tmp_path, CredentialMode.EXTERNAL, deploy="  DB: ${creds.get('db').secret}",
                                            sources=sources, shared_files=shared_files)

    assert creds["db"]["remoteRefPath"] == expected


def test_external_mode_drops_previous_entries_and_local_mode_keeps_them(tmp_path):
    existing = textwrap.dedent("""\
    obsolete:
      type: external
      remoteRefPath: old
    kept:
      type: secret
      data:
        secret: value
    """)
    external_creds, _, _, _ = run_create_credentials(tmp_path / "external", CredentialMode.EXTERNAL, existing=existing)

    local_existing = textwrap.dedent("""\
    kept:
      type: secret
      data:
        secret: value
    """)
    local_creds, _, _, _ = run_create_credentials(tmp_path / "local", CredentialMode.LOCAL, existing=local_existing)

    assert "obsolete" not in external_creds
    assert "kept" in local_creds


@pytest.mark.parametrize("macro, expected", [
    ("${creds.get('db').password}", {"$type": "credRef", "credId": "db", "property": "password"}),
    ('${creds.get("db").username}', {"$type": "credRef", "credId": "db", "property": "username"}),
    ("${creds.get('db').secret}", {"$type": "credRef", "credId": "db"}),
])
def test_external_mode_rewrites_macro_to_cred_ref(tmp_path, macro, expected):
    deploy = f"  PARAM: {macro}\n  LIST:\n    - {macro}"
    e2e = f"  E2E_PARAM: {macro}"

    _, namespace, _, _ = run_create_credentials(tmp_path, CredentialMode.EXTERNAL, deploy=deploy, e2e=e2e)

    assert namespace["deployParameters"]["PARAM"] == expected
    assert namespace["deployParameters"]["LIST"][0] == expected
    assert namespace["e2eParameters"]["E2E_PARAM"] == expected


def test_local_mode_keeps_macro(tmp_path):
    macro = "${creds.get('db').password}"

    _, namespace, _, _ = run_create_credentials(tmp_path, CredentialMode.LOCAL, deploy=f"  PARAM: {macro}")

    assert namespace["deployParameters"]["PARAM"] == macro


@pytest.mark.parametrize("deploy", [
    "  PARAM: ${creds.get('db').roleId}",
    "  PARAM: oracle://${creds.get('db').username}:${creds.get('db').password}@host",
    "  PARAM: https://${creds.get('svc').username}@host",
    '  "#creds{user, pass}": db-cred',
])
def test_external_mode_rejects_unsupported_references(tmp_path, deploy):
    with pytest.raises(ValidationError):
        run_create_credentials(tmp_path, CredentialMode.EXTERNAL, deploy=deploy)


def test_external_mode_rejects_macro_in_technical_parameters(tmp_path):
    with pytest.raises(ReferenceError):
        run_create_credentials(tmp_path, CredentialMode.EXTERNAL,
                               technical="  PARAM: ${creds.get('db').password}")


def test_external_mode_rejects_declared_vault_app_role(tmp_path):
    shared_files = {"shared.yml": "role:\n  type: vaultAppRole\n  data:\n    roleId: a\n    secretId: b\n"
                                  "    path: c\n    namespace: d\n"}

    with pytest.raises(ValueError):
        run_create_credentials(tmp_path, CredentialMode.EXTERNAL, shared_files=shared_files)


def test_local_mode_rejects_cred_ref(tmp_path):
    deploy = "  PARAM:\n    $type: credRef\n    credId: db"

    with pytest.raises(ReferenceError):
        run_create_credentials(tmp_path, CredentialMode.LOCAL, deploy=deploy)


@pytest.mark.parametrize("file_name", ["shared.yml.j2", "shared.yaml.j2", "shared.yml"])
def test_shared_credentials_file_is_rendered_with_jinja(tmp_path, file_name):
    shared_files = {file_name: 'db:\n  type: external\n  remoteRefPath: "{{ current_env.cloud }}/{{ current_env.name }}/db"\n'}

    creds, _, _, _ = run_create_credentials(tmp_path, CredentialMode.EXTERNAL, shared_files=shared_files)

    assert creds["db"]["remoteRefPath"] == "cloud-01/env-01/db"


def test_shared_credentials_file_without_jinja_is_read_verbatim(tmp_path):
    shared_files = {"shared.yml": 'db:\n  type: secret\n  data:\n    secret: "$value-{x}"\n'}

    creds, _, _, _ = run_create_credentials(tmp_path, CredentialMode.LOCAL, shared_files=shared_files)

    assert creds["db"]["data"]["secret"] == "$value-{x}"
