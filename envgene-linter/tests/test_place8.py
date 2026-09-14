from pathlib import Path

import pytest

from envgene_linter.discovery import build_index
from envgene_linter.engine import run_check
from envgene_linter.model import Action, IssueType, Location, Severity


def _write(repo, relative: str, body: str) -> Path:
    path = repo.root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _add_bindings(repo, cluster: str, env: str, body: str) -> None:
    definition = (
        repo.root / "environments" / cluster / env / "Inventory" / "env_definition.yml"
    )
    with definition.open("a", encoding="utf-8") as stream:
        stream.write(body)


def _place8(repo):
    return [finding for finding in run_check(repo.root).findings if finding.rule == "PLACE-8"]


def test_empty_bound_parameter_set(repo):
    repo.env("c", "e", deploy={"cloud": ["empty"]})
    path = repo.root / "environments/parameters/empty.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("parameters: {}\n", encoding="utf-8")

    findings = [f for f in run_check(repo.root).findings if f.rule == "PLACE-8"]

    assert len(findings) == 1
    assert findings[0].path == path
    assert findings[0].message == "ParameterSet 'empty.yml' is empty but is referenced or used by the generator."


@pytest.mark.parametrize(
    ("relative", "scope"),
    [
        ("environments/site.yml", "repository"),
        ("environments/c/parameters/cluster.yml", "c"),
        ("environments/c/e/Inventory/parameters/environment.yml", "c/e"),
    ],
)
def test_parameter_set_finding_has_exact_contract(repo, relative, scope):
    repo.env("c", "e", deploy={"cloud": ["site", "cluster", "environment"]})
    # The site-level case uses the required parameters directory.
    relative = relative.replace("environments/site.yml", "environments/parameters/site.yml")
    path = _write(repo, relative, "name: metadata-only\nparameters: {}\n")

    finding = _place8(repo)[0]

    assert finding.rule == "PLACE-8"
    assert finding.severity is Severity.INFORMATION
    assert finding.issue_type is IssueType.INFORMATION
    assert finding.action is Action.REVIEW
    assert finding.path == path
    assert (finding.line, finding.column) == (1, 1)
    assert finding.locations == (Location(path, 1, 1),)
    assert finding.key == path.stem
    assert finding.scope == scope
    assert finding.related == ()
    assert finding.hint == (
        "Review whether this empty file is intentional. "
        "If not, populate it or remove its reference or usage."
    )


@pytest.mark.parametrize(
    ("body", "reported"),
    [
        ("", True),
        ("# comment only\n", True),
        ("null\n", True),
        ("{}\n", True),
        ("name: p\nversion: 1\ndescription: x\n", True),
        ("parameters: {}\napplications: []\n", True),
        ("applications:\n  - name: app\n", True),
        ("parameters:\n  KEY:\n", False),
        ('parameters:\n  KEY: ""\n', False),
        ("parameters:\n  KEY: false\n", False),
        ("parameters:\n  KEY: 0\n", False),
        ("parameters:\n  KEY: {}\n", False),
        ("parameters:\n  KEY: []\n", False),
        ("applications:\n  - parameters:\n      KEY:\n", False),
        ("[]\n", False),
        ("parameters:\n", False),
        ("parameters: []\n", False),
        ("applications:\n", False),
        ("applications: {}\n", False),
        ("applications:\n  - null\n", False),
        ("applications:\n  - parameters:\n", False),
        ("encrypted: ENC[...]\n", False),
        ("other: value\nparameters: {}\n", False),
    ],
)
def test_parameter_set_structural_emptiness(repo, body, reported):
    repo.env("c", "e", deploy={"cloud": ["candidate"]})
    path = _write(repo, "environments/parameters/candidate.yml", body)
    assert (any(finding.path == path for finding in _place8(repo))) is reported


