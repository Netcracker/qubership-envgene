import json

import pytest

from envgenehelper.business_helper import NamespaceRole, get_bgd_object, get_namespaces
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


def test_root_appdef_miss_loads_from_disk_readonly(tmp_path, env_dir):
    appdefs = tmp_path / "appdefs"
    appdefs.mkdir()
    committed = appdefs / "BGOperator-CRDS.yml"
    committed.write_text("name: BGOperator-CRDS\nregistryName: old-registry\n")
    objects = CurrentEnvInstanceStore(env_dir, base_dir=tmp_path)

    assert objects.get_yaml(appdefs, "BGOperator-CRDS") == {"name": "BGOperator-CRDS",
                                                            "registryName": "old-registry"}

    objects.flush()

    assert committed.read_text() == "name: BGOperator-CRDS\nregistryName: old-registry\n"


def test_put_object_wins_over_disk_root_appdef(tmp_path, env_dir):
    appdefs = tmp_path / "appdefs"
    appdefs.mkdir()
    committed = appdefs / "app.yml"
    committed.write_text("name: from-disk\n")
    objects = CurrentEnvInstanceStore(env_dir, base_dir=tmp_path)
    objects.put(appdefs / "app.yml", {"name": "rendered"})

    assert objects.get_yaml(appdefs, "app") == {"name": "rendered"}


def test_missing_root_appdef_still_raises(tmp_path, env_dir):
    (tmp_path / "appdefs").mkdir()
    objects = CurrentEnvInstanceStore(env_dir, base_dir=tmp_path)

    with pytest.raises(FileNotFoundError):
        objects.get_yaml(tmp_path / "appdefs", "absent")


def test_env_scoped_store_does_not_read_disk(tmp_path, env_dir):
    (tmp_path / "appdefs").mkdir()
    (tmp_path / "appdefs" / "app.yml").write_text("name: a\n")
    objects = CurrentEnvInstanceStore(env_dir)

    with pytest.raises(FileNotFoundError):
        objects.get_yaml(tmp_path / "appdefs", "app")


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


def test_flush_writes_base_dir_object(tmp_path, env_dir):
    objects = CurrentEnvInstanceStore(env_dir, base_dir=tmp_path)
    root_appdef = tmp_path / "appdefs" / "demo.yml"
    objects.put(root_appdef, {"name": "demo"})
    objects.flush()

    assert root_appdef.read_text() == "name: demo\n"


def test_flush_does_not_prune_root_appdef(tmp_path, env_dir):
    (tmp_path / "appdefs").mkdir(parents=True)
    (tmp_path / "appdefs" / "stale.yml").write_text("name: stale\n")
    (tmp_path / "appdefs" / "keep.yml").write_text("name: keep\n")

    objects = CurrentEnvInstanceStore(env_dir, base_dir=tmp_path)
    objects.put(tmp_path / "appdefs" / "keep.yml", {"name": "keep"})
    objects.flush()

    assert (tmp_path / "appdefs" / "keep.yml").exists()
    assert (tmp_path / "appdefs" / "stale.yml").exists()


def test_flush_prunes_stale_env_appdef_copy(env_dir, tmp_path):
    (env_dir / "AppDefs").mkdir(parents=True)
    (env_dir / "AppDefs" / "stale.yml").write_text("name: stale\n")

    objects = CurrentEnvInstanceStore(env_dir, base_dir=tmp_path)
    objects.replace_dir(env_dir / "AppDefs")
    objects.put(tmp_path / "appdefs" / "demo.yml", {"name": "demo"})
    objects.put(env_dir / "AppDefs" / "demo.yml", {"name": "demo"})
    objects.flush()

    assert (env_dir / "AppDefs" / "demo.yml").exists()
    assert not (env_dir / "AppDefs" / "stale.yml").exists()


def test_flush_does_not_prune_appdef_dir_when_not_rendered(env_dir, tmp_path):
    (tmp_path / "appdefs").mkdir(parents=True)
    (tmp_path / "appdefs" / "user.yml").write_text("name: user\n")

    objects = CurrentEnvInstanceStore(env_dir, base_dir=tmp_path)
    objects.put(env_dir / "tenant.yml", {"name": "t"})
    objects.flush()

    assert (tmp_path / "appdefs" / "user.yml").exists()


def test_root_only_app_defs_remove_env_copies(env_dir, tmp_path):
    (env_dir / "AppDefs").mkdir(parents=True)
    (env_dir / "AppDefs" / "stale.yml").write_text("name: stale\n")

    objects = CurrentEnvInstanceStore(env_dir, base_dir=tmp_path)
    objects.replace_dir(env_dir / "AppDefs")
    objects.put(tmp_path / "appdefs" / "demo.yml", {"name": "demo"})
    objects.flush()

    assert not (env_dir / "AppDefs").exists()


def test_flush_keeps_env_appdefs_when_not_replaced(env_dir, tmp_path):
    (env_dir / "AppDefs").mkdir(parents=True)
    (env_dir / "AppDefs" / "old.yml").write_text("name: old\n")

    objects = CurrentEnvInstanceStore(env_dir, base_dir=tmp_path)
    objects.put(tmp_path / "appdefs" / "demo.yml", {"name": "demo"})
    objects.flush()

    assert (env_dir / "AppDefs" / "old.yml").exists()


def test_flush_does_not_write_base_dir_object_outside_app_reg_defs(env_dir, tmp_path):
    template_profile = tmp_path / "tmp" / "templates" / "resource_profiles" / "dev.yml"
    objects = CurrentEnvInstanceStore(env_dir, base_dir=tmp_path)
    objects.put(template_profile, {"name": "dev"})
    objects.flush()

    assert not template_profile.exists()


def test_get_yaml_finds_any_yaml_extension(env_dir, tmp_path):
    objects = CurrentEnvInstanceStore(env_dir, base_dir=tmp_path)
    objects.put(tmp_path / "appdefs" / "demo.yaml", {"name": "demo"})

    assert objects.get_yaml(tmp_path / "appdefs", "demo") == {"name": "demo"}
    with pytest.raises(FileNotFoundError):
        objects.get_yaml(tmp_path / "appdefs", "absent")


def test_flush_rewrites_base_dir_object_changed_by_another_env(tmp_path):
    root_appdef = tmp_path / "appdefs" / "app.yml"
    for env_name, owner in (("a", "A"), ("b", "B"), ("a", "A")):
        objects = CurrentEnvInstanceStore(tmp_path / "environments" / "c" / env_name, base_dir=tmp_path)
        objects.put(root_appdef, {"name": "app", "owner": owner})
        objects.flush()

    assert root_appdef.read_text() == "name: app\nowner: A\n"
