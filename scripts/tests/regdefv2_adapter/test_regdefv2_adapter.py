import os
import textwrap
from pathlib import Path

import jsonschema
import pytest
import yaml

from envgenehelper import openYaml
from envgenehelper.config_helper import get_regdef_v2_schema
from pipeline.pipeline_parameters import PipelineParametersHandler
from regdefv2_adapter.regdefv2_adapter import PUBREG_CREDS_TMP_FILE, run_regdefv2_adapter

V1_REGDEF = {
    "name": "registry-1",
    "credentialsId": "registry-cred",
    "mavenConfig": {
        "repositoryDomainName": "https://my-domain-111122223333.d.codeartifact.us-east-1.amazonaws.com/maven/my-repo/",
        "fullRepositoryUrl": "https://my-domain-111122223333.d.codeartifact.us-east-1.amazonaws.com/maven/my-repo/",
        "targetSnapshot": "snapshot",
        "targetStaging": "staging",
        "targetRelease": "release",
        "releaseGroup": "",
        "snapshotGroup": "",
    },
    "dockerConfig": {
        "snapshotUri": "x", "stagingUri": "x", "releaseUri": "x", "groupUri": "x",
        "snapshotRepoName": "x", "stagingRepoName": "x", "releaseRepoName": "x", "groupName": "x",
    },
}

CLOUD_TEMPLATE = textwrap.dedent("""\
    ---
    name: "{{current_env.cloudNameWithCluster}}"
    apiUrl: ""
    apiPort: ""
    privateUrl: ""
    publicUrl: ""
    dashboardUrl: ""
    labels: []
    defaultCredentialsId: ""
    protocol: "https"
    deployParameters: {}
    e2eParameters: {}
    technicalConfigurationParameters: {}
    deployParameterSets: []
    e2eParameterSets: ["pubreg"]
    technicalConfigurationParameterSets: []
    mergeDeployParametersAndE2EParameters: false
    dbMode: "db"
    databases: []
    maasConfig:
      credentialsId: ""
      maasUrl: ""
      maasInternalAddress: ""
      enable: false
    vaultConfig:
      url: ""
      credentialsId: ""
      enable: false
    dbaasConfigs: []
    consulConfig:
      tokenSecret: ""
      publicUrl: ""
      enabled: false
      internalUrl: ""
    """)

TEMPLATE_DESCRIPTOR = textwrap.dedent("""\
    tenant: "{{templates_dir}}/env_templates/simple/tenant.yml.j2"
    cloud: "{{templates_dir}}/env_templates/simple/cloud.yml.j2"
    namespaces: []
    """)

PUBREG_PARAMSET = textwrap.dedent("""\
    name: "pubreg"
    parameters:
      MAVEN_PROVIDER: "aws"
      PUB_REG_PROVIDER: "aws"
      PUB_REG_METHOD: "secret"
      PUB_REG_KEY: "key"
      PUB_REG_SECRET: "secret"
      PUB_REG_DOMAIN: "my-domain"
      PUB_REG_REGION: "us-east-1"
    """)


@pytest.fixture(autouse=True)
def pipeline_env(monkeypatch, tmp_path):
    monkeypatch.setenv("CI_PROJECT_DIR", str(tmp_path))
    monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01")
    monkeypatch.setenv("ENV_BUILDER", "false")
    monkeypatch.setenv("GENERATE_EFFECTIVE_SET", "false")
    monkeypatch.setenv("PIPELINE_TYPE", "")
    monkeypatch.setenv("APPLICATION_VERSIONS", "")
    monkeypatch.setenv("JSON_SCHEMAS_DIR", str(Path(__file__).resolve().parents[3] / "schemas"))

    (tmp_path / "configuration").mkdir()
    (tmp_path / "configuration" / "config.yml").write_text("crypt: false\n")
    (tmp_path / "configuration" / "credentials").mkdir()
    (tmp_path / "configuration" / "credentials" / "credentials.yml").write_text("{}\n")

    env_dir = tmp_path / "environments" / "cluster-01" / "env-01"
    (env_dir / "Inventory").mkdir(parents=True)
    (env_dir / "Inventory" / "env_definition.yml").write_text(yaml.safe_dump({
        "inventory": {"environmentName": "env-01"},
        "envTemplate": {"name": "simple"},
    }))

    regdefs_dir = tmp_path / "regdefs"
    regdefs_dir.mkdir()
    (regdefs_dir / "registry-1.yml").write_text(yaml.safe_dump(V1_REGDEF))

    templates_dir = tmp_path / "tmp" / "templates"
    env_templates_dir = templates_dir / "env_templates"
    env_templates_dir.mkdir(parents=True)
    (env_templates_dir / "simple.yml").write_text(TEMPLATE_DESCRIPTOR)
    simple_dir = env_templates_dir / "simple"
    simple_dir.mkdir()
    (simple_dir / "cloud.yml.j2").write_text(CLOUD_TEMPLATE)

    parameters_dir = templates_dir / "parameters"
    parameters_dir.mkdir()
    (parameters_dir / "pubreg.yaml").write_text(PUBREG_PARAMSET)


def _ctx() -> PipelineParametersHandler:
    return PipelineParametersHandler.from_env()


