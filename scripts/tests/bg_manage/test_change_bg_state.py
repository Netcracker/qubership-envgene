from pathlib import Path
from types import SimpleNamespace

import pytest

from envgenehelper.models import BgdOperation
from scripts.bg_manage.change_bg_state import (
    S,
    mirror_pair,
    pair_to_str,
    VALID_TRANSITIONS,
    get_current_state,
    get_new_state,
    update_current_state,
    run_change_bg_state,
)


@pytest.fixture
def env_dir(tmp_path, monkeypatch):
    """Points get_current_env_dir_from_env_vars() at a throwaway directory
    and makes update_current_state's file deletion real-but-safe."""
    import scripts.bg_manage.change_bg_state as mod

    monkeypatch.setattr(mod, "get_current_env_dir_from_env_vars", lambda: str(tmp_path))

    def _delete_if_exists(path):
        p = Path(path)
        if p.exists():
            p.unlink()

    monkeypatch.setattr(mod, "deleteFileIfExists", _delete_if_exists)
    return tmp_path


def write_state_files(env_dir: Path, origin: str | None, peer: str | None):
    if origin:
        (env_dir / f".origin-{origin}").touch()
    if peer:
        (env_dir / f".peer-{peer}").touch()


def state_files_on_disk(env_dir: Path) -> set[str]:
    return {f.name for f in env_dir.iterdir() if f.is_file() and f.name.startswith(".")}


def make_ctx(op_value: str | None):
    params = {} if op_value is None else {"BGD_OPERATION": op_value}
    return SimpleNamespace(params=params)


class TestMirrorPair:
    def test_swaps_origin_and_peer(self):
        assert mirror_pair((S.ACTIVE, S.IDLE)) == (S.IDLE, S.ACTIVE)

    def test_double_mirror_is_identity(self):
        pair = (S.LEGACY, S.ACTIVE)
        assert mirror_pair(mirror_pair(pair)) == pair


class TestPairToStr:
    def test_format(self):
        assert pair_to_str((S.ACTIVE, S.IDLE)) == '{"origin": "active", "peer": "idle"}'


class TestTransitionTable:
    def test_only_bgd_operations_are_keys(self):
        assert set(VALID_TRANSITIONS) == {
            BgdOperation.INIT_DOMAIN,
            BgdOperation.WARMUP,
            BgdOperation.PROMOTE,
            BgdOperation.COMMIT,
            BgdOperation.ROLLBACK,
        }

    def test_bgd_init_has_no_mirror(self):
        table = VALID_TRANSITIONS[BgdOperation.INIT_DOMAIN]
        assert (S.ACTIVE, S.NONE) in table
        assert (S.NONE, S.ACTIVE) not in table

    @pytest.mark.parametrize("op", [
        BgdOperation.WARMUP,
        BgdOperation.PROMOTE,
        BgdOperation.COMMIT,
        BgdOperation.ROLLBACK,
    ])
    def test_non_init_operations_are_mirrored(self, op):
        table = VALID_TRANSITIONS[op]
        for curr, nxt in list(table.items()):
            assert mirror_pair(curr) in table
            assert table[mirror_pair(curr)] == mirror_pair(nxt)

    def test_warmup_forward_and_mirror(self):
        table = VALID_TRANSITIONS[BgdOperation.WARMUP]
        assert table[(S.ACTIVE, S.IDLE)] == (S.ACTIVE, S.CANDIDATE)
        assert table[(S.IDLE, S.ACTIVE)] == (S.CANDIDATE, S.ACTIVE)

    def test_promote_forward_and_mirror(self):
        table = VALID_TRANSITIONS[BgdOperation.PROMOTE]
        assert table[(S.ACTIVE, S.CANDIDATE)] == (S.LEGACY, S.ACTIVE)
        assert table[(S.CANDIDATE, S.ACTIVE)] == (S.ACTIVE, S.LEGACY)

    def test_commit_and_rollback_share_same_transition(self):
        commit = VALID_TRANSITIONS[BgdOperation.COMMIT]
        rollback = VALID_TRANSITIONS[BgdOperation.ROLLBACK]
        assert commit[(S.LEGACY, S.ACTIVE)] == (S.IDLE, S.ACTIVE)
        assert rollback[(S.LEGACY, S.ACTIVE)] == (S.IDLE, S.ACTIVE)


class TestGetCurrentState:
    def test_no_files_defaults_to_active_none(self, env_dir):
        assert get_current_state() == (S.ACTIVE, S.NONE)

    def test_reads_origin_and_peer_files(self, env_dir):
        write_state_files(env_dir, origin="active", peer="candidate")
        assert get_current_state() == (S.ACTIVE, S.CANDIDATE)

    def test_only_origin_file_present(self, env_dir):
        write_state_files(env_dir, origin="legacy", peer=None)
        assert get_current_state() == (S.LEGACY, S.NONE)

    def test_unknown_state_suffix_is_ignored(self, env_dir):
        (env_dir / ".origin-bogus").touch()
        write_state_files(env_dir, origin=None, peer="active")
        assert get_current_state() == (S.NONE, S.ACTIVE)

    def test_multiple_origin_files_raises(self, env_dir):
        (env_dir / ".origin-active").touch()
        (env_dir / ".origin-idle").touch()
        with pytest.raises(ValueError, match="origin"):
            get_current_state()

    def test_multiple_peer_files_raises(self, env_dir):
        (env_dir / ".peer-active").touch()
        (env_dir / ".peer-idle").touch()
        with pytest.raises(ValueError, match="peer"):
            get_current_state()

    def test_non_dotfiles_ignored(self, env_dir):
        (env_dir / "readme.txt").touch()
        assert get_current_state() == (S.ACTIVE, S.NONE)


