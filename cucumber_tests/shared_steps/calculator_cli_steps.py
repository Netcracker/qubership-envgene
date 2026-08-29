"""Step definitions for Calculator CLI BDD scenarios (UC-CC-DP-*, UC-CC-MR-*, UC-CC-HR-*, UC-CC-CR-*,
UC-CC-PM-*, UC-CC-GI-*, UC-CC-CP-*).

All generic Given/When/Then steps come from shared_steps and are imported in test_calculator_cli.py.
"""
import re
import yaml

from pytest_bdd import then, parsers

from cucumber_tests.framework.workspace import EnvGeneWorkspace

# Production CLI entry point — present in the envgene Docker image under /module/
_PRODUCTION_CLI = "/module/scripts/utils/run_effective_set_cli.sh"

# mock-reg registry definition matching the purl in test SBOM files
_MOCK_REGISTRY = {
    "mock-reg": {
        "name": "mock-reg",
        "mavenConfig": {
            "targetSnapshot": "snapshot",
            "targetStaging": "staging",
            "targetRelease": "release",
            "repositoryDomainName": "http://localhost:8000/",
        },
    }
}


@then(parsers.parse('the effective set deployment parameters contain "{key_value}"'))
def effective_set_deployment_params_contain(workspace: EnvGeneWorkspace, key_value: str) -> None:
    es_dir = (
        workspace.base_dir
        / "environments" / workspace.cluster_name / workspace.env_name
        / "effective-set" / "deployment"
    )
    assert es_dir.exists(), f"effective-set/deployment directory does not exist at {es_dir}"
    found = False
    for params_file in es_dir.rglob("*.yaml"):
        if key_value in params_file.read_text(encoding="utf-8"):
            found = True
            break
    assert found, (
        f"'{key_value}' not found in any *.yaml under {es_dir}.\n"
        f"YAML files: {[str(p) for p in es_dir.rglob('*.yaml')]}"
    )


@then(parsers.parse('the effective set contains a generation id subdirectory for "{app_name}"'))
def effective_set_contains_generation_id_subdir(workspace: EnvGeneWorkspace, app_name: str) -> None:
    es_dir = (
        workspace.base_dir
        / "environments" / workspace.cluster_name / workspace.env_name
        / "effective-set" / "deployment"
    )
    assert es_dir.exists(), f"effective-set/deployment directory does not exist at {es_dir}"
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE
    )
    found = any(
        child.is_dir() and uuid_pattern.match(child.name)
        for app_dir in es_dir.rglob(app_name)
        if app_dir.is_dir()
        for child in app_dir.iterdir()
    )
    assert found, f"No UUID-named generation subdirectory found for app '{app_name}' under {es_dir}"


@then(parsers.parse('the effective set deployment parameters for "{app_name}" exist under version "{version}"'))
def effective_set_params_exist_under_version(workspace: EnvGeneWorkspace, app_name: str, version: str) -> None:
    es_dir = (
        workspace.base_dir
        / "environments" / workspace.cluster_name / workspace.env_name
        / "effective-set" / "deployment"
    )
    assert es_dir.exists(), f"effective-set/deployment directory does not exist at {es_dir}"
    found = any(
        (app_dir / version / "values").exists()
        for app_dir in es_dir.rglob(app_name)
        if app_dir.is_dir()
    )
    assert found, f"No version directory '{version}/values' found for app '{app_name}' under {es_dir}"


def _es_root(workspace: EnvGeneWorkspace):
    return workspace.base_dir / "environments" / workspace.cluster_name / workspace.env_name / "effective-set"


@then(parsers.parse('the effective set deployment parameters do not contain "{key_value}"'))
def effective_set_deployment_params_do_not_contain(workspace: EnvGeneWorkspace, key_value: str) -> None:
    es_dir = _es_root(workspace) / "deployment"
    assert es_dir.exists(), f"effective-set/deployment directory does not exist at {es_dir}"
    # credentials.yaml/collision-credentials.yaml are excluded: a sensitive value split out of
    # deployment-parameters.yaml is expected to land there, so an absence claim must not trip on it.
    offending = [
        p for p in es_dir.rglob("*.yaml")
        if "credentials" not in p.name and key_value in p.read_text(encoding="utf-8")
    ]
    assert not offending, f"'{key_value}' unexpectedly found in: {[str(p) for p in offending]}"


@then(parsers.parse('the effective set context "{context}" exists'))
def effective_set_context_exists(workspace: EnvGeneWorkspace, context: str) -> None:
    ctx_dir = _es_root(workspace) / context
    assert ctx_dir.is_dir(), f"effective-set/{context} directory does not exist at {ctx_dir}"


@then(parsers.parse('the effective set context "{context}" does not exist'))
def effective_set_context_does_not_exist(workspace: EnvGeneWorkspace, context: str) -> None:
    ctx_dir = _es_root(workspace) / context
    assert not ctx_dir.exists(), f"effective-set/{context} unexpectedly exists at {ctx_dir}"


@then(parsers.parse('the effective set deployment credentials contain "{key_value}"'))
def effective_set_deployment_credentials_contain(workspace: EnvGeneWorkspace, key_value: str) -> None:
    es_dir = _es_root(workspace) / "deployment"
    assert es_dir.exists(), f"effective-set/deployment directory does not exist at {es_dir}"
    cred_files = [p for p in es_dir.rglob("credentials.yaml")]
    found = any(key_value in p.read_text(encoding="utf-8") for p in cred_files)
    assert found, (
        f"'{key_value}' not found in any credentials.yaml under {es_dir}.\n"
        f"credentials.yaml files: {[str(p) for p in cred_files]}"
    )


