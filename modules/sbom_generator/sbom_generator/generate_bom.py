import hashlib
import json
import time
import urllib.parse
from importlib.metadata import version, metadata
from pathlib import Path

import jschon
import jschon_tools
import jsonschema
from artifact_searcher.utils.models import Application, ArtifactDownload, Registry, parse_registry
from cyclonedx.model import Property, HashType, HashAlgorithm
from cyclonedx.model.bom import Bom, BomMetaData
from cyclonedx.model.component import Component, ComponentType
from cyclonedx.model.tool import ToolRepository
from cyclonedx.output.json import JsonV1Dot6
from cyclonedx.schema import SchemaVersion
from cyclonedx.validation.json import JsonStrictValidator
from envgenehelper import logger
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError
from packageurl import PackageURL
from pydantic import ValidationError
from sbom_generator.utils.errors import NotFoundException, IllegalArgumentException, PydanticValidationError
from sbom_generator.utils.models import Configuration, ARTIFACT_TYPE_TO_MIME, AppChart
from sbom_generator.utils.models import MimeType, SBOMOutput, Service, Data, \
    Content, Attachment, CustomComponent, DeploymentDescriptor
from sbom_generator.utils.utils import load_schema, encode_dict_to_base64, load_file, list_files, \
    find_file_by_name_in_dir

from envgenehelper.deploy_plan_adapter import EnvgeneDeployPlan, DeployPlanEntity

jschon.create_catalog('2020-12')


def _load_registry(reg_defs_path, registry_name):
    file_path = find_file_by_name_in_dir(reg_defs_path, registry_name)
    if not file_path:
        raise NotFoundException(f"There is no file by name {registry_name} in dir {reg_defs_path}")
    data = load_file(file_path)
    return parse_registry(data)


def _stable_bom_ref(*parts: str) -> str:
    return hashlib.sha256(':'.join(parts).encode()).hexdigest()[:16]


def build_tool():
    pkg = "sbom_generator"
    pkg_metadata = metadata(pkg)
    return Component(
        name=pkg_metadata["Name"],
        version=version(pkg),
        type=ComponentType.APPLICATION
    )


def build_sd_sbom_component(sd_app_def: Application, sd_app_ver: str, tools: ToolRepository):
    if sd_app_def:
        sd_version = sd_app_ver.split(':')[1]
        solution_component = Component(
            mime_type=MimeType.SOLUTION,
            name=sd_app_def.name,
            version=sd_version,
            type=ComponentType.APPLICATION
        )

        mvn_purl = PackageURL(type='maven', namespace=sd_app_def.group_id, name=sd_app_def.artifact_id,
                              version=sd_version,
                              qualifiers={"registry_id": sd_app_def.registry.name})

        sd_component = Component(
            mime_type=MimeType.SOLUTION_DESCRIPTOR,
            name=sd_app_def.artifact_id,
            version=sd_version,
            group=sd_app_def.group_id,
            type=ComponentType.DATA,
            purl=mvn_purl
        )
    else:
        solution_component = Component(
            mime_type=MimeType.SOLUTION,
            name="Solution",
            version="",
            type=ComponentType.APPLICATION
        )

        sd_component = Component(
            mime_type=MimeType.SOLUTION_DESCRIPTOR,
            name="",
            version="",
            group="",
            type=ComponentType.DATA
        )

    sd_bom = Bom()
    sd_metadata = BomMetaData()
    sd_metadata.tools = tools
    sd_metadata.component = solution_component
    sd_metadata.component.components = [sd_component]
    sd_bom.metadata = sd_metadata
    return sd_bom


def lookup_sub_entities(app_artifacts_local_path: Path, parent_entity_name: str) -> (str, Path):
    sub_entities_info = []
    entity_path = app_artifacts_local_path.joinpath(parent_entity_name)
    lookup_path = Path(f"{entity_path}/charts/{parent_entity_name}/charts")
    if lookup_path.exists() and lookup_path.is_dir():
        names = [p.name for p in lookup_path.iterdir() if p.is_dir()]
        for name in names:
            entity_configs_path = lookup_path.joinpath(name)
            sub_entities_info.append((name, entity_configs_path))
            logger.info(f"Additional entity found {name}")
    return sub_entities_info


