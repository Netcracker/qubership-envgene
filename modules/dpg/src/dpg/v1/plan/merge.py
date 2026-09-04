"""Deployment plan merge command — merge a deployment plan from list."""

import os
from pathlib import Path

from qubership_pipelines_common_library.v1.execution.exec_command import ExecutionCommand
from dpg.v1.cmd import DeploymentPlanGeneratorCommand


class PlanDeploymentMerge(ExecutionCommand):
    """Merge multiple deploy plans into one.

    Reads a comma-separated list of deploy-plan file paths from
    ``params.deploy_plans``, merges them left-to-right, and writes the
    result to ``params.output_file`` (default: ``deploy-plan.yaml``).

    Merge semantics:
    - Entities present in only one plan are included as-is.
    - Entities present in multiple plans keep the **maximum wave** across all plans.

    Output params:
    - ``params.deployment_plan`` — merged plan as a list of entity dicts.
    """

    def _validate(self):
        if not self.context.validate(["params.deploy_plans"]):
            return False

        self._deploy_plans = self.context.input_param_get("params.deploy_plans")
        self._output_file = self.context.input_param_get("params.output_file", "deploy-plan.yaml")
        return True

    def _execute(self):
        plans = self._deploy_plans.split(",")
        deploy_plan = DeploymentPlanGeneratorCommand.merge(deploy_plans=plans, output_file=self._output_file)
        if deploy_plan is not None:
            self.context.output_param_set("params.deployment_plan", deploy_plan.to_dict())
        self.context.output_params_save()

