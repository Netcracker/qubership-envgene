import hashlib
import importlib
import json

import pytest

from envgenehelper.business_helper import NamespaceRole, get_bgd_object, get_namespaces
from envgenehelper.current_env_instance_store import (
    CurrentEnvInstanceStore, current_env_instance_store,
    open_current_env_instance_store, profile_cache_dir,
)
from envgenehelper.yaml_helper import dumpYamlToStr, normalize_comments, readYaml

STORE_MODULE = importlib.import_module("envgenehelper.current_env_instance_store")

SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "profile": {"type": "object", "properties": {"baseline": {"type": "string"}, "name": {"type": "string"}}},
        "value": {"type": "string"},
    },
}


@pytest.fixture
def env_dir(tmp_path):
    return tmp_path / "environments" / "cluster" / "env"


@pytest.fixture
def schema_path(tmp_path):
    path = tmp_path / "schema.json"
    path.write_text(json.dumps(SCHEMA))
    return path


def test_store_never_reads_disk(tmp_path, env_dir):
    template_profile = tmp_path / "templates" / "resource_profiles" / "profile.yml"
    template_profile.parent.mkdir(parents=True)
    template_profile.write_text("name: a\n")
    objects = CurrentEnvInstanceStore(env_dir)

    assert not objects.exists(template_profile)
    assert objects.find_yaml(template_profile.parent, "profile") is None
    with pytest.raises(FileNotFoundError):
        objects.get(template_profile)


def test_find_yaml_returns_put_object_by_name(tmp_path, env_dir):
    profiles_dir = tmp_path / "templates" / "resource_profiles"
    objects = CurrentEnvInstanceStore(env_dir)
    objects.put(profiles_dir / "nested" / "dev.yaml", {"name": "dev"})
    objects.put(profiles_dir / "prod.yml", {"name": "prod"})
    objects.put(profiles_dir / "prod.txt", {"name": "not yaml"})

    assert objects.find_yaml(profiles_dir, "dev") == (profiles_dir / "nested" / "dev.yaml").resolve()
    assert objects.find_yaml(profiles_dir, "prod") == (profiles_dir / "prod.yml").resolve()
    assert objects.find_yaml(profiles_dir, "missing") is None
    assert objects.find_yaml(env_dir, "prod") is None


def test_paths_are_normalized(env_dir):
    objects = CurrentEnvInstanceStore(env_dir)
    obj = objects.put(f"{env_dir}/Namespaces/../tenant.yml", {"name": "t"})

    assert objects.get(env_dir / "tenant.yml") is obj
    assert objects.exists(str(env_dir / "tenant.yml"))


def test_generated_paths_ignore_disk(env_dir):
    stale = env_dir / "Namespaces" / "old" / "namespace.yml"
    stale.parent.mkdir(parents=True)
    stale.write_text("name: old\n")
    objects = CurrentEnvInstanceStore(env_dir)

    assert not objects.exists(stale)
    with pytest.raises(FileNotFoundError):
        objects.get(stale)


def test_list_matches_glob_rules(env_dir):
    objects = CurrentEnvInstanceStore(env_dir)
    for rel in ("Namespaces/a/namespace.yml", "Namespaces/b/namespace.yml", "Namespaces/a/Applications/x.yml",
                "Applications/c.yml", "cloud.yml"):
        objects.put(env_dir / rel, {})

    assert [p.parent.name for p in objects.list(env_dir / "Namespaces" / "*" / "namespace.yml")] == ["a", "b"]
    assert [p.name for p in objects.list(env_dir / "Namespaces" / "*" / "Applications" / "*.yml")] == ["x.yml"]
    assert [p.name for p in objects.list(env_dir / "Applications" / "*.yml")] == ["c.yml"]
    assert objects.list(env_dir / "namespaces" / "*" / "namespace.yml") == []