def test_bound_parameter_sets_include_every_surviving_resolution_entry(repo):
    repo.env("c", "e", deploy={"cloud": ["shared"]}, e2e={"bss": ["shared"]})
    site = _write(repo, "environments/parameters/shared.yml", "{}\n")
    cluster = _write(repo, "environments/c/parameters/shared.yml", "{}\n")
    environment = _write(repo, "environments/c/e/Inventory/parameters/shared.yaml", "{}\n")

    paths = {finding.path for finding in _place8(repo)}

    assert site not in paths  # shadowed by the same staged filename at cluster level
    assert cluster in paths
    assert environment in paths


def test_binding_in_any_environment_selects_shared_parameter_set(repo):
    repo.env("c", "bound", technical={"cloud": ["slot"]})
    repo.env("c", "other")
    path = _write(repo, "environments/parameters/slot.yml", "{}\n")
    assert path in {finding.path for finding in _place8(repo)}


@pytest.mark.parametrize("folder", ["resource_profiles", "rp_override", "Profiles"])
def test_discovers_empty_resource_profile_aliases_recursively(repo, folder):
    repo.env("c", "e")
    _add_bindings(repo, "c", "e", '  envSpecificResourceProfiles:\n    cloud: empty\n')
    path = _write(repo, f"environments/{folder}/nested/empty.yml", "{}\n")
    finding = next(finding for finding in _place8(repo) if finding.path == path)
    assert finding.message == "Resource Profile Override 'empty.yml' is empty but is referenced or used by the generator."
    assert finding.scope == "repository"


@pytest.mark.parametrize("folder", ["credentials", "Credentials", "shared-credentials"])
def test_discovers_empty_credentials_aliases_recursively(repo, folder):
    repo.env("c", "e")
    _add_bindings(repo, "c", "e", '  sharedMasterCredentialFiles: [empty]\n')
    path = _write(repo, f"environments/c/{folder}/nested/empty.yaml", "")
    finding = next(finding for finding in _place8(repo) if finding.path == path)
    assert finding.message == "Credentials file 'empty.yaml' is empty but is referenced or used by the generator."
    assert finding.scope == "c"


@pytest.mark.parametrize(
    ("body", "reported"),
    [
        ("", True),
        ("{}\n", True),
        ("name: p\nversion: 1\ndescription: x\nbaseline: base\n", True),
        ("applications: []\n", True),
        ("applications:\n  - name: app\n", True),
        ("applications:\n  - services: []\n", True),
        ("applications:\n  - services:\n      - name: service\n", True),
        ("applications:\n  - services:\n      - parameters: []\n", True),
        ("applications:\n  - services:\n      - parameters:\n          - null\n", False),
        ("applications:\n  - services:\n      - parameters:\n          - false\n", False),
        ("applications:\n  - services:\n      - parameters:\n          - 0\n", False),
        ('applications:\n  - services:\n      - parameters:\n          - ""\n', False),
        ("applications:\n", False),
        ("applications: {}\n", False),
        ("applications:\n  - null\n", False),
        ("applications:\n  - services:\n", False),
        ("applications:\n  - services:\n      - null\n", False),
        ("applications:\n  - services:\n      - parameters:\n", False),
        ("parameters: {}\n", False),
        ("encrypted: ENC[...]\n", False),
        ("[]\n", False),
    ],
)
def test_resource_profile_structural_emptiness(repo, body, reported):
    repo.env("c", "e")
    _add_bindings(repo, "c", "e", '  envSpecificResourceProfiles:\n    cloud: candidate\n')
    path = _write(repo, "environments/resource_profiles/candidate.yml", body)
    assert (any(finding.path == path for finding in _place8(repo))) is reported


@pytest.mark.parametrize(
    ("body", "reported"),
    [
        ("", True),
        ("null\n", True),
        ("{}\n", True),
        ("credential: {}\n", False),
        ("credential:\n", False),
        ("credential: false\n", False),
        ("credential: 0\n", False),
        ('credential: ""\n', False),
        ("encrypted: ENC[secret]\n", False),
        ("[]\n", False),
    ],
)
def test_credentials_structural_emptiness(repo, body, reported):
    repo.env("c", "e")
    _add_bindings(repo, "c", "e", '  sharedMasterCredentialFiles: [candidate]\n')
    path = _write(repo, "environments/credentials/candidate.yml", body)
    assert (any(finding.path == path for finding in _place8(repo))) is reported