def generate_app_components(app_name: str, registry: Registry, app_dd, app_artifacts_local_path: Path) -> list[
    Component]:
    app_components = []
    service_names = [s.service_name for s in app_dd.services]
    for service in app_dd.services:
        # in services can be not only services
        if service.image_type == 'service':
            service_configs_path = app_artifacts_local_path.joinpath(service.service_name)
            app_components.append(
                generate_service_component(service, service_configs_path, registry))

            sub_entities_info = lookup_sub_entities(app_artifacts_local_path, service.service_name)
            for sub_entity_name, sub_entity_configs_path in sub_entities_info:
                if sub_entity_name not in service_names:
                    # parameters from parent entity transfer to sub entity
                    sub_entity = service.copy()
                    sub_entity.service_name = sub_entity_name
                    app_components.append(
                        generate_service_component(sub_entity, sub_entity_configs_path, registry))
        elif service.image_type == 'image':
            app_components.append(generate_octet_stream(service, registry))

    for smartplug in app_dd.smartplug:
        cfg_configs_path = app_artifacts_local_path.joinpath(smartplug.name)
        cfg_cmp = generate_configuration_component(smartplug, MimeType.SMARTPLUG, cfg_configs_path)
        app_components.append(cfg_cmp)
        sub_entities_info = lookup_sub_entities(app_artifacts_local_path, smartplug.name)
        for sub_entity_name, sub_entity_configs_path in sub_entities_info:
            # parameters from parent entity transfer to sub entity
            sub_entity = smartplug.copy()
            sub_entity.name = sub_entity_name
            app_components.append(
                generate_configuration_component(smartplug, MimeType.SMARTPLUG, cfg_configs_path))

    for cfg in app_dd.configurations:
        cfg_configs_path = app_artifacts_local_path.joinpath(cfg.name)
        cfg_type = cfg.type
        if cfg_type and (cfg_type == 'cdn' or cfg_type == 'cdn-cr'):
            cfg_cmp = generate_configuration_component(cfg, MimeType.CDN, cfg_configs_path)
            app_components.append(cfg_cmp)
            sub_entities_info = lookup_sub_entities(app_artifacts_local_path, cfg.name)
            for sub_entity_name, sub_entity_configs_path in sub_entities_info:
                # parameters from parent entity transfer to sub entity
                sub_entity = cfg.copy()
                sub_entity.name = sub_entity_name
                app_components.append(
                    generate_configuration_component(cfg, MimeType.CDN, cfg_configs_path))
        else:
            cfg_cmp = generate_configuration_component(cfg, MimeType.CONFIGURATION, cfg_configs_path)
            app_components.append(cfg_cmp)
            sub_entities_info = lookup_sub_entities(app_artifacts_local_path, cfg.name)
            for sub_entity_name, sub_entity_configs_path in sub_entities_info:
                # parameters from parent entity transfer to sub entity
                sub_entity = cfg.copy()
                sub_entity.name = sub_entity_name
                app_components.append(
                    generate_configuration_component(cfg, MimeType.CONFIGURATION, cfg_configs_path))
    for chart in app_dd.charts:
        app_components.append(generate_app_chart_component(app_name, chart))

    return app_components


def generate_octet_stream(service: Service, registry) -> Component:
    properties = []
    octet_component = Component(
        mime_type=MimeType.OCTET,
        name=service.service_name,
        type=ComponentType.APPLICATION,
        version=service.version,
        bom_ref=_stable_bom_ref(MimeType.OCTET, service.service_name, service.version)
    )
    properties.append(Property(name='git_branch', value=service.git_branch))
    properties.append(Property(name='git_revision', value=service.git_revision))
    properties.append(Property(name='image_type', value=service.image_type))
    properties.append(Property(name='qualifier', value=service.qualifier))
    properties.append(Property(name='promote_artifacts', value=service.promote_artifacts))
    properties.append(Property(name='deploy_param', value=service.deploy_param))
    properties.append(Property(name='git_url', value=service.git_url))
    properties.append(Property(name='docker_registry', value=service.docker_registry))
    properties.append(Property(name='full_image_name', value=service.full_image_name))
    octet_component.properties = properties
    hashes = generate_hashes(service)
    image_component = Component(
        mime_type=MimeType.IMAGE,
        name=service.image_name,
        type=ComponentType.CONTAINER,
        group=service.docker_repository_name,
        version=service.docker_tag,
        purl=generate_docker_purl(service, registry),
        bom_ref=_stable_bom_ref(MimeType.IMAGE, service.image_name, service.docker_repository_name,
                                service.docker_tag)
    )
    image_component.hashes = hashes
    octet_component.components.add(image_component)
    return octet_component


def generate_hashes(service: Service):
    hashes = []
    if service.docker_digest:
        hashes = [HashType(alg=HashAlgorithm.SHA_256, content=service.docker_digest)]
    return hashes


