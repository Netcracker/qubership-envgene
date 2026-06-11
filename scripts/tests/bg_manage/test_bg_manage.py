import pytest
import os
os.environ['BG_STATE'] = """
{
  "controllerNamespace": "ns-controller",
  "originNamespace": {
    "name": "bss",
    "state": "candidate",
    "version": "v5"
  },
  "peerNamespace": {
    "name": "core",
    "state": "active",
    "version": "v6"
  },
  "updateTime": "2023-07-07T10:00:54Z"
}
"""
from bg_manage import State, S, mirror_pair, is_valid_transition, VALID_TRANSITIONS, NON_MIRRORABLE_STATES

def test_valid_transition():
    assert is_valid_transition(
        (S.ACTIVE, S.IDLE), (S.ACTIVE, S.CANDIDATE)
    ) == (True, "")

def test_invalid_current_state():
    fake_state = (S.NONE, S.NONE)
    assert is_valid_transition(fake_state, (S.ACTIVE, S.IDLE)) == (
        False,
        "Current state is invalid",
    )

def test_invalid_new_state():
    curr = (S.ACTIVE, S.IDLE)
    bad_new_state = (S.IDLE, S.CANDIDATE)
    assert is_valid_transition(curr, bad_new_state) == (
        False,
        "Transition from current state to new one is invalid",
    )

def test_mirror_pair():
    assert mirror_pair((S.ACTIVE, S.IDLE)) == (S.IDLE, S.ACTIVE)

def test_mirrored_transition_exists():
    # Choose a pair that's mirrored
    original = (S.ACTIVE, S.CANDIDATE)
    mirrored = mirror_pair(original)
    for ns in VALID_TRANSITIONS[original]:
        assert mirror_pair(ns) in VALID_TRANSITIONS[mirrored]

def test_non_mirrorable_states_not_mirrored():
    for state in NON_MIRRORABLE_STATES:
        mirrored = mirror_pair(state)
        assert mirrored not in VALID_TRANSITIONS