def test_flush_writes_only_marked_objects_under_env_dir(tmp_path, env_dir):
    source = tmp_path / "templates" / "profile.yml"
    source.parent.mkdir(parents=True)
    source.write_text("name: p\n")
    inventory = env_dir / "Inventory" / "env_definition.yml"
    objects = CurrentEnvInstanceStore(env_dir)

    objects.put(source, {"name": "changed"})
    objects.put(tmp_path / "templates" / "rendered.yml", {"name": "r"})
    objects.put(inventory, {"name": "inv"})
    objects.put(env_dir / "tenant.yml", {"name": "t"})
    objects.flush()

    assert source.read_text() == "name: p\n"
    assert not (tmp_path / "templates" / "rendered.yml").exists()
    assert not inventory.exists()
    assert (env_dir / "tenant.yml").read_text() == "name: t\n"


def test_flush_sorts_quotes_and_adds_header(env_dir, schema_path):
    objects = CurrentEnvInstanceStore(env_dir)
    target = env_dir / "Namespaces" / "a" / "namespace.yml"
    objects.put(target, readYaml("profile:\n  name: n\n  baseline: b\nname: a\n"))
    objects.beautify(target, schema_path, "first\nsecond")
    objects.beautify(target, schema_path)
    objects.flush()

    assert target.read_text() == '# first\n# second\nname: "a"\nprofile:\n  baseline: "b"\n  name: "n"\n'


def test_flush_normalizes_comment_spacing(env_dir):
    objects = CurrentEnvInstanceStore(env_dir)
    target = env_dir / "cloud.yml"
    data = readYaml("a: 1    # c1\nb:\n  c: 2  # c2\n")
    data.insert(1, "d", "v", "inserted")
    objects.put(target, data)
    objects.flush()

    assert target.read_text() == "a: 1 # c1\nd: v # inserted\nb:\n  c: 2 # c2\n"


def test_flush_removes_comments_from_credentials(env_dir):
    objects = CurrentEnvInstanceStore(env_dir)
    target = env_dir / "Credentials" / "credentials.yml"
    objects.put(target, readYaml("cred:  # c\n  type: secret  # t\n"))
    objects.flush()

    assert target.read_text() == "cred:\n  type: secret\n"


def test_current_store_is_available_only_while_open(env_dir):
    with pytest.raises(RuntimeError):
        current_env_instance_store()

    with open_current_env_instance_store(env_dir) as opened_store:
        assert current_env_instance_store() is opened_store

    with pytest.raises(RuntimeError):
        current_env_instance_store()


def test_current_store_is_closed_after_failure(env_dir):
    with pytest.raises(ValueError):
        with open_current_env_instance_store(env_dir):
            raise ValueError("step failed")

    with pytest.raises(RuntimeError):
        current_env_instance_store()


def test_second_open_store_fails(env_dir):
    with open_current_env_instance_store(env_dir) as opened_store:
        with pytest.raises(RuntimeError):
            with open_current_env_instance_store(env_dir):
                pass

        assert current_env_instance_store() is opened_store


def test_store_namespaces_and_bg_domain_are_the_current_run(env_dir):
    previous_namespace = env_dir / "Namespaces" / "old" / "namespace.yml"
    previous_namespace.parent.mkdir(parents=True)
    previous_namespace.write_text("name: env-old\n")
    (env_dir / "bg_domain.yml").write_text("name: old-domain\noriginNamespace:\n  name: env-old\n")
    objects = CurrentEnvInstanceStore(env_dir)
    objects.put(env_dir / "bg_domain.yml", {"name": "domain", "peerNamespace": {"name": "env-peer"}})
    objects.put(env_dir / "Namespaces" / "app-peer" / "namespace.yml", {"name": "env-peer"})
    objects.put(env_dir / "Namespaces" / "core" / "namespace.yml", {"name": "env-core"})

    namespaces = objects.namespaces()

    assert objects.bg_domain()["name"] == "domain"
    assert [(ns.postfix, ns.name, ns.role) for ns in namespaces] == [
        ("app-peer", "env-peer", "peer"), ("core", "env-core", "common")]
    assert namespaces[0].definition_path == (env_dir / "Namespaces" / "app-peer" / "namespace.yml").resolve()