def generate_docker_purl(service: Service, registry):
    # TODO will be another way getting docker pointer for a hierarchical structure of registries
    image_purl = PackageURL(type='docker', namespace=service.docker_repository_name,
                            name=service.image_name,
                            version=service.docker_tag)
    docker_repo_pointer = get_docker_repo_pointer(service, registry)
    if docker_repo_pointer:
        qualifiers = {"registry_id": f"{registry.name}",
                      "repository_id": f"{docker_repo_pointer}"}
        image_purl.qualifiers.update(qualifiers)
    else:
        qualifiers = {"registry_id": f"{registry.name}"}
        image_purl.qualifiers.update(qualifiers)
    return image_purl


def get_docker_repo_pointer(service: Service, registry) -> str | None:
    if not registry.docker_config:
        logger.warning(f"No docker_config for registry {registry.name}")
        return None
    docker_config = registry.docker_config.model_dump(by_alias=True)

    for key, value in docker_config.items():
        if 'uri' in key and not value:
            logger.warning(f"Docker repository {key} is not configured for registry {registry.name}")

    docker_repo_pointer = next(
        (key for key, value in docker_config.items() if 'uri' in key.lower() and value == service.docker_registry),
        None)

    if not docker_repo_pointer:
        logger.warning(
            f"Docker repository pointer wasn't found in registry {registry.name} for {service.service_name}")
    return docker_repo_pointer


def generate_service_component(service: Service, service_configs_path: Path, registry) -> Component:
    properties = []
    service_component = Component(
        mime_type=MimeType.SERVICE,
        name=service.service_name,
        type=ComponentType.APPLICATION,
        version=service.version,
        bom_ref=_stable_bom_ref(MimeType.SERVICE, service.service_name, service.version)
    )
    properties.append(Property(name='git_branch', value=service.git_branch))
    properties.append(Property(name='git_revision', value=service.git_revision))
    properties.append(Property(name='git_version', value=service.version))
    properties.append(Property(name='image_type', value=service.image_type))
    properties.append(Property(name='qualifier', value=service.qualifier))
    properties.append(Property(name='promote_artifacts', value=service.promote_artifacts))
    properties.append(Property(name='deploy_param', value=service.deploy_param))
    properties.append(Property(name='git_url', value=service.git_url))
    properties.append(Property(name='docker_registry', value=service.docker_registry))
    properties.append(Property(name='full_image_name', value=service.full_image_name))
    service_component.properties = properties

    image_cmp = Component(
        mime_type=MimeType.IMAGE,
        name=service.service_name,
        type=ComponentType.CONTAINER,
        group=service.docker_repository_name,
        purl=generate_docker_purl(service, registry),
        version=service.docker_tag,
        bom_ref=_stable_bom_ref(MimeType.IMAGE, service.service_name, service.docker_repository_name,
                                service.docker_tag)
    )
    image_cmp.hashes = generate_hashes(service)
    service_component.components.add(image_cmp)

    profile_cmp = generate_profile_component(service_configs_path, service.service_name)
    if profile_cmp:
        service_component.components.add(profile_cmp)
    return service_component


def generate_profile_component(entity_configs_path: Path, entity_name: str):
    profiles = []
    profile_paths = list_files(Path(f'{entity_configs_path}/helm-templates/{entity_name}/resource-profiles/'))
    if not profile_paths:
        profile_paths = list_files(Path(f'{entity_configs_path}/charts/{entity_name}/resource-profiles/'))
    for profile_path in profile_paths:
        profiles_dict = load_file(profile_path)
        profile_encoded = encode_dict_to_base64(profiles_dict, profile_path.suffix)
        content = Content(
            attachment=Attachment(content_type='application/yaml', content=profile_encoded))
        data = Data(name=profile_path.name, contents=content)
        profiles.append(data.model_dump(by_alias=True))

    if profiles:
        profile_cmp = CustomComponent(
            mime_type=MimeType.RESOURCE_PROFILE,
            name='resource-profile-baselines',
            type=ComponentType.DATA,
            data=profiles,
            bom_ref=_stable_bom_ref(MimeType.RESOURCE_PROFILE, entity_name)
        )
        return profile_cmp


