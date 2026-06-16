import os

from scripts.build_env.tests.base_test import BaseTest

os.environ.setdefault("ENVIRONMENT_NAME", "env-01")
os.environ.setdefault("CLUSTER_NAME", "cluster-01")

from render_config_env import Context, render_obj_by_context


def _ctx(**kwargs) -> Context:
    return Context(**kwargs)


def _render(template: dict, **ctx_vars) -> dict:
    return render_obj_by_context(template, _ctx(**ctx_vars))


class TestCrossLevelReferences(BaseTest):
    """
    UC-CC-HR-1..6 — parameters at one hierarchy level reference values from another.

    render_obj_by_context receives a flat Context whose fields hold the already-merged
    parameter maps from every level. Cross-level resolution is the same Jinja2 mechanism
    as same-level resolution; what makes it cross-level is that the source variable
    originates from a different hierarchy object than the template being rendered.
    """

    # ------------------------------------------------------------------
    # UC-CC-HR-1: Namespace → Cloud
    # ------------------------------------------------------------------

    def test_uc_hr_1_namespace_deploy_resolves_cloud_api_url(self):
        # UC-CC-HR-1: service_url: {{ cloud_api_url }} in Namespace deployParameters
        # must resolve to the Cloud value — Deployment context.
        result = _render(
            {"service_url": "{{ cloud_api_url }}"},
            cloud_api_url="https://api.example.com",
        )
        assert result["service_url"] == "https://api.example.com"

    def test_uc_hr_1_namespace_technical_resolves_cloud_config_url(self):
        # UC-CC-HR-1: config_endpoint: {{ cloud_config_url }} in Namespace
        # technicalConfigurationParameters — Runtime context.
        result = _render(
            {"config_endpoint": "{{ cloud_config_url }}"},
            cloud_config_url="https://config.example.com",
        )
        assert result["config_endpoint"] == "https://config.example.com"

    def test_uc_hr_1_namespace_e2e_reference_resolves_at_jinja2_level(self):
        # UC-CC-HR-1: test_endpoint: {{ cloud_test_url }} resolves at Jinja2 level.
        # Exclusion from output files is enforced by the Calculator — not in scope here.
        result = _render(
            {"test_endpoint": "{{ cloud_test_url }}"},
            cloud_test_url="https://test.example.com",
        )
        assert result["test_endpoint"] == "https://test.example.com"

    # ------------------------------------------------------------------
    # UC-CC-HR-2: Namespace → Tenant
    # ------------------------------------------------------------------

    def test_uc_hr_2_namespace_deploy_resolves_tenant_id(self):
        # UC-CC-HR-2: organization: {{ tenant_id }} in Namespace deployParameters
        # must resolve to the Tenant value — Deployment context.
        result = _render(
            {"organization": "{{ tenant_id }}"},
            tenant_id="acme-corp",
        )
        assert result["organization"] == "acme-corp"

    def test_uc_hr_2_namespace_technical_resolves_tenant_config_id(self):
        # UC-CC-HR-2: config_org: {{ tenant_config_id }} in Namespace
        # technicalConfigurationParameters — Runtime context.
        result = _render(
            {"config_org": "{{ tenant_config_id }}"},
            tenant_config_id="acme-config",
        )
        assert result["config_org"] == "acme-config"

    # ------------------------------------------------------------------
    # UC-CC-HR-3: Cloud → Tenant
    # ------------------------------------------------------------------

    def test_uc_hr_3_cloud_deploy_resolves_tenant_name(self):
        # UC-CC-HR-3: cloud_label: {{ tenant_name }} in Cloud deployParameters
        # merged into Namespace application deployment parameters.
        result = _render(
            {"cloud_label": "{{ tenant_name }}"},
            tenant_name="acme-corp",
        )
        assert result["cloud_label"] == "acme-corp"

    def test_uc_hr_3_cloud_technical_resolves_tenant_config_name(self):
        # UC-CC-HR-3: cloud_config_label: {{ tenant_config_name }} — Runtime context.
        result = _render(
            {"cloud_config_label": "{{ tenant_config_name }}"},
            tenant_config_name="acme-config",
        )
        assert result["cloud_config_label"] == "acme-config"

    def test_uc_hr_3_cloud_e2e_resolves_tenant_test_name(self):
        # UC-CC-HR-3: cloud_test_label: {{ tenant_test_name }} — Pipeline context.
        result = _render(
            {"cloud_test_label": "{{ tenant_test_name }}"},
            tenant_test_name="acme-test",
        )
        assert result["cloud_test_label"] == "acme-test"

    def test_uc_hr_3_all_three_contexts_resolved_in_one_template(self):
        # UC-CC-HR-3: deploy + e2e + technical all reference Tenant — all resolved.
        result = _render(
            {
                "cloud_label": "{{ tenant_name }}",
                "cloud_test_label": "{{ tenant_test_name }}",
                "cloud_config_label": "{{ tenant_config_name }}",
            },
            tenant_name="acme-corp",
            tenant_test_name="acme-test",
            tenant_config_name="acme-config",
        )
        assert result["cloud_label"] == "acme-corp"
        assert result["cloud_test_label"] == "acme-test"
        assert result["cloud_config_label"] == "acme-config"

    # ------------------------------------------------------------------
    # UC-CC-HR-4: Cloud → Namespace (downward reference)
    # ------------------------------------------------------------------

    def test_uc_hr_4_cloud_deploy_resolves_namespace_db_url(self):
        # UC-CC-HR-4: cloud_config: {{ namespace_db_url }} in Cloud deployParameters
        # when Namespace maps are available in the merge scope — Deployment context.
        result = _render(
            {"cloud_config": "{{ namespace_db_url }}"},
            namespace_db_url="postgres://db.local",
        )
        assert result["cloud_config"] == "postgres://db.local"

    def test_uc_hr_4_cloud_technical_resolves_namespace_config_url(self):
        # UC-CC-HR-4: cloud_config_param: {{ namespace_config_url }} — Runtime context.
        result = _render(
            {"cloud_config_param": "{{ namespace_config_url }}"},
            namespace_config_url="https://config.local",
        )
        assert result["cloud_config_param"] == "https://config.local"

    # ------------------------------------------------------------------
    # UC-CC-HR-5: Tenant → Cloud (downward reference)
    # ------------------------------------------------------------------

    def test_uc_hr_5_tenant_deploy_resolves_cloud_region(self):
        # UC-CC-HR-5: tenant_config: {{ cloud_region }} in Tenant deployParameters
        # resolved when cleanup parameters are built — cleanup context.
        result = _render(
            {"tenant_config": "{{ cloud_region }}"},
            cloud_region="us-east-1",
        )
        assert result["tenant_config"] == "us-east-1"

    def test_uc_hr_5_tenant_technical_resolves_cloud_config_region(self):
        # UC-CC-HR-5: tenant_config_param: {{ cloud_config_region }} — cleanup context.
        result = _render(
            {"tenant_config_param": "{{ cloud_config_region }}"},
            cloud_config_region="eu-central-1",
        )
        assert result["tenant_config_param"] == "eu-central-1"

    # ------------------------------------------------------------------
    # UC-CC-HR-6: Tenant → Namespace (downward reference)
    # ------------------------------------------------------------------

    def test_uc_hr_6_tenant_deploy_resolves_namespace_name(self):
        # UC-CC-HR-6: tenant_label: {{ namespace_name }} in Tenant deployParameters
        # resolved during cleanup parameter build — cleanup context.
        result = _render(
            {"tenant_label": "{{ namespace_name }}"},
            namespace_name="core",
        )
        assert result["tenant_label"] == "core"

    def test_uc_hr_6_tenant_technical_resolves_namespace_config_name(self):
        # UC-CC-HR-6: tenant_config_label: {{ namespace_config_name }} — cleanup context.
        result = _render(
            {"tenant_config_label": "{{ namespace_config_name }}"},
            namespace_config_name="config-core",
        )
        assert result["tenant_config_label"] == "config-core"

    # ------------------------------------------------------------------
    # Negative
    # ------------------------------------------------------------------

    def test_missing_cross_level_var_renders_empty_without_exception(self):
        # A variable absent from the merged context (misconfigured environment) must
        # not raise TemplateError — ChainableUndefined silently renders to empty/None.
        result = _render({"service_url": "{{ cloud_api_url }}"})
        assert result.get("service_url") in (None, "", "None")

    def test_all_three_hierarchy_levels_in_one_template(self):
        # Tenant + Cloud + Namespace variables all present in the same Context.
        # All three resolve to their respective literal values — no cross-contamination.
        result = _render(
            {
                "ns_from_cloud": "{{ cloud_api_url }}",
                "ns_from_tenant": "{{ tenant_id }}",
                "cloud_from_tenant": "{{ tenant_name }}",
            },
            cloud_api_url="https://api.example.com",
            tenant_id="acme-corp",
            tenant_name="acme-corp",
        )
        assert result["ns_from_cloud"] == "https://api.example.com"
        assert result["ns_from_tenant"] == "acme-corp"
        assert result["cloud_from_tenant"] == "acme-corp"
