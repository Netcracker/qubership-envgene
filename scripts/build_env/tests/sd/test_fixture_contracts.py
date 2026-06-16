"""
Fixture contract tests — read the Java test fixtures verbatim and assert
cross-file invariants that CmdbCliTest.java does not check explicitly.

These tests do NOT run Java code.  Their purpose is:
  1. Document UC specifications as executable assertions.
  2. Catch inconsistencies between fixture files (e.g. mapping keys vs directory names).
  3. Fail fast when someone edits a fixture manually and breaks a contract.

All fixture paths are under:
  build_effective_set_generator/effective-set-generator/src/test/resources/
  environments/cluster-01/pl-01/effective-set/
"""
import os
import sys
from pathlib import Path

import pytest

from scripts.build_env.tests.base_test import BaseTest

os.environ.setdefault("ENVIRONMENT_NAME", "env-01")
os.environ.setdefault("CLUSTER_NAME", "cluster-01")

_ESE_SCRIPTS = Path(__file__).resolve().parents[4] / "build_effective_set_generator" / "scripts"
if str(_ESE_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_ESE_SCRIPTS))

from envgenehelper.yaml_helper import openYaml

_FIXTURES = (
    Path(__file__).resolve().parents[4]
    / "build_effective_set_generator"
    / "effective-set-generator"
    / "src" / "test" / "resources"
    / "environments" / "cluster-01" / "pl-01" / "effective-set"
)

_SECURED_KEYS = {
    "DBAAS_AGGREGATOR_USERNAME", "DBAAS_AGGREGATOR_PASSWORD",
    "DBAAS_CLUSTER_DBA_CREDENTIALS_USERNAME", "DBAAS_CLUSTER_DBA_CREDENTIALS_PASSWORD",
    "MAAS_CREDENTIALS_USERNAME", "MAAS_CREDENTIALS_PASSWORD",
    "VAULT_TOKEN", "CONSUL_ADMIN_TOKEN", "SSL_SECRET_VALUE",
}


def _load(rel: str) -> dict:
    return dict(openYaml(_FIXTURES / rel))


def _exists(rel: str) -> bool:
    return (_FIXTURES / rel).exists()


# ---------------------------------------------------------------------------
# UC-ES-DEP-A14 / UC-ES-RUN-3 / UC-ES-CLN-3: mapping key consistency
# ---------------------------------------------------------------------------

class TestMappingKeyConsistency(BaseTest):
    """
    UC-ES-DEP-A14 / UC-ES-RUN-3 / UC-ES-CLN-3 — deployment, runtime, and cleanup
    mapping.yaml must all carry the same namespace keys; only the context segment
    of the path value differs.
    """

    def test_all_three_mapping_files_have_identical_key_sets(self):
        # UC-ES-DEP-A14 / RUN-3 / CLN-3: namespace keys in all three mapping files
        # must be exactly the same set.
        dep = set(_load("deployment/mapping.yaml").keys())
        run = set(_load("runtime/mapping.yaml").keys())
        cln = set(_load("cleanup/mapping.yaml").keys())
        assert dep == run == cln, (
            f"mapping.yaml key sets differ: deployment={dep}, runtime={run}, cleanup={cln}"
        )

    def test_deployment_mapping_values_contain_deployment_segment(self):
        # UC-ES-DEP-A14: every value in deployment/mapping.yaml must contain
        # "/effective-set/deployment/" — not runtime or cleanup.
        for key, val in _load("deployment/mapping.yaml").items():
            assert "/effective-set/deployment/" in val, (
                f"deployment mapping key '{key}' has wrong path: {val}"
            )

    def test_runtime_mapping_values_contain_runtime_segment(self):
        # UC-ES-RUN-3: values in runtime/mapping.yaml must contain "/effective-set/runtime/".
        for key, val in _load("runtime/mapping.yaml").items():
            assert "/effective-set/runtime/" in val, (
                f"runtime mapping key '{key}' has wrong path: {val}"
            )

    def test_cleanup_mapping_values_contain_cleanup_segment(self):
        # UC-ES-CLN-3: values in cleanup/mapping.yaml must contain "/effective-set/cleanup/".
        for key, val in _load("cleanup/mapping.yaml").items():
            assert "/effective-set/cleanup/" in val, (
                f"cleanup mapping key '{key}' has wrong path: {val}"
            )

    def test_mapping_keys_start_with_environments_prefix(self):
        # UC-ES-DEP-A14: values use /environments/... prefix as specified.
        for val in _load("deployment/mapping.yaml").values():
            assert val.startswith("/environments/"), (
                f"deployment mapping value must start with /environments/: {val}"
            )

    def test_deployment_mapping_namespace_folders_exist(self):
        # UC-ES-DEP-A14: each namespace folder referenced in deployment/mapping.yaml
        # must actually exist under deployment/.
        for key, val in _load("deployment/mapping.yaml").items():
            ns_folder = val.split("/effective-set/deployment/")[-1]
            assert (_FIXTURES / "deployment" / ns_folder).is_dir(), (
                f"namespace folder for key '{key}' does not exist: deployment/{ns_folder}"
            )

    def test_fixture_mapping_keys(self):
        # UC-ES-DEP-A14: cross-check exact fixture values from the Java test run.
        dep = _load("deployment/mapping.yaml")
        assert dep["pl-01-monitoring"] == (
            "/environments/cluster-01/pl-01/effective-set/deployment/monitoring-origin"
        )
        assert dep["pl-01-pg"] == (
            "/environments/cluster-01/pl-01/effective-set/deployment/pg"
        )


