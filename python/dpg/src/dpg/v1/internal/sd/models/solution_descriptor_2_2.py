from typing import List, Dict
from pydantic import BaseModel, Field

from dpg.v1.internal.sd.models.solution_descriptor_2_1 import SolutionDescriptor_2_1
from dpg.v1.internal.deployment_plan.models import DeployPlanEntity

class DeployGraphEntity(BaseModel):
    chunk_name: str = Field(alias='chunkName')
    apps: List[str]

class SolutionDescritorApplication(BaseModel):
    version: str
    deploy_postfix: str = Field(alias='deployPostfix', default='')
    alias: str = Field(default="")

class SolutionDescriptor_2_2(SolutionDescriptor_2_1):
    version: float
    type: str
    deploy_mode : str = Field(alias='deployMode', default='')
    applications: List[SolutionDescritorApplication]
    deploy_graph: List[DeployGraphEntity] = Field(alias='deployGraph', default=list())

    @property
    def __alias_map(self) -> Dict[str, DeployPlanEntity]:
        aliasmap = dict()
        for app in self.applications:
            if app.alias != "":
                aliasmap[app.alias] = DeployPlanEntity(version=app.version, deployPostfix=app.deploy_postfix)
                continue
            app_name = app.version.split(":")[0]
            aliasmap[f"{app_name}:{app.deploy_postfix}"] = DeployPlanEntity(version=app.version, deployPostfix=app.deploy_postfix)
        return aliasmap

    def collect_waves(self) -> Dict[int, List[DeployPlanEntity]]:
        if len(self.deploy_graph) == 0:
            return super().collect_waves()

        waves: Dict[int, List[DeployPlanEntity]] = dict()
        wave_index = 0
        aliasmap = self.__alias_map

        for chunk in self.deploy_graph:
            waves[wave_index] = [aliasmap[capp] for capp in chunk.apps]
            wave_index += 1
        
        return waves