def test_discovers_new_bindings_and_ignores_malformed_entries(repo):
    repo.env("c", "e")
    _add_bindings(
        repo,
        "c",
        "e",
        "  envSpecificResourceProfiles:\n"
        "    cloud: selected\n"
        "    numeric: 7\n"
        "  sharedMasterCredentialFiles:\n"
        "    - creds\n"
        "    - 9\n",
    )
    env = build_index(repo.root).environments[0]
    assert env.resource_profile_bindings == {"cloud": "selected"}
    assert env.shared_credential_bindings == ["creds"]


def test_malformed_new_binding_containers_are_ignored(repo):
    repo.env("c", "e")
    _add_bindings(
        repo,
        "c",
        "e",
        "  envSpecificResourceProfiles: []\n"
        "  sharedMasterCredentialFiles: {}\n",
    )
    env = build_index(repo.root).environments[0]
    assert env.resource_profile_bindings == {}
    assert env.shared_credential_bindings == []


@pytest.mark.parametrize(
    ("relative", "binding"),
    [
        ("environments/c/e/Inventory/rp_override/nested/slot.yml", "profile"),
        ("environments/c/Profiles/slot.yml", "profile"),
        ("environments/resource_profiles/slot.yaml", "profile"),
        ("environments/c/e/Inventory/Credentials/nested/slot.yml", "credentials"),
        ("environments/c/shared-credentials/slot.yml", "credentials"),
        ("environments/credentials/slot.yaml", "credentials"),
    ],
)
def test_visible_binding_resolves_each_search_level_and_alias(repo, relative, binding):
    repo.env("c", "e")
    if binding == "profile":
        _add_bindings(repo, "c", "e", "  envSpecificResourceProfiles:\n    cloud: slot\n")
    else:
        _add_bindings(repo, "c", "e", "  sharedMasterCredentialFiles:\n    - slot\n")
    path = _write(repo, relative, "{}\n")
    assert path in {finding.path for finding in _place8(repo)}


def test_first_occupied_bucket_selects_all_ambiguous_matches_and_shadows_lower_levels(repo):
    repo.env("c", "e")
    _add_bindings(repo, "c", "e", "  envSpecificResourceProfiles:\n    cloud: slot\n")
    first_a = _write(repo, "environments/c/e/Inventory/resource_profiles/a/slot.yml", "{}\n")
    first_b = _write(repo, "environments/c/e/Inventory/resource_profiles/b/slot.yaml", "{}\n")
    same_base_later_alias = _write(repo, "environments/c/e/Inventory/rp_override/slot.yml", "{}\n")
    cluster = _write(repo, "environments/c/resource_profiles/slot.yml", "{}\n")

    paths = {finding.path for finding in _place8(repo)}

    assert first_a in paths
    assert first_b in paths
    assert same_base_later_alias not in paths
    assert cluster not in paths


def test_parse_error_winner_occupies_binding_slot_and_skip_is_sanitized(repo):
    repo.env("c", "e")
    _add_bindings(repo, "c", "e", "  sharedMasterCredentialFiles:\n    - slot\n")
    bad = _write(repo, "environments/c/e/Inventory/credentials/slot.yml", "password: [TOP_SECRET\n")
    lower = _write(repo, "environments/credentials/slot.yml", "{}\n")

    result = run_check(repo.root)

    assert bad not in {finding.path for finding in result.findings if finding.rule == "PLACE-8"}
    assert lower not in {finding.path for finding in result.findings if finding.rule == "PLACE-8"}
    note = next(note for note in result.skipped if "slot.yml" in note)
    assert note == f"{bad}: cannot parse YAML; PLACE-8 skipped"
    assert "TOP_SECRET" not in note


