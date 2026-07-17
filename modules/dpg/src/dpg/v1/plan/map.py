"""Deployment plan map command — remap namespace values in an existing plan."""

from pathlib import Path

from qubership_pipelines_common_library.v1.execution.exec_command import ExecutionCommand
from dpg.v1.cmd import DeploymentPlanGeneratorCommand


class PlanDeploymentMapNamespaces(ExecutionCommand):
    """Remap namespace values in a deployment plan according to a substitution map.

    Reads a deployment plan from ``params.deployment_plan`` (file path or inline
    list), applies a namespace substitution map, and writes the result to an
    output YAML file.

    Mandatory params:
        params.map: Path to a YAML/JSON file containing the substitution mapping,
            or an inline dict value forwarded from a previous pipeline step.

    Optional params:
        params.deployment_plan: Path to a YAML/JSON file containing the plan list,
            or an inline list value forwarded from a previous pipeline step
            (default: ``deploy-plan.yaml``).
        params.output_file: Destination file path (default: ``deploy-plan.yaml``).

    Output params:
        params.deployment_plan: Remapped plan as a list (forwarded to next steps).
    """

    def _validate(self):
        if not self.context.validate(["params.map"]):
            return False

        self.__deploy_plan = self.context.input_param_get("params.deployment_plan", "deploy-plan.yaml")
        self.__map = self.context.input_param_get("params.map", dict())
        self._output_file = self.context.input_param_get("params.output_file", "deploy-plan.yaml")
        return True

    def _execute(self):
        deploy_plan = DeploymentPlanGeneratorCommand.map(deploy_plan=self.__deploy_plan, map=self.__map, output_file=self._output_file)
        self.context.output_param_set("params.deployment_plan", deploy_plan.to_dict())
        self.context.output_params_save()
