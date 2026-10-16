import json
import sys
from pathlib import Path

import pytest

from envgene_shared.utils import yaml_utils
from envgene_shared.utils.yaml_utils import validate_yaml_by_scheme_or_fail
import envgenehelper.current_env_instance_store  # noqa: F401
store_module = sys.modules["envgenehelper.current_env_instance_store"]
from envgenehelper.business_helper import NamespaceRole, get_bgd_object, get_namespaces
from envgenehelper.current_env_instance_store import (
    CurrentEnvInstanceStore, current_env_instance_store, open_current_env_instance_store,
)
from envgenehelper.object_hash_manifest import load_manifest, manifest_path
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
    assert "appdefs/BGOperator-CRDS.yml" not in load_manifest(env_dir)["objects"]


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


def test_flush_does_not_rewrite_unchanged_object(env_dir, schema_path, monkeypatch):
    target = env_dir / "Namespaces" / "a" / "namespace.yml"

    objects = CurrentEnvInstanceStore(env_dir)
    objects.put(target, readYaml("name: a\n"))
    objects.beautify(target, schema_path)
    objects.flush()

    calls = []
    monkeypatch.setattr(store_module, "writeToFile", lambda path, text: calls.append(Path(path)))
    objects2 = CurrentEnvInstanceStore(env_dir)
    objects2.put(target, readYaml("name: a\n"))
    objects2.beautify(target, schema_path)
    objects2.flush()

    assert Path(target) not in calls


def test_flush_rewrites_object_when_data_changes(env_dir, schema_path):
    objects = CurrentEnvInstanceStore(env_dir)
    target = env_dir / "Namespaces" / "a" / "namespace.yml"
    objects.put(target, readYaml("name: a\n"))
    objects.beautify(target, schema_path)
    objects.flush()

    objects2 = CurrentEnvInstanceStore(env_dir)
    objects2.put(target, readYaml("name: changed\n"))
    objects2.beautify(target, schema_path)
    objects2.flush()

    assert 'name: "changed"' in target.read_text()


def test_flush_stale_manifest_triggers_rewrite(env_dir, schema_path, monkeypatch):
    target = env_dir / "tenant.yml"

    objects = CurrentEnvInstanceStore(env_dir)
    objects.put(target, readYaml("name: a\n"))
    objects.beautify(target, schema_path)
    objects.flush()
    manifest_path(env_dir).write_text(json.dumps({"objects": {}}))

    calls = []
    monkeypatch.setattr(store_module, "writeToFile", lambda path, text: calls.append(Path(path)))
    objects3 = CurrentEnvInstanceStore(env_dir)
    objects3.put(target, readYaml("name: a\n"))
    objects3.beautify(target, schema_path)
    objects3.flush()

    assert Path(target) in calls


def test_flush_deletes_stale_namespace_dir(env_dir):
    stale = env_dir / "Namespaces" / "gone" / "namespace.yml"
    stale.parent.mkdir(parents=True)
    stale.write_text("name: gone\n")

    objects = CurrentEnvInstanceStore(env_dir)
    objects.put(env_dir / "Namespaces" / "keep" / "namespace.yml", readYaml("name: keep\n"))
    objects.flush()

    assert not stale.exists()
    assert (env_dir / "Namespaces" / "keep" / "namespace.yml").read_text() == "name: keep\n"


def test_flush_deletes_stale_generated_file(env_dir):
    env_dir.mkdir(parents=True, exist_ok=True)
    (env_dir / "bg_domain.yml").write_text("name: old\n")

    objects = CurrentEnvInstanceStore(env_dir)
    # a live env object keeps the stale sweep active; bg_domain.yml is then pruned
    objects.put(env_dir / "tenant.yml", {"name": "t"})
    objects.flush()

    assert not (env_dir / "bg_domain.yml").exists()


