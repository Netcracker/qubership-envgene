import json
import yaml
import pytest
from pytest_bdd import scenarios, given, when, then, parsers


@given('Blue-Green state files are not created')
def state_files_not_created(workspace):
    pass

@given(parsers.parse('Blue-Green state files "{origin}" and "{peer}" exist'))
def state_files_exist(workspace, origin, peer):
    o_state = origin.split('-')[1]
    p_state = peer.split('-')[1]
    workspace.builder.set_bg_state_files(o_state, p_state)

@given(parsers.parse('Origin namespace "{origin}" and peer namespace "{peer}" exist with different contents'))
def namespaces_exist(workspace, origin, peer):
    workspace.builder.create_bg_namespaces(origin, peer, different_content=True)

@when(parsers.parse('the Instance pipeline is started with BG_MANAGE=true and BG_STATE for "{operation}"'))
def trigger_pipeline(workspace, operation):
    state_mapping = {
        "Init Domain":      {"origin": "active",    "peer": "idle"},
        "Warmup":           {"origin": "active",    "peer": "candidate"},
        "Promote":          {"origin": "legacy",    "peer": "active"},
        "Commit":           {"origin": "idle",      "peer": "active"},
        "Rollback":         {"origin": "idle",      "peer": "active"},
        "Reverse Warmup":   {"origin": "candidate", "peer": "active"},
        "Reverse Promote":  {"origin": "active",    "peer": "legacy"},
        "Reverse Commit":   {"origin": "active",    "peer": "idle"},
        "Reverse Rollback": {"origin": "active",    "peer": "idle"}
    }
    target = state_mapping[operation]
    bg_state = {
        "controllerNamespace": "controller-ns",
        "originNamespace": {"name": "origin-ns", "state": target["origin"], "version": "1.0"},
        "peerNamespace": {"name": "peer-ns", "state": target["peer"], "version": "1.0"},
        "updateTime": "2026-06-22T00:00:00Z"
    }

    bg_domain = {
        "controllerNamespace": {"name": "controller-ns"},
        "originNamespace": {"name": "origin-ns"},
        "peerNamespace": {"name": "peer-ns"}
    }
    bg_domain_path = workspace.builder.env_dir / "bg_domain.yml"
    with open(bg_domain_path, "w") as f:
        yaml.dump(bg_domain, f)

    res = workspace.run_pipeline(extra_env={
        "BG_MANAGE": "true",
        "BG_STATE": json.dumps(bg_state)
    })

    if res.returncode != 0:
        print("PIPELINE STDOUT:\n", res.stdout)
        print("PIPELINE STDERR:\n", res.stderr)

@then(parsers.parse('the Blue-Green state files become "{origin}" and "{peer}"'))
def assert_state_files(workspace, origin, peer):
    env_dir = workspace.builder.env_dir
    files = set(f.name for f in env_dir.iterdir() if f.is_file() and f.name.startswith("."))

    assert origin in files, f"Expected {origin} to be created, found {files}\nSTDOUT: {workspace.stdout}\nSTDERR: {workspace.stderr}"
    assert peer in files, f"Expected {peer} to be created, found {files}\nSTDOUT: {workspace.stdout}\nSTDERR: {workspace.stderr}"

    state_files = {f for f in files if "-active" in f or "-idle" in f or "-candidate" in f or "-legacy" in f}
    assert len(state_files) == 2, f"Expected exactly 2 state files, found {state_files}"

@then(parsers.parse('Origin namespace "{first}" and peer namespace "{second}" have the same content'))
def assert_namespaces_same(workspace, first, second):
    env_dir = workspace.builder.env_dir
    ns_dir = env_dir / "Namespaces"
    first_dir = ns_dir / first
    second_dir = ns_dir / second

    first_manifest = first_dir / "manifest.yaml"
    second_manifest = second_dir / "manifest.yaml"

    assert first_manifest.exists(), f"manifest.yaml missing in {first}"
    assert second_manifest.exists(), f"manifest.yaml missing in {second}"

    with open(first_manifest, "r") as f1, open(second_manifest, "r") as f2:
        assert f1.read() == f2.read(), f"Content mismatch between {first} and {second}"