@then(parsers.parse('the effective set runtime parameters contain "{key_value}"'))
def effective_set_runtime_params_contain(workspace: EnvGeneWorkspace, key_value: str) -> None:
    es_dir = _es_root(workspace) / "runtime"
    assert es_dir.exists(), f"effective-set/runtime directory does not exist at {es_dir}"
    yaml_files = list(es_dir.rglob("*.yaml"))
    found = any(key_value in p.read_text(encoding="utf-8") for p in yaml_files)
    assert found, (
        f"'{key_value}' not found in any *.yaml under {es_dir}.\n"
        f"YAML files: {[str(p) for p in yaml_files]}\n"
        f"Contents: {[(str(p), p.read_text(encoding='utf-8')) for p in yaml_files]}"
    )


@then(parsers.parse(
    '"{key}" is present in "{collision_file}" and absent from the root of "{source_file}"'))
def collision_key_moved(workspace: EnvGeneWorkspace, key: str, collision_file: str, source_file: str) -> None:
    es_dir = _es_root(workspace) / "deployment"
    assert es_dir.exists(), f"effective-set/deployment directory does not exist at {es_dir}"
    collision_paths = list(es_dir.rglob(collision_file))
    assert collision_paths, f"No {collision_file} found under {es_dir}"
    found_in_collision = False
    for cpath in collision_paths:
        collision_data = yaml.safe_load(cpath.read_text(encoding="utf-8")) or {}
        if key in collision_data:
            found_in_collision = True
            spath = cpath.parent / source_file
            source_data = (yaml.safe_load(spath.read_text(encoding="utf-8")) or {}) if spath.exists() else {}
            # NOTE: the root of deployment-parameters.yaml legitimately has a top-level key
            # named after every service (its own parameter section, see calculator-cli.md),
            # so "test-app" as a bare *key* is always present there when a service is named
            # "test-app" - that's unrelated to collision handling. What must actually be
            # absent from the root is the *scalar* colliding value itself.
            assert source_data.get(key) != collision_data[key], (
                f"'{key}' expected removed from the root of {spath} after moving to the "
                f"collision file, but the same scalar value {collision_data[key]!r} is still there"
            )
            break
    assert found_in_collision, f"'{key}' not found in any {collision_file} under {es_dir}"


@then(parsers.parse('the value of "{key}" is identical across all effective set files'))
def value_identical_across_all_files(workspace: EnvGeneWorkspace, key: str) -> None:
    es_dir = _es_root(workspace)
    assert es_dir.exists(), f"effective-set directory does not exist at {es_dir}"
    pattern = re.compile(rf'^\s*{re.escape(key)}\s*:\s*(.+?)\s*(?:#.*)?$')
    values_by_file = {}
    for yaml_path in es_dir.rglob("*.yaml"):
        for line in yaml_path.read_text(encoding="utf-8").splitlines():
            m = pattern.match(line)
            if m:
                values_by_file[str(yaml_path)] = m.group(1).strip().strip('"\'')
                break
    assert values_by_file, f"'{key}' not found in any file under {es_dir}"
    assert len(values_by_file) >= 2, (
        f"'{key}' was found in only one file, so 'identical across all files' is trivially true "
        f"and proves nothing: {values_by_file}"
    )
    distinct = set(values_by_file.values())
    assert len(distinct) == 1, f"'{key}' has differing values across files: {values_by_file}"


@then('the effective set deployment parameters are sorted alphabetically')
def effective_set_deployment_params_sorted(workspace: EnvGeneWorkspace) -> None:
    es_dir = _es_root(workspace) / "deployment"
    assert es_dir.exists(), f"effective-set/deployment directory does not exist at {es_dir}"
    checked = 0
    for params_path in es_dir.rglob("deployment-parameters.yaml"):
        data = yaml.safe_load(params_path.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict) or not data:
            continue
        checked += 1
        # "global" is a reserved aggregate section (collision-avoidance home for image params
        # that collide with a service name), not an ordinary parameter - it is excluded from the
        # ordering check the same way per-service-parameters (a separate directory) would be.
        keys = [k for k in data.keys() if k != "global"]
        assert keys == sorted(keys), f"Top-level keys not sorted alphabetically in {params_path}: {keys}"
    assert checked, f"No non-empty deployment-parameters.yaml found under {es_dir}"


@then(parsers.parse('the effective set deployment parameters for namespace "{namespace}" contain "{key_value}"'))
def effective_set_ns_params_contain(workspace: EnvGeneWorkspace, namespace: str, key_value: str) -> None:
    ns_dir = _es_root(workspace) / "deployment" / namespace
    assert ns_dir.exists(), f"effective-set/deployment/{namespace} directory does not exist at {ns_dir}"
    found = any(key_value in p.read_text(encoding="utf-8") for p in ns_dir.rglob("*.yaml"))
    assert found, f"'{key_value}' not found in any *.yaml under {ns_dir}"


@then(parsers.parse('the effective set deployment parameters for namespace "{namespace}" do not contain "{key}"'))
def effective_set_ns_params_do_not_contain(workspace: EnvGeneWorkspace, namespace: str, key: str) -> None:
    ns_dir = _es_root(workspace) / "deployment" / namespace
    assert ns_dir.exists(), f"effective-set/deployment/{namespace} directory does not exist at {ns_dir}"
    offending = [
        p for p in ns_dir.rglob("*.yaml")
        if "credentials" not in p.name and key in p.read_text(encoding="utf-8")
    ]
    assert not offending, f"'{key}' unexpectedly found in: {[str(p) for p in offending]}"
