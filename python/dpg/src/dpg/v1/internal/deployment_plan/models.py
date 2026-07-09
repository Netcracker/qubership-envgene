from typing import Dict, List
from pydantic import BaseModel, Field


class DeployPlanEntity(BaseModel):
    wave: int = 0
    version: str
    deploy_postfix: str = Field(alias='deployPostfix', default='')
    namespace: str = Field(default="")

    def __repr__(self):
        return f"DeployPlanEntity(wave={self.wave}, version='{self.version}', namespace='{self.namespace}', deploy_postfix='{self.deploy_postfix}')"

class DeployPlan(BaseModel):
    entities: List[DeployPlanEntity] = Field(default_factory=list)

    @classmethod
    def from_dict(cls, v: list) -> 'DeployPlan':
        return cls(entities=[DeployPlanEntity.model_validate(item) for item in v])

    def to_dict(self) -> list:
        return [entity.model_dump(by_alias=True) for entity in self.entities]

    def validate_namespaces(self):
        for entity in self.entities:
            if entity.namespace == "":
                raise ValueError(f"Namespace is not defined for entity={entity}")

    def __str__(self):
        by_wave: Dict[int, List[DeployPlanEntity]] = {}
        for entity in self.entities:
            by_wave.setdefault(entity.wave, []).append(entity)
        output = ""
        for wave in sorted(by_wave):
            output += f"- Wave #{wave}\n"
            for entity in by_wave[wave]:
                output += f"     - {entity}\n"
        return output
