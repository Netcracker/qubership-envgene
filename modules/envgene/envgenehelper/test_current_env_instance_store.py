import json

import pytest

from envgenehelper.business_helper import get_bgd_object, get_namespaces
from envgenehelper.current_env_instance_store import (
    CurrentEnvInstanceStore, current_env_instance_store, open_current_env_instance_store,
)
from envgenehelper.yaml_helper import dumpYamlToStr, normalize_comments, readYaml

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
    assert len(objects.list(env_dir / "**" / "*.yml")) == 5
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


def test_raw_flush_writes_to_raw_dir_without_credentials(monkeypatch, tmp_path, env_dir):
    monkeypatch.setenv("SAVE_ARTIFACTS_STRATEGY", "ALWAYS")
    raw_dir = tmp_path / "artifacts" / "render"
    objects = CurrentEnvInstanceStore(env_dir)
    data = readYaml("a: 1  # c\nb: 2\n")
    data.ca.items["b"] = None
    objects.put(env_dir / "cloud.yml", data)
    objects.put(env_dir / "Credentials" / "credentials.yml", {"cred": {"type": "secret"}})
    objects.flush(raw=True, raw_dir=raw_dir)

    assert (raw_dir / "cloud.yml").read_text() == "a: 1 # c\nb: 2\n"
    assert not (raw_dir / "Credentials").exists()
    assert not (env_dir / "cloud.yml").exists()


def test_raw_flush_writes_nothing_when_strategy_is_never(monkeypatch, tmp_path, env_dir):
    monkeypatch.setenv("SAVE_ARTIFACTS_STRATEGY", "NEVER")
    raw_dir = tmp_path / "artifacts" / "render"
    objects = CurrentEnvInstanceStore(env_dir)
    objects.put(env_dir / "cloud.yml", {"a": 1})
    objects.flush(raw=True, raw_dir=raw_dir)

    assert not raw_dir.exists()


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