class TestGetNewState:
    def test_valid_lookup(self):
        assert get_new_state(BgdOperation.INIT_DOMAIN, (S.ACTIVE, S.NONE)) == (S.ACTIVE, S.IDLE)

    def test_valid_mirror_lookup(self):
        assert get_new_state(BgdOperation.WARMUP, (S.IDLE, S.ACTIVE)) == (S.CANDIDATE, S.ACTIVE)

    def test_wrong_operation_for_state_raises(self):
        with pytest.raises(ValueError):
            get_new_state(BgdOperation.PROMOTE, (S.ACTIVE, S.IDLE))

    def test_unrecognised_current_state_raises(self):
        with pytest.raises(ValueError):
            get_new_state(BgdOperation.INIT_DOMAIN, (S.LEGACY, S.LEGACY))


class TestUpdateCurrentState:
    def test_removes_old_and_creates_new(self, env_dir):
        write_state_files(env_dir, origin="active", peer="none")
        update_current_state((S.ACTIVE, S.NONE), (S.ACTIVE, S.IDLE))
        assert state_files_on_disk(env_dir) == {".origin-active", ".peer-idle"}

    def test_noop_when_old_files_absent(self, env_dir):
        update_current_state((S.ACTIVE, S.NONE), (S.ACTIVE, S.IDLE))
        assert state_files_on_disk(env_dir) == {".origin-active", ".peer-idle"}


class TestRunChangeBgState:
    def test_invalid_operation_type_raises(self, env_dir):
        with pytest.raises(ValueError):
            run_change_bg_state(make_ctx("BGD-NOT-A-REAL-OP"))
        assert state_files_on_disk(env_dir) == set()

    def test_operation_type_is_case_insensitive(self, env_dir):
        write_state_files(env_dir, origin="active", peer="none")
        run_change_bg_state(make_ctx("init-domain"))
        assert state_files_on_disk(env_dir) == {".origin-active", ".peer-idle"}

    def test_init_from_active_none(self, env_dir):
        run_change_bg_state(make_ctx("INIT-DOMAIN"))
        assert state_files_on_disk(env_dir) == {".origin-active", ".peer-idle"}

    def test_warmup_from_active_idle(self, env_dir):
        write_state_files(env_dir, origin="active", peer="idle")
        run_change_bg_state(make_ctx("WARMUP"))
        assert state_files_on_disk(env_dir) == {".origin-active", ".peer-candidate"}

    def test_warmup_mirror_from_idle_active(self, env_dir):
        write_state_files(env_dir, origin="idle", peer="active")
        run_change_bg_state(make_ctx("WARMUP"))
        assert state_files_on_disk(env_dir) == {".origin-candidate", ".peer-active"}

    def test_promote_from_active_candidate(self, env_dir):
        write_state_files(env_dir, origin="active", peer="candidate")
        run_change_bg_state(make_ctx("PROMOTE"))
        assert state_files_on_disk(env_dir) == {".origin-legacy", ".peer-active"}

    def test_promote_mirror_from_candidate_active(self, env_dir):
        write_state_files(env_dir, origin="candidate", peer="active")
        run_change_bg_state(make_ctx("PROMOTE"))
        assert state_files_on_disk(env_dir) == {".origin-active", ".peer-legacy"}

    def test_commit_from_legacy_active(self, env_dir):
        write_state_files(env_dir, origin="legacy", peer="active")
        run_change_bg_state(make_ctx("COMMIT"))
        assert state_files_on_disk(env_dir) == {".origin-idle", ".peer-active"}

    def test_rollback_from_legacy_active_same_result_as_commit(self, env_dir):
        write_state_files(env_dir, origin="legacy", peer="active")
        run_change_bg_state(make_ctx("ROLLBACK"))
        assert state_files_on_disk(env_dir) == {".origin-idle", ".peer-active"}

    def test_disallowed_transition_raises_and_leaves_state_untouched(self, env_dir):
        write_state_files(env_dir, origin="active", peer="idle")
        with pytest.raises(ValueError):
            run_change_bg_state(make_ctx("PROMOTE"))
        assert state_files_on_disk(env_dir) == {".origin-active", ".peer-idle"}

    def test_unrecognised_current_state_raises_and_leaves_state_untouched(self, env_dir):
        write_state_files(env_dir, origin="legacy", peer="legacy")
        with pytest.raises(ValueError):
            run_change_bg_state(make_ctx("COMMIT"))
        assert state_files_on_disk(env_dir) == {".origin-legacy", ".peer-legacy"}

    def test_multiple_origin_files_raises_and_leaves_state_untouched(self, env_dir):
        (env_dir / ".origin-active").touch()
        (env_dir / ".origin-idle").touch()
        with pytest.raises(ValueError):
            run_change_bg_state(make_ctx("INIT_DOMAIN"))
        assert state_files_on_disk(env_dir) == {".origin-active", ".origin-idle"}