# ---------------------------------------------------------------------------
# UC-ES-DEP-16 / UC-ES-DEP-22 / UC-ES-DEP-23: deployment-parameters.yaml content
# ---------------------------------------------------------------------------

class TestDeploymentParametersContent(BaseTest):
    """
    UC-ES-DEP-16 / UC-ES-DEP-22 / UC-ES-DEP-23 — deployment-parameters.yaml
    for MONITORING contains mandatory identity keys, DBaaS URLs (enabled),
    and gateway URL formulas.
    """

    @pytest.fixture(autouse=True)
    def _params(self):
        self._p = _load(
            "deployment/monitoring-origin/MONITORING/values/deployment-parameters.yaml"
        )

    def test_mandatory_identity_keys_present(self):
        # UC-ES-DEP-16: predefined identity keys always written.
        # Note: MANAGED_BY lives in deploy-descriptor.yaml, not deployment-parameters.yaml.
        for key in ("APPLICATION_NAME", "NAMESPACE", "TENANTNAME",
                    "CLOUD_API_HOST", "CLOUD_API_PORT", "CLOUD_PROTOCOL",
                    "CLOUD_PUBLIC_HOST", "DEPLOYMENT_SESSION_ID"):
            assert key in self._p, f"mandatory key missing: {key}"

    def test_dbaas_enabled_and_urls_present(self):
        # UC-ES-DEP-22: DBaaS enabled → DBAAS_ENABLED true and URL keys present.
        assert self._p["DBAAS_ENABLED"] is True
        assert "API_DBAAS_ADDRESS" in self._p
        assert "DBAAS_AGGREGATOR_ADDRESS" in self._p

    def test_public_gateway_url_formula(self):
        # UC-ES-DEP-23: PUBLIC_GATEWAY_URL = {protocol}://public-gateway-{namespace}.{host}
        ns = self._p["NAMESPACE"]
        host = self._p["CLOUD_PUBLIC_HOST"]
        proto = self._p["CLOUD_PROTOCOL"]
        expected = f"{proto}://public-gateway-{ns}.{host}"
        assert self._p["PUBLIC_GATEWAY_URL"] == expected

    def test_private_gateway_url_formula(self):
        # UC-ES-DEP-23: PRIVATE_GATEWAY_URL = {protocol}://private-gateway-{namespace}.{host}
        ns = self._p["NAMESPACE"]
        host = self._p["CLOUD_PUBLIC_HOST"]
        proto = self._p["CLOUD_PROTOCOL"]
        expected = f"{proto}://private-gateway-{ns}.{host}"
        assert self._p["PRIVATE_GATEWAY_URL"] == expected

    def test_secured_keys_absent_from_deployment_parameters(self):
        # UC-ES-DEP-A6: SECURED_KEYS must not appear in deployment-parameters.yaml —
        # they belong in credentials.yaml only.
        found = _SECURED_KEYS & set(self._p.keys())
        assert not found, f"SECURED_KEYS must not be in deployment-parameters.yaml: {found}"


