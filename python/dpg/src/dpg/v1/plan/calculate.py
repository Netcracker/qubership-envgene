import os
import yaml
from pathlib import Path

from qubership_pipelines_common_library.v1.execution.exec_command import ExecutionCommand

from dpg.v1.internal.deployment_plan import DeploymentPlanCalculator
import dpg.v1.utils as utils

class PlanDeploymentCalculate(ExecutionCommand):

    def _validate(self):
        if not self.context.validate(["params.applications"]):
            return False

        self._applications = self.context.input_param_get("params.applications").split(",")
        self._output_file = self.context.input_param_get("params.output_file", "deploy-plan.yaml")
        self._rootdir = Path(self.context.input_param_get("params.rootdir", os.getcwd()))
        return True

    def _execute(self):
        self.context.logger.info(
            f"Calculating deployment plan"
            f" [{len(self._applications)} application(s)]"
        )

        deploy_plan = DeploymentPlanCalculator(
            applications=self._applications,
            data_provider=utils.get_data_provider(self.context, root_dir=self._rootdir),
        ).calculate(self.context)

        wave_count = len({e.wave for e in deploy_plan.entities})
        app_count = len(deploy_plan.entities)
        self.context.logger.info(f"Deployment plan ready: {wave_count} wave(s), {app_count} application(s)")
        self.context.logger.debug(f"Plan details:\n{deploy_plan}")

        self.context.logger.info(f"Writing deploy plan to {self._output_file}..")
        with open(self._output_file, "w") as f:
            f.write(yaml.dump(deploy_plan.to_dict()))

        self.context.output_param_set("params.deployment_plan", deploy_plan.to_dict())
        self.context.output_params_save()
