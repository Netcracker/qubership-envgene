from typing import List, Dict
from pydantic import BaseModel, Field

from dpg.v1.internal.sd.models.solution_descriptor_base import SolutionDescriptor
from dpg.v1.internal.deployment_plan.models import DeployPlanEntity

class SolutionDescritorApplication(BaseModel):
    version: str
    deploy_postfix: str = Field(alias='deployPostfix', default='')

class SolutionDescriptor_2_1(SolutionDescriptor):
    version: float
    type: str
    deploy_mode : str = Field(alias='deployMode', default='')
    applications: List[SolutionDescritorApplication]

    def collect_waves(self) -> Dict[int, List[DeployPlanEntity]]:
        deploy_postfix_wave_map: Dict[str, int] = dict()
        waves: Dict[int, List[DeployPlanEntity]] = dict()

        for app in self.applications:
            if app.deploy_postfix not in deploy_postfix_wave_map:
                last_wave = -1
                if len(deploy_postfix_wave_map.keys()) > 0:
                    last_wave = max(deploy_postfix_wave_map.values())
                deploy_postfix_wave_map[app.deploy_postfix] = last_wave+1
            
            curr_wave = deploy_postfix_wave_map[app.deploy_postfix]
            if curr_wave not in waves:
                waves[curr_wave] = list()

            waves[curr_wave].append(DeployPlanEntity(version=app.version, deployPostfix=app.deploy_postfix))

        return waves
