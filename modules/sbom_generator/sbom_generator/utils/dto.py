from sbom_generator.utils.models import BaseSchema


class ApplicationDTO(BaseSchema):
    name: str
    artifact_id: str
    group_id: str
    registry_name: str
    solution_descriptor: bool = False
