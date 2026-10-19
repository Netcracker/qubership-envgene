from artifact_searcher.utils.models import Registry, RegistryV2, Application
from sbom_generator.utils.dto import ApplicationDTO


def map_app_dto_to_model(dto: ApplicationDTO, registry: Registry | RegistryV2) -> Application:
    return Application(
        name=dto.name,
        artifact_id=dto.artifact_id,
        group_id=dto.group_id,
        registry=registry,
        solution_descriptor=dto.solution_descriptor
    )