def test_legacy_profile_parse_error_is_sanitized(repo):
    repo.env("c", "e")
    bad = _write(repo, "environments/parameters/bad.yml", "token: [LEGACY_SECRET\n")

    result = run_check(repo.root)

    note = next(note for note in result.skipped if str(bad) in note)
    assert note == f"{bad}: cannot parse YAML; ParameterSet skipped"
    assert "LEGACY_SECRET" not in note


def test_reference_matching_is_exact_and_cluster_local(repo):
    repo.env("a", "e")
    repo.env("b", "e")
    _add_bindings(repo, "a", "e", "  envSpecificResourceProfiles:\n    cloud: slot.yml\n")
    _add_bindings(repo, "b", "e", "  envSpecificResourceProfiles:\n    cloud: slot\n")
    a = _write(repo, "environments/a/resource_profiles/slot.yml", "{}\n")
    b = _write(repo, "environments/b/resource_profiles/slot.yml", "{}\n")

    paths = {finding.path for finding in _place8(repo)}

    assert a not in paths
    assert b in paths


def test_legacy_profile_shape_and_binding_use_profile_rules_without_duplicates(repo):
    repo.env("c", "e", deploy={"cloud": ["shaped", "ordinary"]})
    _add_bindings(repo, "c", "e", "  envSpecificResourceProfiles:\n    cloud: bound-legacy\n")
    shaped = _write(
        repo,
        "environments/parameters/shaped.yml",
        "applications:\n  - services:\n      - parameters: []\n",
    )
    bound = _write(repo, "environments/parameters/bound-legacy.yml", "{}\n")
    ordinary = _write(repo, "environments/parameters/ordinary.yml", "{}\n")

    findings = _place8(repo)

    assert [finding.path for finding in findings].count(shaped) == 1
    assert next(f for f in findings if f.path == shaped).message.startswith("Resource Profile Override")
    assert bound in {finding.path for finding in findings}
    assert next(f for f in findings if f.path == ordinary).message.startswith("ParameterSet")


def test_legacy_profile_with_mixed_payload_is_unknown(repo):
    repo.env("c", "e", deploy={"cloud": ["mixed"]})
    path = _write(
        repo,
        "environments/parameters/mixed.yml",
        "parameters: {}\napplications:\n  - services: []\n",
    )
    assert path not in {finding.path for finding in _place8(repo)}


@pytest.mark.parametrize(
    "body",
    [
        (
            "applications:\n"
            "  - services: []\n"
            "    parameters:\n"
            "      VALUE: 1\n"
        ),
        (
            "applications:\n"
            "  - parameters:\n"
            "      VALUE: 1\n"
            "  - services: []\n"
        ),
        (
            "applications:\n"
            "  - services: []\n"
            "    parameters: {}\n"
        ),
        (
            "applications:\n"
            "  - parameters:\n"
            "  - services: []\n"
        ),
    ],
    ids=("same-app-content", "split-app-content", "same-app-empty", "split-app-null"),
)
def test_legacy_profile_with_application_parameter_container_is_mixed(repo, body):
    repo.env("c", "e", deploy={"cloud": ["mixed"]})
    path = _write(repo, "environments/parameters/mixed.yml", body)
    assert path not in {finding.path for finding in _place8(repo)}


def test_templates_generated_output_and_outside_symlinks_are_skipped(repo, tmp_path):
    repo.env("c", "e", deploy={"cloud": ["outside"]})
    _add_bindings(repo, "c", "e",
        "  envSpecificResourceProfiles:\n    cloud: template\n    app: generated\n    other: outside\n"
        "  sharedMasterCredentialFiles: [generated]\n")
    jinja = _write(repo, "environments/resource_profiles/template.yml.j2", "{{ profile }}\n")
    generated_profile = _write(repo, "environments/c/e/Profiles/generated.yml", "{}\n")
    generated_credentials = _write(repo, "environments/c/e/Credentials/generated.yml", "{}\n")
    outside = tmp_path.parent / f"{tmp_path.name}-outside.yml"
    outside.write_text("{}\n", encoding="utf-8")
    link = repo.root / "environments/resource_profiles/outside.yml"
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(outside)
    parameter_link = repo.root / "environments/parameters/outside.yml"
    parameter_link.parent.mkdir(parents=True, exist_ok=True)
    parameter_link.symlink_to(outside)

    result = run_check(repo.root)
    paths = {finding.path for finding in result.findings if finding.rule == "PLACE-8"}

    assert not {jinja, generated_profile, generated_credentials, link, parameter_link} & paths
    assert any(str(jinja) in note and "jinja" in note for note in result.skipped)