def test_store_bg_domain_is_empty_when_not_rendered(env_dir):
    env_dir.mkdir(parents=True)
    (env_dir / "bg_domain.yml").write_text("name: old-domain\n")

    assert CurrentEnvInstanceStore(env_dir).bg_domain() == {}


def test_store_namespaces_ignore_bg_domain_of_previous_run(monkeypatch, tmp_path, env_dir):
    env_dir.mkdir(parents=True)
    (env_dir / "bg_domain.yml").write_text("originNamespace:\n  name: env-origin\n")
    monkeypatch.setenv("CI_PROJECT_DIR", str(tmp_path))
    monkeypatch.setenv("FULL_ENV_NAME", "cluster/env")
    objects = CurrentEnvInstanceStore(env_dir)
    objects.put(env_dir / "Namespaces" / "origin" / "namespace.yml", {"name": "env-origin"})

    assert [ns.role for ns in objects.namespaces()] == [NamespaceRole.COMMON]


def test_disk_readers_do_not_see_objects_only_in_store(env_dir):
    previous_namespace = env_dir / "Namespaces" / "old" / "namespace.yml"
    previous_namespace.parent.mkdir(parents=True)
    previous_namespace.write_text("name: env-old\n")
    (env_dir / "bg_domain.yml").write_text("name: old-domain\n")
    with open_current_env_instance_store(env_dir) as opened_store:
        opened_store.put(env_dir / "Namespaces" / "new" / "namespace.yml", {"name": "env-new"})
        opened_store.put(env_dir / "bg_domain.yml", {"name": "domain"})

        assert [ns.name for ns in get_namespaces(env_dir)] == ["env-old"]
        assert get_bgd_object(env_dir)["name"] == "old-domain"
        assert [ns.name for ns in opened_store.namespaces()] == ["env-new"]


@pytest.mark.parametrize("source, expected", [
    ("a: 1    # c\n# block\n  # indented block\nb: 2\n", "a: 1 # c\n# block\n  # indented block\nb: 2\n"),
    ("l:\n  - 1   # one\n  # between\n  - 2  # two\n", "l:\n  - 1 # one\n  # between\n  - 2 # two\n"),
    ("l:\n  - name: z    # c\n    v: 1\n", "l:\n  - name: z # c\n    v: 1\n"),
    ("m:    # c\n  k: v\n", "m: # c\n  k: v\n"),
    ("s:    # c\n  - v\n", "s: # c\n  - v\n"),
    ("l:\n  -   - 1   # nested\n", "l:\n  -   - 1 # nested\n"),
    ("f: [1, 2]   # flow\n", "f: [1, 2] # flow\n"),
    ("a: 1 # already\n", "a: 1 # already\n"),
])
def test_normalize_comments(source, expected):
    data = readYaml(source)
    normalize_comments(data)

    assert dumpYamlToStr(data) == expected


def _profile_path(tmp_path, content):
    profile = tmp_path / "resource_profiles" / "dev_bss_override.yml"
    profile.parent.mkdir(parents=True, exist_ok=True)
    profile.write_bytes(content)
    return profile