def test_flush_writes_base_dir_object(tmp_path, env_dir):
    # base_dir (the repo root) is a separate write scope; a root AppDefs copy lives
    # outside env_dir and must still be written to disk.
    objects = CurrentEnvInstanceStore(env_dir, base_dir=tmp_path)
    root_appdef = tmp_path / "appdefs" / "demo.yml"
    objects.put(root_appdef, {"name": "demo"})
    objects.flush()

    assert root_appdef.read_text() == "name: demo\n"
    manifest = readYaml(manifest_path(env_dir).read_text())
    assert manifest["objects"]["appdefs/demo.yml"]


def test_flush_does_not_rewrite_unchanged_base_dir_object(env_dir, tmp_path, monkeypatch):
    root_appdef = tmp_path / "appdefs" / "demo.yml"
    objects = CurrentEnvInstanceStore(env_dir, base_dir=tmp_path)
    objects.put(root_appdef, {"name": "demo"})
    objects.flush()

    calls = []
    monkeypatch.setattr(store_module, "writeToFile", lambda path, text: calls.append(Path(path)))
    objects2 = CurrentEnvInstanceStore(env_dir, base_dir=tmp_path)
    objects2.put(root_appdef, {"name": "demo"})
    objects2.flush()

    assert root_appdef not in calls


def test_flush_rewrites_base_dir_object_changed_by_another_env(tmp_path):
    root_appdef = tmp_path / "appdefs" / "app.yml"
    for env_name, owner in (("a", "A"), ("b", "B"), ("a", "A")):
        objects = CurrentEnvInstanceStore(tmp_path / "environments" / "c" / env_name, base_dir=tmp_path)
        objects.put(root_appdef, {"name": "app", "owner": owner})
        objects.flush()

    assert root_appdef.read_text() == "name: app\nowner: A\n"


def test_flush_does_not_prune_root_appdef(tmp_path, env_dir):
    # Root appdefs are merged into and never cleaned (docs/features/app-reg-defs.md): a root file
    # not written this run belongs to another environment/template set and must survive flush.
    (tmp_path / "appdefs").mkdir(parents=True)
    (tmp_path / "appdefs" / "stale.yml").write_text("name: stale\n")
    (tmp_path / "appdefs" / "keep.yml").write_text("name: keep\n")

    objects = CurrentEnvInstanceStore(env_dir, base_dir=tmp_path)
    objects.put(tmp_path / "appdefs" / "keep.yml", {"name": "keep"})
    objects.flush()

    assert (tmp_path / "appdefs" / "keep.yml").exists()
    assert (tmp_path / "appdefs" / "stale.yml").exists()


def test_flush_prunes_stale_env_appdef_copy(env_dir, tmp_path):
    # dual placement: env AppDefs is reset to exactly the rendered set
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
    # appregdef skipped: store holds no app/reg defs, the dir must be left untouched
    (tmp_path / "appdefs").mkdir(parents=True)
    (tmp_path / "appdefs" / "user.yml").write_text("name: user\n")

    objects = CurrentEnvInstanceStore(env_dir, base_dir=tmp_path)
    objects.put(env_dir / "tenant.yml", {"name": "t"})
    objects.flush()

    assert (tmp_path / "appdefs" / "user.yml").exists()


def test_flush_skips_stale_sweep_when_store_has_only_base_dir_objects(env_dir, tmp_path):
    # BGD-warmup: app/reg defs are rendered (root objects) but env_build does not run,
    # so the store holds only base_dir objects. The sweep must not wipe env generated
    # objects that are not in the store.
    env_dir.mkdir(parents=True, exist_ok=True)
    (env_dir / "bg_domain.yml").write_text("name: old\n")
    (env_dir / "Namespaces" / "old" / "namespace.yml").parent.mkdir(parents=True)
    (env_dir / "Namespaces" / "old" / "namespace.yml").write_text("name: old\n")

    objects = CurrentEnvInstanceStore(env_dir, base_dir=tmp_path)
    objects.put(tmp_path / "appdefs" / "demo.yml", {"name": "demo"})
    objects.flush()

    assert (tmp_path / "appdefs" / "demo.yml").read_text() == "name: demo\n"
    assert (env_dir / "bg_domain.yml").exists()
    assert (env_dir / "Namespaces" / "old" / "namespace.yml").exists()


