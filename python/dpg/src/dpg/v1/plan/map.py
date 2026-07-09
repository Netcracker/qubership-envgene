import os
import yaml
from pathlib import Path

from qubership_pipelines_common_library.v1.execution.exec_command import ExecutionCommand

from dpg.v1.internal.deployment_plan import DeploymentPlanCalculator, DeployPlan
import dpg.v1.utils as utils


class PlanDeploymentMapNamespaces(ExecutionCommand):

    def _validate(self):
        if not self.context.validate(["params.map"]):
            return False

        self.__deploy_plan = self.context.input_param_get("params.deployment_plan", "deploy-plan.yaml")
        self.__map = self.context.input_param_get("params.map", dict())
        self._rootdir = Path(self.context.input_param_get("params.rootdir", os.getcwd()))
        self._output_file = self.context.input_param_get("params.output_file", "deploy-plan.yaml")
        return True

    def _execute(self):
        if utils.is_file_path(self.__deploy_plan):
            with open(self.__deploy_plan, "r") as f:
                self.__deploy_plan = utils.load_json_or_yaml(f.read())
        deploy_plan = DeployPlan.from_dict(self.__deploy_plan)
        self.context.logger.info(f"Input plan details:\n{deploy_plan}")

        if utils.is_file_path(self.__map):
            with open(self.__map, "r") as f:
                self.__map = utils.load_json_or_yaml(f.read())

        if not isinstance(self.__map, dict) or len(self.__map.keys()) == 0:
            raise Exception("Map provided in input param `params.map` invalid.")

        deploy_plan = DeploymentPlanCalculator.map_namespaces_to_plan(self.context, deploy_plan, map=self.__map)

        wave_count = len({e.wave for e in deploy_plan.entities})
        app_count = len(deploy_plan.entities)
        self.context.logger.info(f"Deployment plan ready: {wave_count} wave(s), {app_count} application(s)")
        self.context.logger.debug(f"Plan details:\n{deploy_plan}")

        self.context.logger.info(f"Writing deploy plan to {self._output_file}..")
        with open(self._output_file, "w") as f:
            f.write(yaml.dump(deploy_plan.to_dict()))

        self.context.output_param_set("params.deployment_plan", deploy_plan.to_dict())
        self.context.output_params_save()