# ---------------------------------------------------------------------------
# UC-ES-DEP-A6: credentials.yaml content
# ---------------------------------------------------------------------------

class TestCredentialsContent(BaseTest):
    """
    UC-ES-DEP-A6 — credentials.yaml for MONITORING must contain K8S_TOKEN and
    the secured credential keys; none of these may appear in deployment-parameters.yaml.
    """

    @pytest.fixture(autouse=True)
    def _creds(self):
        self._c = _load(
            "deployment/monitoring-origin/MONITORING/values/credentials.yaml"
        )

    def test_k8s_token_in_credentials(self):
        # UC-ES-DEP-A6: K8S_TOKEN always written to credentials.yaml.
        assert "K8S_TOKEN" in self._c

    def test_secured_keys_present_in_credentials(self):
        # UC-ES-DEP-A6: SECURED_KEYS present in insecure params are moved here.
        # Fixture has DBaaS, MaaS, Consul credentials.
        for key in ("DBAAS_AGGREGATOR_USERNAME", "DBAAS_AGGREGATOR_PASSWORD",
                    "MAAS_CREDENTIALS_USERNAME", "MAAS_CREDENTIALS_PASSWORD",
                    "CONSUL_ADMIN_TOKEN"):
            assert key in self._c, f"secured key missing from credentials.yaml: {key}"

    def test_credentials_and_deployment_params_share_no_secured_keys(self):
        # UC-ES-DEP-A6: no key can be in both credentials.yaml and
        # deployment-parameters.yaml simultaneously.
        dep = set(_load(
            "deployment/monitoring-origin/MONITORING/values/deployment-parameters.yaml"
        ).keys())
        overlap = (_SECURED_KEYS | {"K8S_TOKEN"}) & dep
        assert not overlap, (
            f"keys present in both credentials and deployment-parameters: {overlap}"
        )


# ---------------------------------------------------------------------------
# UC-ES-DEP-20: collision-deployment-parameters.yaml
# ---------------------------------------------------------------------------

class TestCollisionDeploymentParameters(BaseTest):
    """
    UC-ES-DEP-20 — collision-deployment-parameters.yaml exists for every
    application; keys in it must not appear in deployment-parameters.yaml.
    """

    def test_collision_file_exists_for_monitoring(self):
        # UC-ES-DEP-20: file is always written (empty when no collisions).
        assert _exists(
            "deployment/monitoring-origin/MONITORING/values/collision-deployment-parameters.yaml"
        )

    def test_collision_file_exists_for_postgres(self):
        assert _exists(
            "deployment/pg/postgres/values/collision-deployment-parameters.yaml"
        )

    def test_collision_keys_absent_from_main_deployment_parameters(self):
        # UC-ES-DEP-20: keys routed to collision must be removed from main params.
        collision = _load(
            "deployment/monitoring-origin/MONITORING/values/collision-deployment-parameters.yaml"
        )
        if not collision:
            return  # empty fixture — no collision keys to check
        dep = _load(
            "deployment/monitoring-origin/MONITORING/values/deployment-parameters.yaml"
        )
        overlap = set(collision.keys()) & set(dep.keys())
        assert not overlap, (
            f"collision keys found in deployment-parameters.yaml: {overlap}"
        )


# ---------------------------------------------------------------------------
# UC-ES-DEP-15: DEPLOYMENT_SESSION_ID consistency across output files
# ---------------------------------------------------------------------------

class TestDeploymentSessionIdConsistency(BaseTest):
    """
    UC-ES-DEP-15 — DEPLOYMENT_SESSION_ID must be the same value in
    deployment-parameters.yaml and deploy-descriptor.yaml for the same run.
    """

    def test_session_id_matches_in_deployment_params_and_deploy_descriptor(self):
        # UC-ES-DEP-15: session ID written by CLI must be consistent.
        dep = _load(
            "deployment/monitoring-origin/MONITORING/values/deployment-parameters.yaml"
        )
        dd = _load(
            "deployment/monitoring-origin/MONITORING/values/deploy-descriptor.yaml"
        )
        assert dep["DEPLOYMENT_SESSION_ID"] == dd["DEPLOYMENT_SESSION_ID"], (
            "DEPLOYMENT_SESSION_ID differs between deployment-parameters.yaml and "
            "deploy-descriptor.yaml"
        )


