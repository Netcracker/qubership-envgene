"""Tests for template_scanner: discover cred-ids + infer types from consumer templates."""

from pathlib import Path

import yaml

from cred_migration.template_scanner import (
    build_paramset_index,
    collect_cred_usages_from_text,
    infer_cred_type_from_usages,
    list_descriptors,
    parse_descriptor,
    scan_descriptor_creds,
    scan_parameters_creds,
    scan_solution_consumer_creds,
    list_env_template_solutions,
)


def _make(tmp_path, relpath, content=""):
    p = tmp_path / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return p


# ---- Text-level extraction ----

def test_collect_cred_usages_extracts_value_macros():
    text = """
    DB_USER: "${creds.get('app-db').username}"
    DB_PASS: "${creds.get('app-db').password}"
    TOKEN: "${creds.get('token-cred').secret}"
    """
    usages = collect_cred_usages_from_text(text)
    assert usages == {
        "app-db": {"username", "password"},
        "token-cred": {"secret"},
    }


def test_collect_cred_usages_recognizes_envgen_and_cmdb_aliases():
    text = """
    A: "${envgen.creds.get('cred-a').username}"
    B: "${cmdb.creds.get('cred-b').secret}"
    """
    usages = collect_cred_usages_from_text(text)
    assert usages == {"cred-a": {"username"}, "cred-b": {"secret"}}


def test_collect_cred_usages_recognizes_hash_macros_as_username_password_pair():
    text = "'#creds{LOGIN, PASS}': 'app-cred'"
    usages = collect_cred_usages_from_text(text)
    assert usages == {"app-cred": {"username", "password"}}


def test_collect_cred_usages_recognizes_builtin_credentials_id():
    text = "credentialsId: my-cred"
    usages = collect_cred_usages_from_text(text)
    # Built-in field ref → single-value shape (no property).
    assert usages == {"my-cred": {"__builtin__"}}


def test_collect_cred_usages_returns_empty_for_text_without_macros():
    assert collect_cred_usages_from_text("plain: text\nother: value") == {}


# ---- Type inference ----

def test_infer_cred_type_username_and_password_means_multi_field():
    assert infer_cred_type_from_usages({"username", "password"}) == "usernamePassword"


def test_infer_cred_type_secret_only_means_single_value():
    assert infer_cred_type_from_usages({"secret"}) == "secret"


def test_infer_cred_type_builtin_ref_only_means_single_value():
    assert infer_cred_type_from_usages({"__builtin__"}) == "secret"


def test_infer_cred_type_username_only_still_multi_field():
    """One field of a pair still implies usernamePassword (partial usage)."""
    assert infer_cred_type_from_usages({"username"}) == "usernamePassword"


def test_infer_cred_type_mixed_fields_and_builtin_prefers_multi_field():
    assert infer_cred_type_from_usages({"username", "password", "__builtin__"}) == "usernamePassword"


# ---- Solution discovery ----

def test_list_env_template_solutions_returns_solution_dirs(tmp_path):
    _make(tmp_path, "templates/env_templates/bss/cloud.yml.j2")
    _make(tmp_path, "templates/env_templates/oss/tenant.yml.j2")
    solutions = list_env_template_solutions(tmp_path)
    names = {s.name for s in solutions}
    assert names == {"bss", "oss"}


# ---- Per-solution scan ----

def test_scan_solution_consumer_creds_walks_all_consumer_templates(tmp_path):
    solution_dir = tmp_path / "templates" / "env_templates" / "bss"
    _make(tmp_path, "templates/env_templates/bss/cloud.yml.j2",
          "deployParameters:\n  A: \"${creds.get('c1').username}\"")
    _make(tmp_path, "templates/env_templates/bss/namespace.yml.j2",
          "deployParameters:\n  B: \"${creds.get('c1').password}\"")
    _make(tmp_path, "templates/env_templates/bss/tenant.yml.j2",
          "deployParameters:\n  T: \"${creds.get('c2').secret}\"")
    _make(tmp_path, "templates/env_templates/bss/namespace-alt.yml.j2",
          "credentialsId: c3")

    creds = scan_solution_consumer_creds(solution_dir)
    assert creds == {
        "c1": "usernamePassword",
        "c2": "secret",
        "c3": "secret",  # built-in cred field → single-value
    }


