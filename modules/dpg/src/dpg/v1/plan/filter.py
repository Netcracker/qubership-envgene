"""Deployment plan filtering command — include-only filter by postfix, component, wave, namespace."""

from qubership_pipelines_common_library.v1.execution.exec_command import ExecutionCommand
from dpg.v1.cmd import DeploymentPlanGeneratorCommand


class PlanDeploymentFilter(ExecutionCommand):
    """Filter a deployment plan with include-only rules.

    Reads a deployment plan from ``params.deployment_plan`` (file path or
    inline list), applies up to four independent include filters, and writes
    the result to an output YAML file.

    Mandatory params:
        params.deployment_plan: Path to a YAML/JSON file containing the plan list,
            or an inline list value forwarded from a previous pipeline step.

    Optional params:
        params.output_file: Destination file path (default: ``deployplan.yaml``).
        params.deploy_postfix_filter: Allowed ``deployPostfix`` values.
        params.component_names_filter: Allowed component names (part before ``:`` in version).
        params.wave_filter: Allowed wave numbers (e.g. ``0;1`` or ``0,1``).
        params.namespace_filter: Allowed namespace values.

    Output params:
        params.output_file: Filtered plan as a list (forwarded to next steps).
    """

    _DEFAULT_OUTPUT_FILE = "deploy-plan.yaml"

    def _validate(self) -> bool:
        if not self.context.validate([]):
            return False

        self._deployment_plan_input = self.context.input_param_get("params.deployment_plan", self._DEFAULT_OUTPUT_FILE)
        self._output_file = self.context.input_param_get("params.output_file", self._DEFAULT_OUTPUT_FILE)
        self._deploy_postfix_filter = self.context.input_param_get("params.deploy_postfix_filter")
        self._component_names_filter = self.context.input_param_get("params.component_names_filter")
        self._wave_filter = self.context.input_param_get("params.wave_filter")
        self._namespace_filter = self.context.input_param_get("params.namespace_filter")
        return True

    def _execute(self) -> None:
        filtered_plan = DeploymentPlanGeneratorCommand.filter(
            deploy_plan=self._deployment_plan_input,
            deploy_postfix_filter=self._deploy_postfix_filter,
            component_names_filter=self._component_names_filter,
            wave_filter=self._wave_filter,
            namespace_filter=self._namespace_filter
        )

        self.context.output_param_set("params.deployment_plan", filtered_plan.to_dict())
        self.context.output_params_save()