# ---------------------------------------------------------------------------
# UC-ES-DEP-A9: deploy-descriptor.yaml structure
# ---------------------------------------------------------------------------

class TestDeployDescriptorStructure(BaseTest):
    """
    UC-ES-DEP-A9 — deploy-descriptor.yaml has required top-level keys and
    the correct shape for image-type services (artifacts always empty list).
    """

    @pytest.fixture(autouse=True)
    def _dd(self):
        self._d = _load(
            "deployment/monitoring-origin/MONITORING/values/deploy-descriptor.yaml"
        )

    def test_top_level_keys_present(self):
        # UC-ES-DEP-A9: global, deployDescriptor, APPLICATION_NAME, DEPLOYMENT_SESSION_ID,
        # MANAGED_BY must exist at root level.
        for key in ("global", "deployDescriptor", "APPLICATION_NAME",
                    "DEPLOYMENT_SESSION_ID", "MANAGED_BY"):
            assert key in self._d, f"top-level key missing from deploy-descriptor.yaml: {key}"

    def test_deploy_descriptor_section_is_non_empty(self):
        # UC-ES-DEP-A9: deployDescriptor must contain at least one service entry.
        assert self._d["deployDescriptor"], "deployDescriptor section must not be empty"

    def test_image_service_has_empty_artifacts_list(self):
        # UC-ES-DEP-A9: image-type services always have artifacts: [].
        dd_section = self._d["deployDescriptor"]
        # alertmanager is application/octet-stream — always empty artifacts
        assert dd_section["alertmanager"]["artifacts"] == [], (
            "alertmanager (image service) must have artifacts: [] in deploy-descriptor"
        )

    def test_image_service_has_docker_fields(self):
        # UC-ES-DEP-A9: image-type service has docker_registry and full_image_name.
        svc = self._d["deployDescriptor"]["alertmanager"]
        assert "docker_registry" in svc
        assert "full_image_name" in svc


# ---------------------------------------------------------------------------
# UC-ES-DEP-A11: per-service-parameters structure
# ---------------------------------------------------------------------------

class TestPerServiceParametersStructure(BaseTest):
    """
    UC-ES-DEP-A11 — per-service-parameters/ directory exists under each
    application's values/; each service entry has the required predefined keys.
    """

    def test_per_service_parameters_dir_exists_for_monitoring(self):
        # UC-ES-DEP-A11: charted SBOM → per-service-parameters/{chart}/ created.
        assert (_FIXTURES / "deployment/monitoring-origin/MONITORING/values/"
                "per-service-parameters").is_dir()

    def test_per_service_parameters_dir_exists_for_postgres(self):
        assert (_FIXTURES / "deployment/pg/postgres/values/"
                "per-service-parameters").is_dir()

    def test_per_service_entries_have_required_keys(self):
        # UC-ES-DEP-A11: each service entry has SERVICE_NAME, DEPLOYMENT_VERSION,
        # DEPLOYMENT_RESOURCE_NAME, ARTIFACT_DESCRIPTOR_VERSION.
        params = _load(
            "deployment/pg/postgres/values/per-service-parameters/"
            "postgres/deployment-parameters.yaml"
        )
        for svc_name, svc_params in params.items():
            for key in ("SERVICE_NAME", "DEPLOYMENT_VERSION",
                        "DEPLOYMENT_RESOURCE_NAME", "ARTIFACT_DESCRIPTOR_VERSION"):
                assert key in svc_params, (
                    f"per-service key '{key}' missing for service '{svc_name}'"
                )

    def test_service_name_value_matches_key(self):
        # UC-ES-DEP-A11: SERVICE_NAME value equals the map key (service name).
        params = _load(
            "deployment/pg/postgres/values/per-service-parameters/"
            "postgres/deployment-parameters.yaml"
        )
        for svc_name, svc_params in params.items():
            assert svc_params["SERVICE_NAME"] == svc_name, (
                f"SERVICE_NAME value '{svc_params['SERVICE_NAME']}' "
                f"does not match map key '{svc_name}'"
            )

    def test_deployment_version_is_v1(self):
        # UC-ES-DEP-A11: DEPLOYMENT_VERSION is always "v1" (suffix convention).
        params = _load(
            "deployment/pg/postgres/values/per-service-parameters/"
            "postgres/deployment-parameters.yaml"
        )
        for svc_name, svc_params in params.items():
            assert svc_params["DEPLOYMENT_VERSION"] == "v1", (
                f"DEPLOYMENT_VERSION must be 'v1' for service '{svc_name}'"
            )


