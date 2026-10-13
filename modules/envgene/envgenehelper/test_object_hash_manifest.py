import json

from ruyaml import CommentedMap, CommentedSeq

from envgenehelper.current_env_instance_store import CurrentEnvInstanceStore
from envgenehelper.object_hash_manifest import (
    canonical_hash, manifest_bytes, load_manifest, manifest_path, save_manifest, schema_file_hash,
    sync_manifest_with_disk,
)


def test_canonical_hash_ignores_key_order():
    assert canonical_hash({"a": 1, "b": [1, 2]}) == canonical_hash({"b": [1, 2], "a": 1})


def test_canonical_hash_is_sensitive_to_list_order():
    assert canonical_hash({"a": [1, 2]}) != canonical_hash({"a": [2, 1]})


def test_canonical_hash_is_sensitive_to_values():
    assert canonical_hash({"a": 1}) != canonical_hash({"a": 2})


def test_canonical_hash_is_stable_across_container_types():
    data = CommentedMap({"name": "env", "replicas": 3})
    data.ca.comment = "generated"
    assert canonical_hash(data) == canonical_hash({"name": "env", "replicas": 3})


def test_canonical_hash_salt_changes_result():
    assert canonical_hash({"a": 1}, salt="s1") != canonical_hash({"a": 1}, salt="s2")
    assert canonical_hash({"a": 1}, salt="s1") != canonical_hash({"a": 2}, salt="s1")


def test_canonical_hash_flattens_nested_commented_structures():
    inner = CommentedSeq(["x", "y"])
    inner.ca.comment = "list"
    data = CommentedMap({"items": inner, "count": 2})
    assert canonical_hash(data) == canonical_hash({"items": ["x", "y"], "count": 2})


def test_schema_file_hash_is_stable_and_content_bound(tmp_path):
    same_a = tmp_path / "same_a.json"
    same_b = tmp_path / "same_b.json"
    diff = tmp_path / "diff.json"
    same_a.write_text('{"x": 1}')
    same_b.write_text('{"x": 1}')
    diff.write_text('{"x": 2}')
    assert schema_file_hash(same_a) == schema_file_hash(same_b)
    assert schema_file_hash(same_a) != schema_file_hash(diff)


def test_manifest_round_trip(tmp_path):
    env_dir = tmp_path / "env"
    manifest = {"objects": {"tenant.yml": {"hash": "h1", "schema": "s1"}}}
    save_manifest(env_dir, manifest)

    assert manifest_path(env_dir) == env_dir / ".envgene" / "object-hashes.json"
    assert load_manifest(env_dir) == manifest
    assert json.loads(manifest_bytes(manifest)) == manifest


def test_load_manifest_absent_returns_empty(tmp_path):
    assert load_manifest(tmp_path / "missing") == {"objects": {}}


def test_load_manifest_invalid_json_returns_empty(tmp_path):
    env_dir = tmp_path / "env"
    manifest_path(env_dir).parent.mkdir(parents=True)
    manifest_path(env_dir).write_text("not json")
    assert load_manifest(env_dir) == {"objects": {}}


def test_load_manifest_malformed_shape_returns_empty(tmp_path):
    env_dir = tmp_path / "env"
    manifest_path(env_dir).parent.mkdir(parents=True)
    manifest_path(env_dir).write_text(json.dumps({"objects": "nope"}))
    assert load_manifest(env_dir) == {"objects": {}}


def _built_env(tmp_path):
    env_dir = tmp_path / "environments" / "cluster" / "env"
    objects = CurrentEnvInstanceStore(env_dir)
    objects.put(env_dir / "tenant.yml", {"name": "t", "count": 1, "flag": True, "empty": None})
    objects.put(env_dir / "cloud.yml", {"name": "c", "items": ["a", {"b": "1"}]})
    objects.flush()
    return env_dir


def test_sync_is_noop_right_after_build(tmp_path):
    env_dir = _built_env(tmp_path)

    assert sync_manifest_with_disk(env_dir) is False


def test_sync_updates_entry_of_manually_edited_object(tmp_path):
    env_dir = _built_env(tmp_path)
    before = load_manifest(env_dir)["objects"]
    (env_dir / "tenant.yml").write_text("name: edited\n")

    assert sync_manifest_with_disk(env_dir) is True

    after = load_manifest(env_dir)["objects"]
    assert after["tenant.yml"]["hash"] != before["tenant.yml"]["hash"]
    assert after["cloud.yml"] == before["cloud.yml"]


def test_sync_removes_entry_of_deleted_object(tmp_path):
    env_dir = _built_env(tmp_path)
    (env_dir / "cloud.yml").unlink()

    assert sync_manifest_with_disk(env_dir) is True
    assert list(load_manifest(env_dir)["objects"]) == ["tenant.yml"]


def test_sync_keeps_validated_hashes(tmp_path):
    env_dir = _built_env(tmp_path)
    manifest = load_manifest(env_dir)
    save_manifest(env_dir, {**manifest, "validated": ["h1"]})
    (env_dir / "tenant.yml").write_text("name: edited\n")

    sync_manifest_with_disk(env_dir)

    assert load_manifest(env_dir)["validated"] == ["h1"]


def test_manually_edited_object_is_rebuilt_after_sync(tmp_path):
    env_dir = _built_env(tmp_path)
    (env_dir / "tenant.yml").write_text("name: edited\n")
    sync_manifest_with_disk(env_dir)

    objects = CurrentEnvInstanceStore(env_dir)
    objects.put(env_dir / "tenant.yml", {"name": "t", "count": 1, "flag": True, "empty": None})
    objects.put(env_dir / "cloud.yml", {"name": "c", "items": ["a", {"b": "1"}]})
    objects.flush()

    assert "edited" not in (env_dir / "tenant.yml").read_text()


def test_sync_without_manifest_does_nothing(tmp_path):
    assert sync_manifest_with_disk(tmp_path) is False
    assert not manifest_path(tmp_path).exists()


def test_sync_reads_root_app_def_from_base_dir(tmp_path):
    env_dir = tmp_path / "environments" / "cluster" / "env"
    objects = CurrentEnvInstanceStore(env_dir, base_dir=tmp_path)
    objects.put(tmp_path / "appdefs" / "demo.yml", {"name": "demo"})
    objects.flush()
    before = load_manifest(env_dir)["objects"]["appdefs/demo.yml"]

    assert sync_manifest_with_disk(env_dir, base_dir=tmp_path) is False

    (tmp_path / "appdefs" / "demo.yml").write_text("name: edited\n")

    assert sync_manifest_with_disk(env_dir, base_dir=tmp_path) is True
    assert load_manifest(env_dir)["objects"]["appdefs/demo.yml"] != before
