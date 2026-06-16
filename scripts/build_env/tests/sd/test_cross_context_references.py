import os

from scripts.build_env.tests.base_test import BaseTest

os.environ.setdefault("ENVIRONMENT_NAME", "env-01")
os.environ.setdefault("CLUSTER_NAME", "cluster-01")

from render_config_env import Context, render_obj_by_context


def _ctx(**kwargs) -> Context:
    return Context(**kwargs)


def _render(template: dict, **ctx_vars) -> dict:
    return render_obj_by_context(template, _ctx(**ctx_vars))


class TestCrossContextReferences(BaseTest):
    """
    UC-CC-CR-3..6 — cross-parameter-type references within the same Namespace.

    Scoping rules:
    - deployParameters → Deployment context (deployment-parameters.yaml)
    - technicalConfigurationParameters → Runtime context (runtime/parameters.yaml)
    - e2eParameters → Pipeline context only; NOT included in deployment or runtime scope

    When the Effective Set generator builds a rendering context it merges only the
    parameter types that belong to the target scope.  At the Python (Jinja2) layer,
    render_obj_by_context reflects this: variables passed in kwargs are resolved, those
    absent from kwargs are ChainableUndefined and render to empty/None.

    UC-CC-CR-3 / UC-CC-CR-4: e2eParameters reference deploy or technical vars.
    The Jinja2 substitution works in pipeline scope (all vars present), but
    e2eParameters values are never written to deployment/runtime output — "silent drop".

    UC-CC-CR-5: technicalConfigurationParameters reference deployParameters.
    The runtime context merges both types, so the reference resolves successfully.

    UC-CC-CR-6: technicalConfigurationParameters reference e2eParameters.
    e2eParameters are NOT in runtime context; the reference is unresolvable.
    At the Python rendering level this renders empty (ChainableUndefined); the
    Effective Set generator (Java CLI) raises "Could not process expression for
    parameter <name> with value: ${e2e_endpoint}" in this scenario.
    """

    # ------------------------------------------------------------------
    # UC-CC-CR-3: E2EParameters → DeployParameters — silent drop
    # ------------------------------------------------------------------

    def test_uc_cr_3_e2e_referencing_deploy_resolves_in_pipeline_context(self):
        # UC-CC-CR-3: In pipeline scope all parameter types are present in context.
        # test_endpoint: {{ api_url }} resolves because api_url (deployParameters)
        # is available. The "silent drop" means the resolved value is never written
        # to deployment or runtime output — only pipeline scope would include it.
        result = _render(
            {"test_endpoint": "{{ api_url }}"},
            api_url="https://api.example.com",
        )
        assert result["test_endpoint"] == "https://api.example.com"

    def test_uc_cr_3_e2e_variable_absent_from_deployment_context_renders_empty(self):
        # UC-CC-CR-3: Deployment context does NOT include e2eParameters variables.
        # A template key that lives in e2eParameters renders to empty when built with
        # deployment-only context — Python equivalent of the "silent drop".
        result = _render({"test_endpoint": "{{ e2e_only_var }}"})
        assert result.get("test_endpoint") in (None, "", "None")

    # ------------------------------------------------------------------
    # UC-CC-CR-4: E2EParameters → TechnicalConfigurationParameters — silent drop
    # ------------------------------------------------------------------

    def test_uc_cr_4_valid_technical_param_unaffected_by_absent_e2e_ref(self):
        # UC-CC-CR-4: Generation completes successfully; config_endpoint in runtime
        # output is unaffected by absent e2e variable in the same template.
        # This is the key scenario for UC-CR-4: mixed template with one resolvable
        # (technical) and one unresolvable (e2e) key.
        result = _render(
            {
                "config_endpoint": "{{ config_endpoint }}",
                "test_config": "{{ e2e_test_config }}",
            },
            config_endpoint="https://config.example.com",
        )
        assert result["config_endpoint"] == "https://config.example.com"
        assert result.get("test_config") in (None, "", "None")

    # ------------------------------------------------------------------
    # UC-CC-CR-5: TechnicalConfigurationParameters → DeployParameters — resolves
    # ------------------------------------------------------------------

    def test_uc_cr_5_technical_referencing_deploy_resolves_successfully(self):
        # UC-CC-CR-5: Runtime context merges deployParameters and
        # technicalConfigurationParameters. deploy_url is available so
        # runtime_config: {{ deploy_url }} resolves to the deploy value.
        result = _render(
            {"runtime_config": "{{ deploy_url }}"},
            deploy_url="https://deploy.example.com",
        )
        assert result["runtime_config"] == "https://deploy.example.com"

    def test_uc_cr_5_both_runtime_and_deploy_outputs_populated(self):
        # UC-CC-CR-5: Full scenario — deploy_url in deployment output,
        # runtime_config resolved in runtime output, both from same context.
        result = _render(
            {
                "deploy_url": "{{ deploy_url }}",
                "runtime_config": "{{ deploy_url }}",
            },
            deploy_url="https://deploy.example.com",
        )
        assert result["deploy_url"] == "https://deploy.example.com"
        assert result["runtime_config"] == "https://deploy.example.com"

    # ------------------------------------------------------------------
    # UC-CC-CR-6: TechnicalConfigurationParameters → E2EParameters — not resolved
    # ------------------------------------------------------------------

    def test_uc_cr_6_technical_referencing_e2e_renders_empty_in_runtime_context(self):
        # UC-CC-CR-6: Runtime context does NOT include e2eParameters.
        # runtime_endpoint: {{ e2e_endpoint }} — e2e_endpoint absent → empty.
        # The Effective Set generator (Java CLI) raises "Could not process expression
        # for parameter runtime_endpoint with value: ${e2e_endpoint}" for this case.
        result = _render({"runtime_endpoint": "{{ e2e_endpoint }}"})
        assert result.get("runtime_endpoint") in (None, "", "None")

    def test_uc_cr_6_other_technical_params_resolve_even_when_e2e_missing(self):
        # UC-CC-CR-6: A technical param that references a deploy param still resolves
        # correctly; only the e2e reference is broken.
        result = _render(
            {
                "valid_runtime_config": "{{ deploy_url }}",
                "broken_e2e_ref": "{{ e2e_endpoint }}",
            },
            deploy_url="https://deploy.example.com",
        )
        assert result["valid_runtime_config"] == "https://deploy.example.com"
        assert result.get("broken_e2e_ref") in (None, "", "None")

    def test_uc_cr_6_e2e_endpoint_source_value_in_pipeline_context(self):
        # UC-CC-CR-6 (contrast): e2e_endpoint IS defined in e2eParameters in the source
        # namespace.yml. In pipeline scope (all parameter types present) it resolves —
        # but runtime scope excludes it.
        pipeline_result = _render(
            {"runtime_endpoint": "{{ e2e_endpoint }}"},
            e2e_endpoint="https://e2e.example.com",
        )
        runtime_result = _render(
            {"runtime_endpoint": "{{ e2e_endpoint }}"},
            # e2e_endpoint intentionally absent — simulates runtime context
        )
        assert pipeline_result["runtime_endpoint"] == "https://e2e.example.com"
        assert runtime_result.get("runtime_endpoint") in (None, "", "None")