# ---------------------------------------------------------------------------
# UC-ES-RUN-1 / UC-ES-RUN-2: runtime output files exist
# ---------------------------------------------------------------------------

class TestRuntimeOutputFiles(BaseTest):
    """
    UC-ES-RUN-1 / UC-ES-RUN-2 — runtime/parameters.yaml and
    runtime/credentials.yaml exist for each processed application.
    """

    def test_runtime_parameters_yaml_exists_for_monitoring(self):
        # UC-ES-RUN-1: runtime non-sensitive output written per namespace/app.
        assert _exists("runtime/monitoring-origin/MONITORING/parameters.yaml")

    def test_runtime_credentials_yaml_exists_for_monitoring(self):
        # UC-ES-RUN-2: runtime sensitive output written per namespace/app.
        assert _exists("runtime/monitoring-origin/MONITORING/credentials.yaml")

    def test_runtime_parameters_yaml_exists_for_postgres(self):
        assert _exists("runtime/pg/postgres/parameters.yaml")

    def test_runtime_credentials_yaml_exists_for_postgres(self):
        assert _exists("runtime/pg/postgres/credentials.yaml")

    def test_runtime_parameters_contains_technical_config_keys(self):
        # UC-ES-RUN-1: technicalConfigurationParameters from cloud/namespace are
        # merged into runtime/parameters.yaml.
        params = _load("runtime/monitoring-origin/MONITORING/parameters.yaml")
        # cloud.yml has integrations.ndo-api-gw.url; namespace has TECHNICAL_PARAM_1
        assert "integrations.ndo-api-gw.url" in params
        assert "TECHNICAL_PARAM_1" in params


# ---------------------------------------------------------------------------
# UC-ES-PIPE-1: pipeline output files exist and have expected content
# ---------------------------------------------------------------------------

class TestPipelineOutputFiles(BaseTest):
    """
    UC-ES-PIPE-1 — pipeline/parameters.yaml and pipeline/credentials.yaml
    exist; parameters.yaml contains e2eParameters from cloud.
    """

    def test_pipeline_parameters_yaml_exists(self):
        # UC-ES-PIPE-1: non-sensitive e2eParameters written to pipeline/parameters.yaml.
        assert _exists("pipeline/parameters.yaml")

    def test_pipeline_credentials_yaml_exists(self):
        # UC-ES-PIPE-1: sensitive e2eParameters written to pipeline/credentials.yaml.
        assert _exists("pipeline/credentials.yaml")

    def test_pipeline_parameters_contains_cloud_e2e_key(self):
        # UC-ES-PIPE-1: cloud.yml e2eParameters.CLOUD_LEVEL_PARAM_1 appears in
        # pipeline/parameters.yaml (non-sensitive split).
        params = _load("pipeline/parameters.yaml")
        assert "CLOUD_LEVEL_PARAM_1" in params
        assert params["CLOUD_LEVEL_PARAM_1"] == "cloud-level-value-1"


# ---------------------------------------------------------------------------
# UC-ES-CLN-1 / UC-ES-CLN-2 / UC-ES-CLN-3: cleanup context content
# ---------------------------------------------------------------------------

