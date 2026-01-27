import os
import shutil
import json
from enum import auto, Enum
from pathlib import Path

from envgenehelper.business_helper import get_current_env_dir_from_env_vars, getenv_with_error, get_namespaces, get_bgd_object
from envgenehelper.file_helper import deleteFileIfExists
from envgenehelper.yaml_helper import openYaml
from envgenehelper import logger, writeYamlToFile

ENV_PATH = get_current_env_dir_from_env_vars()
NAMESPACES_PATH = os.path.join(ENV_PATH, 'Namespaces')
BG_STATE_STR = getenv_with_error('BG_STATE')
logger.info(f"Content of BG_STATE: {BG_STATE_STR}")
BG_STATE = json.loads(BG_STATE_STR)

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

def mirror_pair(pair: Pair) -> Pair:
    return pair[1], pair[0]

def pair_to_str(pair: Pair) -> str:
    return f'{{"origin": "{pair[0]}", "peer": "{pair[1]}"}}'

def is_mirrored(a: Pair, b: Pair) -> bool:
    return a == mirror_pair(b)

S = State

VALID_TRANSITIONS_BASE: dict[Pair, list[Pair]] = {
    (S.ACTIVE,S.NONE): [
        (S.ACTIVE,S.IDLE),
    ],
    (S.ACTIVE, S.IDLE): [
        (S.ACTIVE, S.CANDIDATE),
        (S.ACTIVE, S.FAILEDW),
        (S.ACTIVE, S.IDLE),
    ],
    (S.ACTIVE,S.CANDIDATE): [
        (S.LEGACY,S.ACTIVE),
        (S.ACTIVE,S.FAILEDC),
        (S.ACTIVE,S.IDLE),
    ],
    (S.LEGACY,S.ACTIVE): [
        (S.IDLE,S.ACTIVE),
        (S.FAILEDC,S.ACTIVE),
    ],
    (S.ACTIVE,S.FAILEDW): [
        (S.ACTIVE,S.CANDIDATE),
        (S.ACTIVE,S.FAILEDW),
    ],
    (S.ACTIVE,S.FAILEDC): [
        (S.IDLE, S.ACTIVE),
        (S.ACTIVE, S.FAILEDC),
    ],
    (S.FAILEDC, S.ACTIVE): [
        (S.IDLE, S.ACTIVE),
        (S.FAILEDC, S.ACTIVE),
    ]
}

NON_MIRRORABLE_STATES: list[Pair] = [(S.ACTIVE,S.NONE)]
VALID_TRANSITIONS = {}
for curr, valid_new_states in VALID_TRANSITIONS_BASE.items():
    VALID_TRANSITIONS.setdefault(curr, valid_new_states)
    if curr not in NON_MIRRORABLE_STATES:
        mirrored_curr = mirror_pair(curr)
        mirrored_new_states = [mirror_pair(n) for n in valid_new_states]
        VALID_TRANSITIONS.setdefault(mirrored_curr, mirrored_new_states)

def is_valid_transition(curr_state: Pair, new_state: Pair) -> tuple[bool, str]:
    valid_new_states = VALID_TRANSITIONS.get(curr_state, None)
    if valid_new_states is None:
        return False, "Current state is invalid"
    if new_state not in VALID_TRANSITIONS[curr_state]:
        return False, "Transition from current state to new one is invalid"
    return new_state in VALID_TRANSITIONS[curr_state], ""

def get_current_state() -> Pair:
    origin_state = S.NONE
    peer_state = S.NONE

    for file in Path(ENV_PATH).iterdir():
        if not file.is_file():
            continue
        name = file.name
        if not name.startswith(".") or "-" not in name:
            continue

        role, state = name[1:].split("-", 1)
        state_enum = getattr(State, state.upper(), None)
        if not state_enum:
            continue
        multiple_state_files_err_msg = f"Multiple state files found in {ENV_PATH}"

        if role == "origin":
            if origin_state != S.NONE: raise ValueError(multiple_state_files_err_msg + " for 'origin'")
            origin_state = state_enum
        elif role == "peer":
            if peer_state != S.NONE: raise ValueError(multiple_state_files_err_msg + " for 'peer'")
            peer_state = state_enum

    if origin_state == S.NONE and peer_state == S.NONE:
        origin_state = S.ACTIVE
        peer_state = S.NONE

    return origin_state, peer_state

def str_to_state(state: str) -> State:
    return getattr(State, state.upper(), S.NONE)

def get_new_state() -> Pair:
    origin_state = BG_STATE['originNamespace']['state']
    peer_state = BG_STATE['peerNamespace']['state']
    return str_to_state(origin_state), str_to_state(peer_state)

def validate_bg_state_namespace_names():
    bgd_file = get_bgd_object()
    origin_name_bg_state = BG_STATE['originNamespace']['name']
    peer_name_bg_state = BG_STATE['peerNamespace']['name']
    origin_name_file = bgd_file['originNamespace']['name']
    peer_name_file = bgd_file['peerNamespace']['name']
    if origin_name_bg_state != origin_name_file:
        raise ValueError('Origin namespace name in BG_STATE and bg_domain.yml do not match')
    if peer_name_bg_state != peer_name_file:
        raise ValueError('Peer namespace name in BG_STATE and bg_domain.yml do not match')

def update_current_state(curr_state: Pair, new_state: Pair):
    logger.info("Updating state files")
    deleteFileIfExists(os.path.join(ENV_PATH, f".origin-{curr_state[0]}"))
    deleteFileIfExists(os.path.join(ENV_PATH, f".peer-{curr_state[1]}"))
    open(os.path.join(ENV_PATH,f".origin-{new_state[0]}"),'w').close()
    open(os.path.join(ENV_PATH,f".peer-{new_state[1]}"),'w').close()
    logger.info("Successfully updated state files")

def make_operation_specific_changes(curr_state: Pair, new_state: Pair):
    transition = (curr_state, new_state)
    mirrored_transition = (mirror_pair(curr_state), mirror_pair(new_state))

    warm_up_operation = ((S.ACTIVE,S.IDLE),(S.ACTIVE,S.CANDIDATE))

    logger.info('Checking if current operation is warmup')
    if transition == warm_up_operation or mirrored_transition == warm_up_operation:
        logger.info('Current operation is warmup, copying content of "active" namespace to "candidate"')
        if new_state[0] == S.ACTIVE:
            active_ns = BG_STATE['originNamespace']['name']
            candidate_ns = BG_STATE['peerNamespace']['name']
        else:
            active_ns = BG_STATE['peerNamespace']['name']
            candidate_ns = BG_STATE['originNamespace']['name']
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
    logger.info('Finished check')

def run_bg_manage():
    curr_state = get_current_state()
    # validate_bg_state_namespace_names()
    new_state = get_new_state()
    logger.info(
        "Validating state transition.\n"
        f"Current state from repository: {pair_to_str(curr_state)}\n"
        f"Target state from BG_STATE: {pair_to_str(new_state)}"
    )
    is_valid, err_msg = is_valid_transition(curr_state, new_state)
    if not is_valid:
        raise ValueError(f"{err_msg}.\n")
    logger.info("Validation succeeded")
    make_operation_specific_changes(curr_state, new_state)
    update_current_state(curr_state, new_state)

if __name__ == "__main__":
    run_bg_manage()

