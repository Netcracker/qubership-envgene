import shutil
from enum import auto, Enum
from pathlib import Path

from dpg.v1.cmd import DeploymentPlanGeneratorCommand
from envgenehelper import logger, writeYamlToFile
from envgenehelper.business_helper import get_current_env_dir_from_env_vars, get_namespaces, \
    NamespaceRole, getEnvDefinitionPath
from envgenehelper.yaml_helper import openYaml
from envgenehelper.deploy_plan_adapter import EnvgeneDeployPlan
from pipeline.pipeline_parameters import PipelineParametersHandler


class State(Enum):
    ACTIVE = auto()
    IDLE = auto()
    CANDIDATE = auto()
    LEGACY = auto()
    FAILEDC = auto()
    FAILEDW = auto()
    NONE = auto()

    def __str__(self):
        return self.name.lower()


Pair = tuple[State, State]

S = State


def get_current_state() -> Pair:
    env_path = get_current_env_dir_from_env_vars()
    origin_state = S.NONE
    peer_state = S.NONE

    for file in Path(env_path).iterdir():
        if not file.is_file():
            continue
        name = file.name
        if not name.startswith(".") or "-" not in name:
            continue

        role, state = name[1:].split("-", 1)
        state_enum = getattr(State, state.upper(), None)
        if not state_enum:
            continue
        multiple_state_files_err_msg = f"Multiple state files found in {env_path}"

        if role == NamespaceRole.ORIGIN:
            if origin_state != S.NONE: raise ValueError(multiple_state_files_err_msg + " for 'origin'")
            origin_state = state_enum
        elif role == NamespaceRole.PEER:
            if peer_state != S.NONE: raise ValueError(multiple_state_files_err_msg + " for 'peer'")
            peer_state = state_enum

    if origin_state == S.NONE and peer_state == S.NONE:
        origin_state = S.ACTIVE
        peer_state = S.NONE

    return origin_state, peer_state


def run_warmup(ctx: PipelineParametersHandler):
    curr_state = get_current_state()
    active_role = NamespaceRole.ORIGIN if curr_state[0] == S.ACTIVE else NamespaceRole.PEER
    candidate_role = NamespaceRole.PEER if active_role == NamespaceRole.ORIGIN else NamespaceRole.ORIGIN

    namespaces = get_namespaces()
    active_ns = next((ns for ns in namespaces if ns.role == active_role))
    candidate_ns = next((ns for ns in namespaces if ns.role == candidate_role))
    logger.info(f'Active ns: {active_ns.name}, Candidate ns: {candidate_ns.name}')

    shutil.rmtree(candidate_ns.path, ignore_errors=True)
    shutil.copytree(active_ns.path, candidate_ns.path)

    candidate_ns_file_path = candidate_ns.definition_path
    candidate_ns_file = openYaml(candidate_ns_file_path)
    candidate_ns_file['name'] = candidate_ns.name
    writeYamlToFile(candidate_ns_file_path, candidate_ns_file)

    logger.info('Copying was successful')

    sync_bg_ns_artifacts(active_ns.role, candidate_ns.role)
    create_dp_for_warmup(ctx, active_ns.name, candidate_ns.name)


def create_dp_for_warmup(ctx: PipelineParametersHandler, active_namespace: str, candidate_namespace: str):
    full_plan = ctx.deploy_plan
    active_entities = DeploymentPlanGeneratorCommand.filter(
        deploy_plan=full_plan, namespace_filter=active_namespace).entities
    if not active_entities:
        raise ValueError(
            f"Cannot create warmup delta: full deploy plan has no entries for active namespace '{active_namespace}'")

    candidate_entities = [
        entity.model_copy(update={"namespace": candidate_namespace})
        for entity in active_entities
    ]
    ctx.deploy_plan_delta = EnvgeneDeployPlan(entities=candidate_entities)
    ctx.deploy_plan_delta.write(EnvgeneDeployPlan.delta_path())
    logger.info(f"Created warmup delta for candidate '{candidate_namespace}':\n{ctx.deploy_plan_delta}")


def sync_bg_ns_artifacts(active_role: NamespaceRole, candidate_role: NamespaceRole):
    env_definition_path = getEnvDefinitionPath(get_current_env_dir_from_env_vars())
    env_definition = openYaml(env_definition_path, allow_default=True)
    bg_ns_artifacts = env_definition.get('envTemplate', {}).get('bgNsArtifacts')

    if not bg_ns_artifacts or active_role not in bg_ns_artifacts:
        logger.info('envTemplate.bgNsArtifacts is not set, skipping sync')
        return

    logger.info(f'Syncing envTemplate.bgNsArtifacts: "{candidate_role}" := "{active_role}"')
    bg_ns_artifacts[candidate_role] = bg_ns_artifacts[active_role]
    writeYamlToFile(env_definition_path, env_definition)