def generate_configuration_component(configuration: Configuration, cfg_mime_type: MimeType,
                                     cfg_configs_path) -> Component | None:
    properties = [Property(name='git_branch', value=configuration.git_branch),
                  Property(name='git_revision', value=configuration.git_revision),
                  Property(name='version', value=configuration.version),
                  Property(name='build_id_dtrust', value=configuration.build_id_dtrust),
                  Property(name='git_url', value=configuration.git_url),
                  Property(name='type', value=configuration.type),
                  Property(name='maven_repository', value=configuration.maven_repository)]
    configuration_component = Component(
        mime_type=cfg_mime_type,
        name=configuration.name,
        type=ComponentType.APPLICATION,
        properties=properties,
        version=configuration.version,
        bom_ref=_stable_bom_ref(cfg_mime_type, configuration.name, configuration.version)
    )

    artifacts = configuration.artifacts
    if artifacts:
        for artifact in artifacts:
            artifact_type = artifact.type
            if ARTIFACT_TYPE_TO_MIME.get(artifact_type):
                artifact_group = artifact.id.split(':')[0]
                artifact_name = artifact.id.split(':')[1]
                artifact_version = artifact.id.split(':')[2]
                artifact_cmp = Component(
                    mime_type=ARTIFACT_TYPE_TO_MIME[artifact_type],
                    name=artifact_name,
                    type=ComponentType.APPLICATION,
                    group=artifact_group,
                    version=artifact_version,
                    properties=[Property(name='type', value=artifact_type),
                                Property(name='classifier', value=artifact.classifier)],
                    bom_ref=_stable_bom_ref(ARTIFACT_TYPE_TO_MIME[artifact_type], artifact_group, artifact_name,
                                            artifact_version, artifact.classifier)
                )
                configuration_component.components.add(artifact_cmp)

    profile_cmp = generate_profile_component(cfg_configs_path, configuration.name)
    if profile_cmp:
        configuration_component.components.add(profile_cmp)
    return configuration_component


def validate_sbom(raw_sbom):
    sbom = JsonV1Dot6(raw_sbom).output_as_string()
    # TODO dirty hack due to mime-type in cyclonedx-python-lib has wrong serializable
    sbom = sbom.replace("mimeType", "mime-type")
    validator = JsonStrictValidator(schema_version=SchemaVersion.V1_6)
    validation_errors = validator.validate_str(sbom)
    if validation_errors:
        logger.error(f"Errors after validation v1.6 schema: {validation_errors}")
    return sbom


def validate_and_sort_by_schema(obj, schema_name: str):
    obj_json = json.loads(obj)
    schema = load_schema(schema_name)
    try:
        jsonschema.validate(obj_json, schema)
        obj_sorted = jschon_tools.process_json_doc(
            schema_data=schema,
            doc_data=obj_json,
            sort=True
        )
        return obj_sorted
    except JsonSchemaValidationError as ex:
        joined_errors = "\n".join(str(error) for error in ex.context)
        logger.error(f"SBOM for validation: {obj} \n"
                     f"Error during validation according to {schema_name} schema, details: {joined_errors}")
        raise ex


def _match_appver_to_dd_artifact(
        sd_content: EnvgeneDeployPlan,
        dd_artifacts: list[ArtifactDownload]) -> list[tuple[str, str, ArtifactDownload]]:
    dd_artifact_info_map = {}
    for candidate in dd_artifacts:
        version_dir = Path(candidate.local_target_path).parent
        # APP_ARTIFACTS_DIR/<app_name>/<version>/<dd file>
        dd_artifact_info_map[(version_dir.parent.name, version_dir.name)] = candidate

    matches = []
    unmatched_apps = []
    snapshot_appvers = []
    for app in sd_content.entities:
        app_name, app_version = app.version.split(':', 1)
        if 'SNAPSHOT' in app_version:
            snapshot_appvers.append(app.version)
            continue
        dd_artifact = dd_artifact_info_map.get((app_name, app_version))
        if dd_artifact is None:
            unmatched_apps.append(app.version)
        else:
            matches.append((app_name, app_version, dd_artifact))

    if snapshot_appvers:
        raise IllegalArgumentException(
            f"SNAPSHOT is not supported version of Deployment Descriptor artifacts: {', '.join(snapshot_appvers)}")
    if unmatched_apps:
        raise NotFoundException(
            f"Deployment descriptor was not found for applications: {', '.join(unmatched_apps)}")

    return matches


