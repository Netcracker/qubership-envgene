import os
import shutil
from enum import auto, Enum
from pathlib import Path

from envgenehelper.business_helper import get_current_env_dir_from_env_vars, getenv_with_error, get_namespaces, \
    get_bgd_object, NamespaceRole
from envgenehelper.file_helper import deleteFileIfExists
from envgenehelper.yaml_helper import openYaml
from envgenehelper import logger, writeYamlToFile


class State(Enum):
    ACTIVE = auto()
    IDLE = auto()
    CANDIDATE = auto()
    LEGACY = auto()
    NONE = auto()

    def __str__(self):
        return self.name.lower()


class OperationType(Enum):
    BGD_INIT = "BGD-INIT"
    BGD_WARMUP = "BGD-WARMUP"
    BGD_PROMOTE = "BGD-PROMOTE"
    BGD_COMMIT = "BGD-COMMIT"
    BGD_ROLLBACK = "BGD-ROLLBACK"
    
    @classmethod
    def from_str(cls, value: str) -> "OperationType | None":
        for member in cls:
            if member.value == value:
                return member
        return None


Pair = tuple[State, State]


def mirror_pair(pair: Pair) -> Pair:
    return pair[1], pair[0]


def pair_to_str(pair: Pair) -> str:
    return f'{{"origin": "{pair[0]}", "peer": "{pair[1]}"}}'


S = State

VALID_TRANSITIONS_BASE: dict[OperationType, dict[Pair, Pair]] = {
    OperationType.BGD_INIT: {
        (S.ACTIVE, S.NONE): (S.ACTIVE, S.IDLE),
    },
    OperationType.BGD_WARMUP: {
        (S.ACTIVE, S.IDLE): (S.ACTIVE, S.CANDIDATE),
    },
    OperationType.BGD_PROMOTE: {
        (S.ACTIVE, S.CANDIDATE): (S.LEGACY, S.ACTIVE),
    },
    OperationType.BGD_COMMIT: {
        (S.LEGACY, S.ACTIVE): (S.IDLE, S.ACTIVE),
    },
    OperationType.BGD_ROLLBACK: {
        (S.LEGACY, S.ACTIVE): (S.IDLE, S.ACTIVE),
    },
}

NON_MIRRORABLE_OPERATIONS: set[OperationType] = {OperationType.BGD_INIT}

VALID_TRANSITIONS: dict[OperationType, dict[Pair, Pair]] = {}
for _op, _transitions in VALID_TRANSITIONS_BASE.items():
    _op_table = dict(_transitions)
    if _op not in NON_MIRRORABLE_OPERATIONS:
        for _curr, _nxt in _transitions.items():
            _op_table.setdefault(mirror_pair(_curr), mirror_pair(_nxt))
    VALID_TRANSITIONS[_op] = _op_table


def get_opeartion_type() -> OperationType | None:
    raw = getenv_with_error("OPERATION_TYPE")
    op = OperationType.from_str(raw)
    return op 


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
            if origin_state != S.NONE:
                raise ValueError(multiple_state_files_err_msg + " for 'origin'")
            origin_state = state_enum
        elif role == NamespaceRole.PEER:
            if peer_state != S.NONE:
                raise ValueError(multiple_state_files_err_msg + " for 'peer'")
            peer_state = state_enum

    if origin_state == S.NONE and peer_state == S.NONE:
        origin_state = S.ACTIVE
        peer_state = S.NONE

    return origin_state, peer_state


def get_new_state(op: OperationType, curr_state: Pair) -> Pair:
    op_table = VALID_TRANSITIONS.get(op)
    if op_table is None or curr_state not in op_table:
        raise ValueError(f"Operation {op.value} is not allowed from state {pair_to_str(curr_state)}")
    return op_table[curr_state]


def update_current_state(curr_state: Pair, new_state: Pair):
    env_path = get_current_env_dir_from_env_vars()
    logger.info("Updating state files")
    deleteFileIfExists(os.path.join(env_path, f".origin-{curr_state[0]}"))
    deleteFileIfExists(os.path.join(env_path, f".peer-{curr_state[1]}"))
    open(os.path.join(env_path, f".origin-{new_state[0]}"), 'w').close()
    open(os.path.join(env_path, f".peer-{new_state[1]}"), 'w').close()
    logger.info("Successfully updated state files")


def make_operation_specific_changes(op: OperationType, new_state: Pair):
    if op != OperationType.BGD_WARMUP:
        logger.info(f"Operation '{op.value} has no namespace sideffects")
        return
        
    logger.info('Operation is warmup, copying content of "active" namespace to "candidate"')
    bgd = get_bgd_object()

    if new_state[0] == S.ACTIVE:
        active_ns_name = bgd['originNamespace']['name']
        candidate_ns_name = bgd['peerNamespace']['name']
    else:
        active_ns_name = bgd['peerNamespace']['name']
        candidate_ns_name = bgd['originNamespace']['name']
    logger.info(f'Active ns: {active_ns_name}, Candidate ns: {candidate_ns_name}')

    namespaces = get_namespaces()
    active_ns = next(ns for ns in namespaces if ns.name == active_ns_name)
    candidate_ns = next(ns for ns in namespaces if ns.name == candidate_ns_name)

    shutil.rmtree(candidate_ns.path, ignore_errors=True)
    shutil.copytree(active_ns.path, candidate_ns.path)

    candidate_ns_file_path = candidate_ns.definition_path
    candidate_ns_file = openYaml(candidate_ns_file_path)
    candidate_ns_file['name'] = candidate_ns.name
    writeYamlToFile(candidate_ns_file_path, candidate_ns_file)

    logger.info('Copying and sync were successful')


def run_bg_manage():
    op = get_opeartion_type()
    if op is None:
        logger.info("OPERATION_TYPE not set to a recognised BGD value, skipping bg_manage")
        return
    
    curr_state = get_current_state()
    new_state = get_new_state(op, curr_state)
    logger.info(f"Operation '{op.value}' is allowed: {pair_to_str(curr_state)} -> {pair_to_str(new_state)}")

    make_operation_specific_changes(op, new_state)
    update_current_state(curr_state, new_state)