class TestCleanupContext(BaseTest):
    """
    UC-ES-CLN-1 — cleanup/parameters.yaml per namespace, merged non-sensitive
    deploy parameters from Tenant, Cloud, Namespace hierarchy.

    UC-ES-CLN-2 — cleanup/credentials.yaml per namespace, contains K8S_TOKEN
    and storage credential keys; custom runtime params override with higher
    priority (Java Calculator behaviour, not testable here — see CmdbCliTest.java).

    UC-ES-CLN-3 — cleanup/mapping.yaml namespace keys match disk folder names.
    """

    # Storage-level credential keys that belong in credentials.yaml only.
    _CLEANUP_CREDENTIAL_KEYS = frozenset({
        "K8S_TOKEN",
        "STORAGE_PASSWORD", "STORAGE_USERNAME",
        "CDN_STORAGE_PASSWORD", "CDN_STORAGE_USERNAME",
        "DOC_STORAGE_PASSWORD", "DOC_STORAGE_USERNAME",
    })

    # ------------------------------------------------------------------ CLN-1

    def test_cleanup_parameters_yaml_exists_for_all_namespaces(self):
        # UC-ES-CLN-1: parameters file is written per namespace, not per application.
        for ns in ("monitoring-origin", "pg"):
            assert _exists(f"cleanup/{ns}/parameters.yaml"), (
                f"cleanup/{ns}/parameters.yaml must exist"
            )

    def test_cleanup_params_contains_identity_keys(self):
        # UC-ES-CLN-1: identity / cloud keys always written to cleanup/parameters.yaml.
        params = _load("cleanup/monitoring-origin/parameters.yaml")
        for key in ("NAMESPACE", "TENANTNAME", "CLOUD_API_HOST"):
            assert key in params, f"identity key '{key}' missing from cleanup/parameters.yaml"

    def test_cleanup_params_namespace_value_matches_actual_namespace(self):
        # UC-ES-CLN-1: NAMESPACE value equals the actual k8s namespace, not the deployPostfix.
        params = _load("cleanup/monitoring-origin/parameters.yaml")
        assert params["NAMESPACE"] == "pl-01-monitoring"

    def test_cleanup_credential_keys_absent_from_parameters(self):
        # UC-ES-CLN-1 / CLN-2: storage credential keys must not appear in
        # parameters.yaml — they belong in credentials.yaml only.
        params = set(_load("cleanup/monitoring-origin/parameters.yaml").keys())
        found = self._CLEANUP_CREDENTIAL_KEYS & params
        assert not found, (
            f"cleanup credential keys must not be in parameters.yaml: {found}"
        )

    # ------------------------------------------------------------------ CLN-2

    def test_cleanup_credentials_yaml_exists_for_all_namespaces(self):
        # UC-ES-CLN-2: credentials file is written per namespace.
        for ns in ("monitoring-origin", "pg"):
            assert _exists(f"cleanup/{ns}/credentials.yaml"), (
                f"cleanup/{ns}/credentials.yaml must exist"
            )

    def test_cleanup_credentials_contains_k8s_token(self):
        # UC-ES-CLN-2: K8S_TOKEN always in cleanup/credentials.yaml (used to
        # authenticate cleanup operations against the k8s API).
        for ns in ("monitoring-origin", "pg"):
            creds = _load(f"cleanup/{ns}/credentials.yaml")
            assert "K8S_TOKEN" in creds, (
                f"K8S_TOKEN missing from cleanup/{ns}/credentials.yaml"
            )

    def test_cleanup_credentials_contains_storage_credential_keys(self):
        # UC-ES-CLN-2: sensitive storage credentials written to cleanup/credentials.yaml.
        creds = _load("cleanup/monitoring-origin/credentials.yaml")
        for key in ("STORAGE_PASSWORD", "STORAGE_USERNAME",
                    "CDN_STORAGE_PASSWORD", "CDN_STORAGE_USERNAME"):
            assert key in creds, (
                f"storage credential key '{key}' missing from cleanup/credentials.yaml"
            )

    def test_cleanup_credential_keys_not_duplicated_in_parameters(self):
        # UC-ES-CLN-2: no storage credential key can appear in both
        # cleanup/credentials.yaml and cleanup/parameters.yaml.
        params = set(_load("cleanup/monitoring-origin/parameters.yaml").keys())
        overlap = self._CLEANUP_CREDENTIAL_KEYS & params
        assert not overlap, (
            f"cleanup credential keys must not appear in parameters.yaml: {overlap}"
        )

    # ------------------------------------------------------------------ CLN-3

    def test_cleanup_mapping_namespace_folders_exist(self):
        # UC-ES-CLN-3: every namespace path in cleanup/mapping.yaml must point
        # to an existing folder on disk.
        for key, val in _load("cleanup/mapping.yaml").items():
            ns_folder = val.split("/effective-set/cleanup/")[-1]
            assert (_FIXTURES / "cleanup" / ns_folder).is_dir(), (
                f"cleanup mapping '{key}' → folder 'cleanup/{ns_folder}' does not exist"
            )


