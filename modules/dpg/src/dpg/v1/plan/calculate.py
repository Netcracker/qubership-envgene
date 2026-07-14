"""Deployment plan calculate command — compute a deployment plan from an application list."""

import os
from pathlib import Path

from qubership_pipelines_common_library.v1.execution.exec_command import ExecutionCommand
from dpg.v1.cmd import DeploymentPlanGeneratorCommand


class PlanDeploymentCalculate(ExecutionCommand):
    """Calculate a deployment plan from a list of application names.

    Resolves dependency order and wave assignments for the supplied applications
    and writes the resulting plan to an output YAML file.

    Mandatory params:
        params.applications: Comma-separated list of application names to include
            in the deployment plan.

    Optional params:
        params.output_file: Destination file path (default: ``deploy-plan.yaml``).
        params.rootdir: Root directory used by the data provider to resolve
            application metadata (default: current working directory).

    Output params:
        params.deployment_plan: Calculated plan as a list (forwarded to next steps).
    """

    def _validate(self):
        if not self.context.validate(["params.applications"]):
            return False

        self._applications = self.context.input_param_get("params.applications").split(",")
        self._output_file = self.context.input_param_get("params.output_file", "deploy-plan.yaml")
        self._rootdir = Path(self.context.input_param_get("params.rootdir", os.getcwd()))
        return True

    def _execute(self):
        deploy_plan = DeploymentPlanGeneratorCommand.calculate(applications=self._applications, output_file=self._output_file, rootdir=self._rootdir)
        self.context.output_param_set("params.deployment_plan", deploy_plan.to_dict())
        self.context.output_params_save()
