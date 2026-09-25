import os
import textwrap
from pathlib import Path

import jsonschema
import pytest
import yaml

from envgenehelper import openYaml, get_cred_config, extra_creds_scope
from envgenehelper.config_helper import get_regdef_v2_schema
from pipeline.pipeline_parameters import PipelineParametersHandler
from regdefv2_adapter.regdefv2_adapter import run_regdefv2_adapter

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
    "helmConfig": {"helmTargetStaging": "helm-staging", "helmTargetRelease": "helm-release"},
    "goConfig": {"goTargetSnapshot": "go-snapshot", "goTargetRelease": "go-release", "goProxyRepository": "go-proxy"},
    "helmAppConfig": {
        "helmStagingRepoName": "x", "helmReleaseRepoName": "x", "helmGroupRepoName": "x", "helmDevRepoName": "x",
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
      PUB_REG_REPOSITORY: "my-repo"
      HELM_REPO_BASE_URL: "https://helm.example.com"
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
    rendered_regdefs_dir = tmp_path / "tmp" / "render" / "env-01" / "RegDefs"
    rendered_regdefs_dir.mkdir(parents=True)
    (rendered_regdefs_dir / "registry-1.yml").write_text(yaml.safe_dump(V1_REGDEF))

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

    with extra_creds_scope():
        yield


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
        for section in ("dockerConfig", "helmConfig", "helmAppConfig"):
            assert synthesized[section] == {**V1_REGDEF[section], **synthesized[section]}
            assert synthesized[section]["authConfig"] == "pub-reg-auth"
        assert synthesized["mavenConfig"]["repositoryDomainName"] == V1_REGDEF["mavenConfig"]["repositoryDomainName"]
        assert synthesized["dockerConfig"] == {**V1_REGDEF["dockerConfig"], "authConfig": "pub-reg-auth"}
        assert synthesized["helmConfig"]["repositoryDomainName"] == "https://helm.example.com"
        assert synthesized["helmAppConfig"]["repositoryDomainName"] == "https://helm.example.com"
        assert synthesized["goConfig"]["repositoryDomainName"] == V1_REGDEF["mavenConfig"]["repositoryDomainName"]

        assert get_cred_config()["transient-pub-reg-creds"]["data"] == {"username": "key", "password": "secret"}

    @pytest.mark.unit
    def test_gcp_synthesizes_schema_valid_v2_regdef(self, tmp_path):
        (tmp_path / "tmp" / "templates" / "parameters" / "pubreg.yaml").write_text(textwrap.dedent("""\
            name: "pubreg"
            parameters:
              MAVEN_PROVIDER: "gcp"
              PUB_REG_PROVIDER: "gcp"
              PUB_REG_METHOD: "service_account"
              PUB_REG_SECRET: "secret"
              PUB_REG_PROJECT: "my-project"
              PUB_REG_SA_EMAIL: "sa@my-project.iam.gserviceaccount.com"
              HELM_REPO_BASE_URL: "https://helm.example.com"
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

        assert get_cred_config()["transient-pub-reg-creds"]["data"] == {"secret": "secret"}

    @pytest.mark.unit
    @pytest.mark.parametrize("missing", ["PUB_REG_KEY", "PUB_REG_SECRET", "PUB_REG_REGION", "PUB_REG_DOMAIN", "PUB_REG_REPOSITORY"])
    def test_aws_secret_requires_all_params(self, tmp_path, missing):
        paramset = "\n".join(line for line in PUBREG_PARAMSET.splitlines() if f"{missing}:" not in line)
        (tmp_path / "tmp" / "templates" / "parameters" / "pubreg.yaml").write_text(paramset)

        with pytest.raises(ValueError, match=missing):
            run_regdefv2_adapter(_ctx())

    @pytest.mark.unit
    def test_helm_sections_fail_schema_without_helm_domain_param(self, tmp_path):
        paramset = "\n".join(line for line in PUBREG_PARAMSET.splitlines() if "HELM_REPO_BASE_URL:" not in line)
        (tmp_path / "tmp" / "templates" / "parameters" / "pubreg.yaml").write_text(paramset)

        with pytest.raises(jsonschema.ValidationError, match="repositoryDomainName"):
            run_regdefv2_adapter(_ctx())

    @pytest.mark.unit
    def test_gcp_service_account_requires_secret(self, tmp_path):
        (tmp_path / "tmp" / "templates" / "parameters" / "pubreg.yaml").write_text(textwrap.dedent("""\
            name: "pubreg"
            parameters:
              MAVEN_PROVIDER: "gcp"
              PUB_REG_PROVIDER: "gcp"
              PUB_REG_METHOD: "service_account"
              PUB_REG_KEY: "key"
            """))

        with pytest.raises(ValueError, match="PUB_REG_SECRET"):
            run_regdefv2_adapter(_ctx())

    @pytest.mark.unit
    def test_anonymous_method_does_not_require_key_or_secret(self, tmp_path):
        (tmp_path / "tmp" / "templates" / "parameters" / "pubreg.yaml").write_text(textwrap.dedent("""\
            name: "pubreg"
            parameters:
              MAVEN_PROVIDER: "aws"
              PUB_REG_PROVIDER: "aws"
              PUB_REG_METHOD: "anonymous"
              HELM_REPO_BASE_URL: "https://helm.example.com"
            """))
        ctx = _ctx()

        run_regdefv2_adapter(ctx)

        synthesized = openYaml(ctx.transient_regdefs_dir / "registry-1.yml")
        auth_config = synthesized["authConfig"]["pub-reg-auth"]
        assert auth_config["authMethod"] == "anonymous"
        assert "credentialsId" not in auth_config
        assert "authType" not in auth_config
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
