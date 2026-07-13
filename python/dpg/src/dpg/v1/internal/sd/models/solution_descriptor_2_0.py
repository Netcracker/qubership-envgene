from typing import List, Dict

from dpg.v1.internal.sd.models.solution_descriptor_base import SolutionDescriptor
from dpg.v1.internal.deployment_plan.models import DeployPlanEntity

class SolutionDescriptor_2_0(SolutionDescriptor):
    version: float 
    type: str
    applications: List[str]

    def collect_waves(self) -> Dict[int, List[DeployPlanEntity]]:
        return {0: [DeployPlanEntity(version=v, deployPostfix="") for v in self.applications]}