def test_unreadable_nested_directory_is_sanitized_and_does_not_abort(repo, monkeypatch):
    repo.env("c", "e")
    _add_bindings(repo, "c", "e", '  envSpecificResourceProfiles:\n    cloud: accessible\n')
    profile_root = repo.root / "environments/resource_profiles"
    blocked = profile_root / "blocked"
    blocked.mkdir(parents=True)
    accessible = _write(repo, "environments/resource_profiles/accessible.yml", "{}\n")
    real_iterdir = Path.iterdir

    def iterdir_with_failure(path):
        if path == blocked:
            raise PermissionError("TOP_SECRET_FROM_OS")
        return real_iterdir(path)

    monkeypatch.setattr(Path, "iterdir", iterdir_with_failure)

    result = run_check(repo.root)

    assert accessible in {
        finding.path for finding in result.findings if finding.rule == "PLACE-8"
    }
    assert f"{blocked}: cannot enumerate directory; PLACE-8 skipped" in result.skipped
    assert "TOP_SECRET_FROM_OS" not in "\n".join(result.skipped)


def test_internal_symlink_alias_keeps_its_higher_priority_resolution_bucket(repo):
    repo.env("c", "e")
    _add_bindings(repo, "c", "e", "  envSpecificResourceProfiles:\n    cloud: slot\n")
    shared = _write(repo, "environments/resource_profiles/shared.yml", "{}\n")
    alias = repo.root / "environments/c/e/Inventory/rp_override/slot.yml"
    alias.parent.mkdir(parents=True)
    alias.symlink_to(shared)
    fallback = _write(repo, "environments/c/e/Inventory/parameters/slot.yml", "{}\n")

    paths = {finding.path.resolve() for finding in _place8(repo)}

    assert shared.resolve() in paths
    assert fallback.resolve() not in paths


def test_findings_are_sorted_by_path_key_and_line(repo):
    repo.env("c", "e", deploy={"cloud": ["a"]})
    _add_bindings(repo, "c", "e", "  sharedMasterCredentialFiles: [z]\n")
    credential = _write(repo, "environments/credentials/z.yml", "{}\n")
    parameter = _write(repo, "environments/parameters/a.yml", "{}\n")
    findings = _place8(repo)
    assert [finding.path for finding in findings] == [credential, parameter]


@pytest.mark.parametrize("folder", ["parameters", "resource_profiles", "credentials"])
def test_unreferenced_empty_entities_are_ignored(repo, folder):
    repo.env("c", "e")
    _write(repo, f"environments/{folder}/unused.yml", "{}\n")
    assert _place8(repo) == []


def test_inventory_generation_credentials_are_used_without_explicit_binding(repo):
    repo.env("c", "e")
    used = _write(repo, "environments/c/e/Inventory/credentials/inventory_generation_creds.yml", "{}\n")
    _write(repo, "environments/credentials/inventory_generation_creds.yml", "{}\n")
    _write(repo, "environments/c/e/Inventory/credentials/other.yml", "{}\n")
    assert [f.path for f in _place8(repo)] == [used]


def test_nonempty_inventory_generation_credentials_are_not_reported(repo):
    repo.env("c", "e")
    _write(repo, "environments/c/e/Inventory/credentials/inventory_generation_creds.yml", "synthetic: {}\n")
    assert _place8(repo) == []