def test_root_only_flush_keeps_manifest_entries_of_env_objects(env_dir, tmp_path, monkeypatch):
    tenant = env_dir / "tenant.yml"
    objects = CurrentEnvInstanceStore(env_dir, base_dir=tmp_path)
    objects.put(tenant, {"name": "t"})
    objects.flush()

    root_only = CurrentEnvInstanceStore(env_dir, base_dir=tmp_path)
    root_only.put(tmp_path / "appdefs" / "demo.yml", {"name": "demo"})
    root_only.flush()

    calls = []
    monkeypatch.setattr(store_module, "writeToFile", lambda path, text: calls.append(Path(path)))
    objects2 = CurrentEnvInstanceStore(env_dir, base_dir=tmp_path)
    objects2.put(tenant, {"name": "t"})
    objects2.flush()

    assert tenant not in calls


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


def test_flush_rewrites_unchanged_object_missing_on_disk(env_dir, tmp_path):
    root_appdef = tmp_path / "appdefs" / "demo.yml"
    objects = CurrentEnvInstanceStore(env_dir, base_dir=tmp_path)
    objects.put(root_appdef, {"name": "demo"})
    objects.flush()
    root_appdef.unlink()

    objects2 = CurrentEnvInstanceStore(env_dir, base_dir=tmp_path)
    objects2.put(root_appdef, {"name": "demo"})
    objects2.flush()

    assert root_appdef.exists()


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


def test_flush_saves_validations_passed_this_run(env_dir, schema_path):
    with open_current_env_instance_store(env_dir) as objects:
        validate_yaml_by_scheme_or_fail(input_yaml_content={"name": "t"}, schema_file_path=schema_path)
        objects.put(env_dir / "tenant.yml", {"name": "t"})
        objects.flush()

    assert json.loads(manifest_path(env_dir).read_text())["validated"] == sorted(objects.validated.seen)


def test_next_run_skips_validation_saved_in_manifest(env_dir, schema_path, monkeypatch):
    with open_current_env_instance_store(env_dir) as objects:
        validate_yaml_by_scheme_or_fail(input_yaml_content={"name": "t"}, schema_file_path=schema_path)
        objects.put(env_dir / "tenant.yml", {"name": "t"})
        objects.flush()
    monkeypatch.setattr(yaml_utils, "get_schema_validator", lambda _: pytest.fail("validation must be skipped"))

    with open_current_env_instance_store(env_dir):
        validate_yaml_by_scheme_or_fail(input_yaml_content={"name": "t"}, schema_file_path=schema_path)


def test_flush_drops_validations_not_used_this_run(env_dir, schema_path):
    with open_current_env_instance_store(env_dir) as objects:
        validate_yaml_by_scheme_or_fail(input_yaml_content={"name": "old"}, schema_file_path=schema_path)
        objects.put(env_dir / "tenant.yml", {"name": "old"})
        objects.flush()

    with open_current_env_instance_store(env_dir) as objects:
        validate_yaml_by_scheme_or_fail(input_yaml_content={"name": "new"}, schema_file_path=schema_path)
        objects.put(env_dir / "tenant.yml", {"name": "new"})
        objects.flush()

    assert json.loads(manifest_path(env_dir).read_text())["validated"] == sorted(objects.validated.seen)


def test_root_only_flush_keeps_validations_of_env_objects(env_dir, tmp_path, schema_path):
    with open_current_env_instance_store(env_dir, base_dir=tmp_path) as objects:
        validate_yaml_by_scheme_or_fail(input_yaml_content={"name": "t"}, schema_file_path=schema_path)
        objects.put(env_dir / "tenant.yml", {"name": "t"})
        objects.flush()
    env_validations = objects.validated.seen

    with open_current_env_instance_store(env_dir, base_dir=tmp_path) as root_only:
        root_only.put(tmp_path / "appdefs" / "demo.yml", {"name": "demo"})
        root_only.flush()

    assert set(json.loads(manifest_path(env_dir).read_text())["validated"]) == env_validations
