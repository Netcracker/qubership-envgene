"""Step definitions for Blue-Green Deployment BDD scenarios."""
import json
import yaml
from pathlib import Path
from pytest_bdd import given, then, parsers

from cucumber_tests.framework.workspace import EnvGeneWorkspace


# ── Setup steps ───────────────────────────────────────────────────────────────


@given(parsers.parse(
    'the bg_domain.yml is configured with origin namespace "{origin_ns}" and peer namespace "{peer_ns}"'
))
def configure_bg_domain(workspace: EnvGeneWorkspace, origin_ns: str, peer_ns: str) -> None:
    """Create bg_domain.yml in the environment directory for UC-BG-1 (no pre-existing state)."""
    env_dir = workspace.builder.get_env_dir(workspace.cluster_name, workspace.env_name)
    bg_domain = {
        "controllerNamespace": {"name": "controller-ns"},
        "originNamespace": {"name": origin_ns},
        "peerNamespace": {"name": peer_ns},
    }
    bg_domain_path = env_dir / "bg_domain.yml"
    with open(bg_domain_path, "w") as f:
        yaml.dump(bg_domain, f)


# ── Assertion steps ───────────────────────────────────────────────────────────


@then(parsers.parse('the Blue-Green state files are "{origin_file}" and "{peer_file}"'))
def assert_bg_state_files(
    workspace: EnvGeneWorkspace, origin_file: str, peer_file: str
) -> None:
    """Assert that exactly the expected two BG state files exist in the environment directory."""
    env_dir = workspace.builder.get_env_dir(workspace.cluster_name, workspace.env_name)
    state_files = {
        f.name
        for f in env_dir.iterdir()
        if f.is_file() and f.name.startswith(".")
        and any(s in f.name for s in ("-active", "-idle", "-candidate", "-legacy"))
    }

    assert origin_file in state_files, (
        f"Expected state file {origin_file!r} not found. "
        f"Actual state files: {state_files}\n"
        f"STDOUT: {workspace.stdout}\nSTDERR: {workspace.stderr}"
    )
    assert peer_file in state_files, (
        f"Expected state file {peer_file!r} not found. "
        f"Actual state files: {state_files}\n"
        f"STDOUT: {workspace.stdout}\nSTDERR: {workspace.stderr}"
    )
    assert len(state_files) == 2, (
        f"Expected exactly 2 BG state files, found {len(state_files)}: {state_files}"
    )


@then(parsers.parse('the namespace "{first_ns}" and namespace "{second_ns}" have the same content'))
def assert_namespaces_same_content(
    workspace: EnvGeneWorkspace, first_ns: str, second_ns: str
) -> None:
    """Assert that two namespace directories have identical file trees.

    Verifies the full copytree result of warmup: every file in the active namespace
    is present in the candidate namespace with the same content, except namespace.yml
    whose 'name' field is preserved from the candidate (bg_manage restores it after copy).
    Used by UC-BG-2 (Warmup) and UC-BG-6 (Reverse Warmup).
    """
    env_dir = workspace.builder.get_env_dir(workspace.cluster_name, workspace.env_name)
    ns_dir = env_dir / "Namespaces"

    first_dir = ns_dir / first_ns
    second_dir = ns_dir / second_ns

    assert first_dir.exists(), f"Namespace directory missing: {first_dir}"
    assert second_dir.exists(), f"Namespace directory missing: {second_dir}"

    first_files = {p.relative_to(first_dir) for p in first_dir.rglob("*") if p.is_file()}
    second_files = {p.relative_to(second_dir) for p in second_dir.rglob("*") if p.is_file()}

    only_in_first = first_files - second_files
    only_in_second = second_files - first_files
    assert not only_in_first, (
        f"Files present in {first_ns!r} but missing in {second_ns!r}: {sorted(str(p) for p in only_in_first)}\n"
        f"STDOUT: {workspace.stdout}\nSTDERR: {workspace.stderr}"
    )
    assert not only_in_second, (
        f"Files present in {second_ns!r} but missing in {first_ns!r}: {sorted(str(p) for p in only_in_second)}\n"
        f"STDOUT: {workspace.stdout}\nSTDERR: {workspace.stderr}"
    )

    # Compare every file except namespace.yml — bg_manage restores the candidate's 'name' after copy
    for rel_path in sorted(first_files):
        if rel_path.name == "namespace.yml":
            continue
        first_content = (first_dir / rel_path).read_text(encoding="utf-8")
        second_content = (second_dir / rel_path).read_text(encoding="utf-8")
        assert first_content == second_content, (
            f"Content mismatch for {rel_path} between {first_ns!r} and {second_ns!r}.\n"
            f"{first_ns}: {first_content!r}\n"
            f"{second_ns}: {second_content!r}\n"
            f"STDOUT: {workspace.stdout}\nSTDERR: {workspace.stderr}"
        )