# ---------------------------------------------------------------------------
# Topology output files (UC-ES-PIPE-1 / UC-ES-NOSBOM-1)
# ---------------------------------------------------------------------------

class TestTopologyOutputFiles(BaseTest):
    """
    Topology and Pipeline files are generated in all modes (full generation
    and No SBOMs Mode).

    Note — UC-ES-NOSBOM-1: when the Calculator is invoked without --sd-path,
    --sboms-path, --registries (Python-level: _build_cli_cmd receives a
    non-existent sd_path), only pipeline/ and topology/ are produced;
    deployment/, runtime/, and cleanup/ are not written.  The Python-level
    wiring is tested in test_sbom_processing.py::TestNoSbomMode.  The
    directory-absence assertion is Java-side and verified in CmdbCliTest.java.
    """

    def test_topology_parameters_yaml_exists(self):
        assert _exists("topology/parameters.yaml")

    def test_topology_credentials_yaml_exists(self):
        assert _exists("topology/credentials.yaml")

    def test_topology_parameters_contains_cluster_section(self):
        # topology/parameters.yaml has cluster block with API coordinates.
        params = _load("topology/parameters.yaml")
        assert "cluster" in params
        cluster = params["cluster"]
        for key in ("api_url", "api_port", "protocol", "public_url"):
            assert key in cluster, f"cluster.{key} missing from topology/parameters.yaml"

    def test_topology_parameters_contains_environments_section(self):
        # topology/parameters.yaml: environments.<cluster>/<env>.namespaces with deployPostfix.
        params = _load("topology/parameters.yaml")
        assert "environments" in params
        namespaces = params["environments"]["cluster-01/pl-01"]["namespaces"]
        assert "pl-01-monitoring" in namespaces
        assert "pl-01-pg" in namespaces

    def test_topology_deploy_postfixes_match_deployment_mapping_paths(self):
        # topology/parameters.yaml deployPostfix values must correspond to namespace
        # folder names referenced in deployment/mapping.yaml.
        topo = _load("topology/parameters.yaml")
        mapping_paths = " ".join(_load("deployment/mapping.yaml").values())
        namespaces = topo["environments"]["cluster-01/pl-01"]["namespaces"]
        for ns_name, ns_data in namespaces.items():
            postfix = ns_data["deployPostfix"]
            assert postfix in mapping_paths, (
                f"deployPostfix '{postfix}' for namespace '{ns_name}' "
                "not found in any deployment mapping path"
            )

    def test_topology_credentials_contains_k8s_tokens_per_namespace(self):
        # topology/credentials.yaml: k8s_tokens map keyed by namespace name.
        creds = _load("topology/credentials.yaml")
        assert "k8s_tokens" in creds
        tokens = creds["k8s_tokens"]
        assert "pl-01-monitoring" in tokens
        assert "pl-01-pg" in tokens

    def test_topology_k8s_tokens_match_cleanup_credentials(self):
        # topology/credentials.yaml k8s_tokens must equal cleanup/*/credentials.yaml
        # K8S_TOKEN — both are written from the same namespace credential source.
        topo_creds = _load("topology/credentials.yaml")
        namespaces = _load("topology/parameters.yaml")["environments"]["cluster-01/pl-01"]["namespaces"]
        for ns_name, ns_data in namespaces.items():
            postfix = ns_data["deployPostfix"]
            topo_token = topo_creds["k8s_tokens"][ns_name]
            cleanup_token = _load(f"cleanup/{postfix}/credentials.yaml")["K8S_TOKEN"]
            assert cleanup_token == topo_token, (
                f"K8S_TOKEN for namespace '{ns_name}' differs between "
                f"topology/credentials.yaml and cleanup/{postfix}/credentials.yaml"
            )