class TestRegdefV2Adapter:
    @pytest.mark.unit
    def test_aws_synthesizes_schema_valid_v2_regdef_from_cloud_e2e_parameters(self):
        ctx = _ctx()

        run_regdefv2_adapter(ctx)

        synthesized = openYaml(ctx.transient_regdefs_dir / "registry-1.yml")
        assert "fullRepositoryUrl" not in synthesized["mavenConfig"]
        jsonschema.validate(instance=synthesized, schema=get_regdef_v2_schema())

        creds = openYaml(PUBREG_CREDS_TMP_FILE)
        assert creds["transient-pub-reg-creds"]["data"]["username"] == "key"

    @pytest.mark.unit
    def test_gcp_synthesizes_schema_valid_v2_regdef(self, tmp_path):
        (tmp_path / "tmp" / "templates" / "parameters" / "pubreg.yaml").write_text(textwrap.dedent("""\
            name: "pubreg"
            parameters:
              MAVEN_PROVIDER: "gcp"
              PUB_REG_PROVIDER: "gcp"
              PUB_REG_METHOD: "service_account"
              PUB_REG_KEY: "key"
              PUB_REG_SECRET: "secret"
              PUB_REG_PROJECT: "my-project"
              PUB_REG_SA_EMAIL: "sa@my-project.iam.gserviceaccount.com"
            """))
        ctx = _ctx()

        run_regdefv2_adapter(ctx)

        synthesized = openYaml(ctx.transient_regdefs_dir / "registry-1.yml")
        auth_config = synthesized["authConfig"]["pub-reg-auth"]
        assert auth_config["provider"] == "gcp"
        assert auth_config["authMethod"] == "service_account"
        assert auth_config["authType"] == "shortLived"
        assert auth_config["gcpRegProject"] == "my-project"
        assert auth_config["gcpRegSAEmail"] == "sa@my-project.iam.gserviceaccount.com"
        jsonschema.validate(instance=synthesized, schema=get_regdef_v2_schema())

    @pytest.mark.unit
    def test_azure_synthesizes_schema_valid_v2_regdef(self, tmp_path):
        (tmp_path / "tmp" / "templates" / "parameters" / "pubreg.yaml").write_text(textwrap.dedent("""\
            name: "pubreg"
            parameters:
              MAVEN_PROVIDER: "azure"
              PUB_REG_PROVIDER: "azure"
              PUB_REG_METHOD: "oauth2"
              PUB_REG_KEY: "key"
              PUB_REG_SECRET: "secret"
              PUB_REG_TENANT_ID: "tenant-1"
              PUB_REG_ACR_NAME: "myacr"
            """))
        ctx = _ctx()

        run_regdefv2_adapter(ctx)

        synthesized = openYaml(ctx.transient_regdefs_dir / "registry-1.yml")
        auth_config = synthesized["authConfig"]["pub-reg-auth"]
        assert auth_config["provider"] == "azure"
        assert auth_config["authType"] == "shortLived"
        assert auth_config["azureTenantId"] == "tenant-1"
        assert auth_config["azureACRName"] == "myacr"
        jsonschema.validate(instance=synthesized, schema=get_regdef_v2_schema())

    @pytest.mark.unit
    def test_anonymous_method_does_not_require_key_or_secret(self, tmp_path):
        (tmp_path / "tmp" / "templates" / "parameters" / "pubreg.yaml").write_text(textwrap.dedent("""\
            name: "pubreg"
            parameters:
              MAVEN_PROVIDER: "aws"
              PUB_REG_PROVIDER: "aws"
              PUB_REG_METHOD: "anonymous"
            """))
        ctx = _ctx()

        run_regdefv2_adapter(ctx)

        synthesized = openYaml(ctx.transient_regdefs_dir / "registry-1.yml")
        auth_config = synthesized["authConfig"]["pub-reg-auth"]
        assert auth_config["authMethod"] == "anonymous"
        jsonschema.validate(instance=synthesized, schema=get_regdef_v2_schema())

    @pytest.mark.unit
    def test_already_v2_regdef_is_copied_as_is(self, tmp_path):
        old_v2 = {
            "version": "2.0",
            "name": "registry-1",
            "authConfig": {"old-auth": {"provider": "nexus", "authMethod": "user_pass", "credentialsId": "old-cred"}},
            "mavenConfig": {
                "repositoryDomainName": "https://my-domain-111122223333.d.codeartifact.us-east-1.amazonaws.com/maven/my-repo/",
                "authConfig": "old-auth",
                "targetSnapshot": "snapshot", "targetStaging": "staging", "targetRelease": "release",
            },
        }
        (tmp_path / "regdefs" / "registry-1.yml").write_text(yaml.safe_dump(old_v2))
        ctx = _ctx()

        run_regdefv2_adapter(ctx)

        kept = openYaml(ctx.transient_regdefs_dir / "registry-1.yml")
        assert kept == old_v2

    @pytest.mark.unit
    def test_nexus_provider_keeps_v1_no_synthesis(self, tmp_path):
        (tmp_path / "tmp" / "templates" / "parameters" / "pubreg.yaml").write_text(
            PUBREG_PARAMSET.replace('MAVEN_PROVIDER: "aws"', 'MAVEN_PROVIDER: "nexus"')
        )
        ctx = _ctx()

        run_regdefv2_adapter(ctx)

        assert ctx.transient_regdefs_dir is None
        assert os.environ["LOCAL_PUBREG_FILE"]

    @pytest.mark.unit
    def test_no_maven_provider_is_noop(self, tmp_path):
        (tmp_path / "tmp" / "templates" / "parameters" / "pubreg.yaml").write_text(
            "name: \"pubreg\"\nparameters: {}\n"
        )
        os.environ.pop("LOCAL_PUBREG_FILE", None)
        ctx = _ctx()

        run_regdefv2_adapter(ctx)

        assert ctx.transient_regdefs_dir is None
        assert "LOCAL_PUBREG_FILE" not in os.environ

    @pytest.mark.unit
    def test_committed_regdefs_dir_ignores_placement_mode(self, tmp_path):
        (tmp_path / "configuration" / "config.yml").write_text("crypt: false\napp_reg_defs_placement: root\n")

        ctx = _ctx()

        assert ctx.committed_regdefs_dir == tmp_path / "regdefs"