def generate_boms(sd_content: EnvgeneDeployPlan, dd_artifacts: list[ArtifactDownload]) -> SBOMOutput:
    logger.info(f"Starting SBOM generation for {len(sd_content.entities)} applications")
    registries_map = {}
    sboms_map = {}
    matches = _match_appver_to_dd_artifact(sd_content, dd_artifacts)

    start_time = time.perf_counter()
    for app_name, app_version, dd_artifact in matches:
        logger.info(f'Processing application {app_name}:{app_version}')
        app_def = dd_artifact.source.application
        registry = app_def.registry
        repo_value = dd_artifact.source.repository.type.value

        dd_path = Path(dd_artifact.local_target_path)
        app_artifacts_local_path = dd_path.parent / dd_path.stem / app_def.artifact_id

        app_raw_sbom = Bom()
        app_raw_sbom.serial_number = None
        app_raw_sbom.timestamp = None
        app_raw_sbom.metadata = generate_metadata(app_def=app_def, app_version=app_version, repo=repo_value)

        try:
            app_dd = DeploymentDescriptor.by_path_with_app(dd_path, app_def, repo_value)
        except ValidationError as e:
            raise PydanticValidationError(original=e, type_obj=DeploymentDescriptor.__name__, src_path=dd_path)
        if is_dd_valid(app_dd, app_name):
            appver = f'{app_name}:{app_version}'
            app_raw_sbom.components = generate_app_components(app_name=app_name, registry=registry, app_dd=app_dd,
                                                              app_artifacts_local_path=app_artifacts_local_path)
            app_sbom = validate_sbom(app_raw_sbom)
            registry_name_encoded = urllib.parse.quote(registry.name)
            registries_map.setdefault(registry_name_encoded, registry)

            app_sbom_sorted = validate_and_sort_by_schema(app_sbom, schema_name="application")
            sboms_map.setdefault(appver, app_sbom_sorted)
            logger.debug(f'Application {app_name} SBOM was generated successfully {app_sbom_sorted}')

    end_time = time.perf_counter()
    logger.info(f"SBOM generation finished for {len(sboms_map)} applications: {end_time - start_time:.6f} sec")
    return SBOMOutput(registries=registries_map, sboms=sboms_map)


def is_dd_valid(app_dd, app_name: str) -> bool:
    if app_dd.services or app_dd.smartplug or app_dd.configurations or app_dd.charts:
        return True

    logger.warning(f'Application SBOM generation was skipped for {app_name}, because services, smartplugs, '
                   f'configurations, charts are empty')
    return False


def generate_app_chart_component(app_name: str, app_chart: AppChart) -> Component:
    return Component(
        mime_type=MimeType.APP_CHART,
        name=app_name,
        type=ComponentType.APPLICATION,
        version=app_chart.helm_chart_version,
        bom_ref=_stable_bom_ref(MimeType.APP_CHART, app_name, app_chart.helm_chart_version)
    )


def generate_metadata(app_def: Application, app_version: str, repo: str):
    mvn_purl = PackageURL(type='maven', namespace=app_def.group_id, name=app_def.artifact_id,
                          version=app_version,
                          qualifiers={"registry_id": app_def.registry.name,
                                      "repository_id": repo})
    dd_component = Component(
        mime_type=MimeType.DEPLOYMENT_DESCRIPTOR,
        name=app_def.artifact_id,
        group=app_def.group_id,
        version=app_version,
        purl=mvn_purl,
        type=ComponentType.DATA,
        bom_ref=_stable_bom_ref(MimeType.DEPLOYMENT_DESCRIPTOR, app_def.group_id, app_def.artifact_id,
                                app_version)
    )

    eso_property = Property(name='eso_support', value="false")
    dd_component.properties.add(eso_property)

    app_metadata_component = Component(
        mime_type=MimeType.APPLICATION,
        name=app_def.name,
        version=app_version,
        type=ComponentType.APPLICATION,
        bom_ref=_stable_bom_ref(MimeType.APPLICATION, app_def.name, app_version)
    )
    app_metadata = BomMetaData()
    app_metadata.timestamp = None
    app_metadata.component = app_metadata_component
    app_metadata.component.components = [dd_component]
    app_metadata.tools.components.add(build_tool())
    return app_metadata


def exclude_resolved_apps(sd: EnvgeneDeployPlan, sbom_dir_path: Path) -> list[DeployPlanEntity]:
    result = []

    for app in sd.entities:
        app_name = app.version.split(':')[0]
        app_ver_filename = app.version.replace(":", "-")
        sbom_app_path = sbom_dir_path / app_name / f'{app_ver_filename}.sbom.json'

        if not sbom_app_path.exists():
            result.append(app)
            continue

        logger.info(f"Generating sboms for app '{app.version}' skipped")

    return result


class Generator:
    @staticmethod
    def generate_bom_by_content(sd_content: EnvgeneDeployPlan, dd_artifacts: list[ArtifactDownload],
                                sbom_dir_path: Path) -> SBOMOutput:
        sd_content.entities = exclude_resolved_apps(sd_content, sbom_dir_path)
        return generate_boms(sd_content=sd_content, dd_artifacts=dd_artifacts)