def test_scan_solution_consumer_creds_returns_empty_for_solution_without_macros(tmp_path):
    solution_dir = tmp_path / "templates" / "env_templates" / "empty"
    _make(tmp_path, "templates/env_templates/empty/cloud.yml.j2", "name: x")
    assert scan_solution_consumer_creds(solution_dir) == {}


# ---- scan_parameters_creds (shared ParameterSets under templates/parameters/) ----

def test_scan_parameters_creds_walks_all_yaml_extensions(tmp_path):
    """ParameterSet files use .yml, .yaml, and .yml.j2 - all must be scanned."""
    _make(tmp_path, "templates/parameters/area1/set-a.yml",
          'params:\n  U: "${creds.get(\'shared-cred-a\').username}"')
    _make(tmp_path, "templates/parameters/area2/set-b.yaml",
          'params:\n  T: "${creds.get(\'shared-cred-b\').secret}"')
    _make(tmp_path, "templates/parameters/area3/set-c.yml.j2",
          'params:\n  P: "${creds.get(\'shared-cred-c\').password}"')
    creds = scan_parameters_creds(tmp_path)
    assert creds == {
        "shared-cred-a": "usernamePassword",
        "shared-cred-b": "secret",
        "shared-cred-c": "usernamePassword",
    }


def test_scan_parameters_creds_recursive_into_nested_subdirs(tmp_path):
    _make(tmp_path, "templates/parameters/area/nested/deep/file.yml",
          '"${creds.get(\'deep-cred\').secret}"')
    assert scan_parameters_creds(tmp_path) == {"deep-cred": "secret"}


def test_scan_parameters_creds_empty_when_no_parameters_dir(tmp_path):
    assert scan_parameters_creds(tmp_path) == {}


# ---- solution scan also recognises .yml and .yaml (not only .yml.j2) ----

def test_scan_solution_consumer_creds_recognises_plain_yaml_extensions(tmp_path):
    solution_dir = tmp_path / "templates" / "env_templates" / "bss"
    _make(tmp_path, "templates/env_templates/bss/cloud.yml",
          '"${creds.get(\'plain-yml-cred\').secret}"')
    _make(tmp_path, "templates/env_templates/bss/tenant.yaml",
          '"${creds.get(\'plain-yaml-cred\').username}"')
    creds = scan_solution_consumer_creds(solution_dir)
    assert creds == {
        "plain-yml-cred": "secret",
        "plain-yaml-cred": "usernamePassword",
    }


# ---- list_descriptors: enumerate Template Descriptor files ----

def test_list_descriptors_returns_yaml_files_in_env_templates_dir(tmp_path):
    _make(tmp_path, "templates/env_templates/dev.yaml", "tenant: x")
    _make(tmp_path, "templates/env_templates/sit.yml", "tenant: y")
    _make(tmp_path, "templates/env_templates/dev/cloud.yml.j2", "not a descriptor")
    _make(tmp_path, "templates/env_templates/dev/tenant.yml.j2", "not a descriptor")
    descriptors = list_descriptors(tmp_path)
    names = {d.name for d in descriptors}
    assert names == {"dev.yaml", "sit.yml"}


# ---- parse_descriptor: extract template refs ----

def test_parse_descriptor_resolves_all_template_paths(tmp_path):
    _make(tmp_path, "templates/env_templates/dev.yaml", yaml.safe_dump({
        "tenant": "{{ templates_dir }}/env_templates/dev/tenant.yml.j2",
        "cloud": "{{ templates_dir }}/env_templates/dev/cloud.yml.j2",
        "namespaces": [
            {"name": "core", "template_path": "{{ templates_dir }}/env_templates/dev/ns/core.yml.j2"},
            {"name": "bss", "template_path": "{{ templates_dir }}/env_templates/dev/ns/bss.yml.j2"},
        ],
        "composite_structure": "{{ templates_dir }}/env_templates/dev/composite.yml.j2",
    }))
    refs = parse_descriptor(tmp_path / "templates/env_templates/dev.yaml", tmp_path)
    # Paths returned as Path objects relative to repo root, `{{ templates_dir }}` stripped.
    rel_strs = {str(p.relative_to(tmp_path)) for p in refs}
    assert rel_strs == {
        "templates/env_templates/dev/tenant.yml.j2",
        "templates/env_templates/dev/cloud.yml.j2",
        "templates/env_templates/dev/ns/core.yml.j2",
        "templates/env_templates/dev/ns/bss.yml.j2",
        "templates/env_templates/dev/composite.yml.j2",
    }


