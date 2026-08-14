import shutil
import json
from enum import auto, Enum
from pathlib import Path

from envgenehelper.business_helper import get_current_env_dir_from_env_vars, getenv_with_error, get_namespaces, \
    NamespaceRole, getEnvDefinitionPath
from envgenehelper.yaml_helper import openYaml
from envgenehelper import logger, writeYamlToFile


def _bg_state():
    bg_state_str = getenv_with_error('BG_STATE')
    logger.info(f"Content of BG_STATE: {bg_state_str}")
    return json.loads(bg_state_str)


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


def run_warmup():
    curr_state = get_current_state()
    bg_state = _bg_state()
    if curr_state[0] == S.ACTIVE:
        active_ns = bg_state['originNamespace']['name']
        candidate_ns = bg_state['peerNamespace']['name']
    else:
        active_ns = bg_state['peerNamespace']['name']
        candidate_ns = bg_state['originNamespace']['name']
    logger.info(f'Active ns: {active_ns}, Candidate ns: {candidate_ns}')

    namespaces = get_namespaces()
    active_ns = next((ns for ns in namespaces if ns.name == active_ns))
    candidate_ns = next((ns for ns in namespaces if ns.name == candidate_ns))

    shutil.rmtree(candidate_ns.path, ignore_errors=True)
    shutil.copytree(active_ns.path, candidate_ns.path)

    candidate_ns_file_path = candidate_ns.definition_path
    candidate_ns_file = openYaml(candidate_ns_file_path)
    candidate_ns_file['name'] = candidate_ns.name
    writeYamlToFile(candidate_ns_file_path, candidate_ns_file)

    logger.info('Copying was successful')

    sync_bg_ns_artifacts(active_ns.role, candidate_ns.role)


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