@pytest.fixture
def shared_root(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    monkeypatch.setenv("CI_PROJECT_DIR", str(root))
    monkeypatch.setattr(STORE_MODULE, "get_envgene_config_yaml", lambda: {})
    return root


@pytest.mark.parametrize("value, enabled", [
    (True, True), ("true", True), ("True", True), ("TRUE", True),
    (False, False), ("false", False), ("False", False), ("FALSE", False),
])
def test_profile_cache_flag_values(shared_root, monkeypatch, value, enabled):
    monkeypatch.setattr(STORE_MODULE, "get_envgene_config_yaml", lambda: {"cache": {"enabled": value}})

    assert (profile_cache_dir() is not None) == enabled


@pytest.mark.parametrize("value", [False, "false", "FALSE"])
def test_profile_cache_disabled_by_config(tmp_path, env_dir, shared_root, monkeypatch, value):
    monkeypatch.setattr(STORE_MODULE, "get_envgene_config_yaml", lambda: {"cache": {"enabled": value}})
    profile = _profile_path(tmp_path, b"name: dev\n")
    store = CurrentEnvInstanceStore(env_dir)

    assert store.load_profile_from_cache(profile)["name"] == "dev"
    assert profile_cache_dir() is None
    assert not (shared_root / ".shared").exists()


def test_profile_cache_miss_parses_and_hit_reads_pickle(tmp_path, env_dir, shared_root):
    profile = _profile_path(tmp_path, b"name: dev_bss_override\nbaseline: dev\n")
    store = CurrentEnvInstanceStore(env_dir)
    first = store.load_profile_from_cache(profile)

    assert profile_cache_dir() == shared_root / ".shared" / "profile-cache"
    cache_file = profile_cache_dir() / (hashlib.sha256(b"name: dev_bss_override\nbaseline: dev\n").hexdigest() + ".pkl")
    assert first["name"] == "dev_bss_override"
    assert cache_file.is_file()
    assert not (env_dir / ".envgene").exists()

    cached_bytes = cache_file.read_bytes()
    repeated_store = CurrentEnvInstanceStore(env_dir)
    second = repeated_store.load_profile_from_cache(profile)

    assert second == first
    assert cache_file.read_bytes() == cached_bytes


def test_profile_cache_disabled_without_ci_project_dir(tmp_path, env_dir, monkeypatch):
    monkeypatch.delenv("CI_PROJECT_DIR", raising=False)
    profile = _profile_path(tmp_path, b"name: dev\n")
    store = CurrentEnvInstanceStore(env_dir)

    assert store.load_profile_from_cache(profile)["name"] == "dev"
    assert profile_cache_dir() is None
    assert not (env_dir / ".envgene").exists()


def test_profile_cache_content_change_misses(tmp_path, env_dir, shared_root):
    profile = _profile_path(tmp_path, b"name: dev\nbaseline: old\n")
    store = CurrentEnvInstanceStore(env_dir)
    assert store.load_profile_from_cache(profile)["baseline"] == "old"
    profile.write_bytes(b"name: dev\nbaseline: new\n")

    changed = store.load_profile_from_cache(profile)

    assert changed["baseline"] == "new"
    cache_files = list(profile_cache_dir().glob("*.pkl"))
    assert len(cache_files) == 2


def test_profile_cache_corrupt_pickle_falls_back_to_parse(tmp_path, env_dir, shared_root):
    profile = _profile_path(tmp_path, b"name: dev\n")
    store = CurrentEnvInstanceStore(env_dir)
    store.load_profile_from_cache(profile)
    cache_file = profile_cache_dir() / (hashlib.sha256(b"name: dev\n").hexdigest() + ".pkl")
    cache_file.write_bytes(b"not a pickle")

    assert store.load_profile_from_cache(profile)["name"] == "dev"


def test_flush_never_prunes_shared_profile_cache(tmp_path, env_dir, shared_root):
    old_key = hashlib.sha256(b"name: dev\nbaseline: old\n").hexdigest() + ".pkl"
    new_key = hashlib.sha256(b"name: dev\nbaseline: new\n").hexdigest() + ".pkl"
    profile = _profile_path(tmp_path, b"name: dev\nbaseline: old\n")
    store = CurrentEnvInstanceStore(env_dir)
    store.load_profile_from_cache(profile)
    profile.write_bytes(b"name: dev\nbaseline: new\n")
    store.load_profile_from_cache(profile)

    store.flush()
    assert sorted(f.name for f in profile_cache_dir().glob("*.pkl")) == sorted([old_key, new_key])

    next_run = CurrentEnvInstanceStore(env_dir)
    next_run.load_profile_from_cache(profile)
    next_run.flush()

    assert sorted(f.name for f in profile_cache_dir().glob("*.pkl")) == sorted([old_key, new_key])