def test_parse_descriptor_ignores_missing_optional_fields(tmp_path):
    _make(tmp_path, "templates/env_templates/minimal.yaml", yaml.safe_dump({
        "tenant": "{{ templates_dir }}/tenant.yml.j2",
    }))
    refs = parse_descriptor(tmp_path / "templates/env_templates/minimal.yaml", tmp_path)
    assert len(refs) == 1


# ---- build_paramset_index: name → file map ----

def test_build_paramset_index_indexes_files_by_inner_name_field(tmp_path):
    _make(tmp_path, "templates/parameters/area1/set-a.yml",
          yaml.safe_dump({"name": "paramset-alpha", "parameters": {}}))
    _make(tmp_path, "templates/parameters/area2/set-b.yaml",
          yaml.safe_dump({"name": "paramset-beta", "parameters": {}}))
    _make(tmp_path, "templates/parameters/area3/set-c.yml.j2",
          yaml.safe_dump({"name": "paramset-gamma"}))
    index = build_paramset_index(tmp_path)
    assert set(index.keys()) == {"paramset-alpha", "paramset-beta", "paramset-gamma"}
    assert str(index["paramset-alpha"].relative_to(tmp_path)) == (
        "templates/parameters/area1/set-a.yml"
    )


def test_build_paramset_index_empty_when_no_parameters_dir(tmp_path):
    assert build_paramset_index(tmp_path) == {}


# ---- scan_descriptor_creds: transitive scan per descriptor ----

def test_scan_descriptor_creds_transitively_follows_paramset_refs(tmp_path):
    # Descriptor references a cloud template.
    _make(tmp_path, "templates/env_templates/dev.yaml", yaml.safe_dump({
        "tenant": "{{ templates_dir }}/env_templates/dev/tenant.yml.j2",
        "cloud": "{{ templates_dir }}/env_templates/dev/cloud.yml.j2",
    }))
    # Cloud template uses one direct macro + references two ParameterSets.
    _make(tmp_path, "templates/env_templates/dev/cloud.yml.j2", yaml.safe_dump({
        "deployParameters": {
            "DIRECT": "${creds.get('direct-cred').secret}"
        },
        "deployParameterSets": ["paramset-alpha"],
        "e2eParameterSets": ["paramset-beta"],
        "technicalConfigurationParameterSets": ["paramset-tech"],  # MUST be skipped
    }))
    _make(tmp_path, "templates/env_templates/dev/tenant.yml.j2", "name: dev-tenant")
    # ParameterSet with cred macro.
    _make(tmp_path, "templates/parameters/area/alpha.yml", yaml.safe_dump({
        "name": "paramset-alpha",
        "parameters": {"A": "${creds.get('alpha-cred').username}",
                       "B": "${creds.get('alpha-cred').password}"}
    }))
    _make(tmp_path, "templates/parameters/area/beta.yml", yaml.safe_dump({
        "name": "paramset-beta",
        "parameters": {"T": "${creds.get('beta-cred').secret}"}
    }))
    # tech paramset with cred that must NOT appear (skipped via technicalConfigurationParameterSets).
    _make(tmp_path, "templates/parameters/area/tech.yml", yaml.safe_dump({
        "name": "paramset-tech",
        "parameters": {"TECH": "${creds.get('tech-cred').secret}"}
    }))

    creds = scan_descriptor_creds(
        descriptor_path=tmp_path / "templates/env_templates/dev.yaml",
        repo_root=tmp_path,
    )
    # Direct cloud macro + two paramset macros. tech-cred MUST NOT appear.
    assert creds == {
        "direct-cred": "secret",
        "alpha-cred": "usernamePassword",
        "beta-cred": "secret",
    }


def test_scan_descriptor_creds_returns_empty_when_no_macros(tmp_path):
    _make(tmp_path, "templates/env_templates/empty.yaml", yaml.safe_dump({
        "tenant": "{{ templates_dir }}/env_templates/empty/tenant.yml.j2",
    }))
    _make(tmp_path, "templates/env_templates/empty/tenant.yml.j2", "name: x")
    assert scan_descriptor_creds(
        descriptor_path=tmp_path / "templates/env_templates/empty.yaml",
        repo_root=tmp_path,
    ) == {}
