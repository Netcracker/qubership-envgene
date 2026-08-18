"""Tests for cli_output: parse external-cred-provision log markers."""

from cred_migration.cli_output import CredOutcome, parse_cli_log


def test_parse_cli_log_captures_created_as_success():
    log = "some noise\n[app-db] created\nmore noise\n"
    result = parse_cli_log(log)
    assert result == {"app-db": CredOutcome(success=True, marker="created", detail=None)}


def test_parse_cli_log_captures_overwritten_as_success():
    result = parse_cli_log("[token] overwritten")
    assert result["token"].success is True
    assert result["token"].marker == "overwritten"


def test_parse_cli_log_captures_skipped_and_verified_as_success():
    result = parse_cli_log("[a] skipped\n[b] verified")
    assert result["a"].success is True
    assert result["b"].success is True


def test_parse_cli_log_captures_failed_with_reason():
    log = "[bad-cred] FAILED: RuntimeError: permission denied"
    result = parse_cli_log(log)
    assert result["bad-cred"].success is False
    assert result["bad-cred"].marker == "failed"
    assert "permission denied" in result["bad-cred"].detail


def test_parse_cli_log_captures_dry_run_ok_as_success():
    result = parse_cli_log("[app-db] dry_run_ok")
    assert result["app-db"].success is True


def test_parse_cli_log_captures_dry_run_fail_as_failure():
    result = parse_cli_log("[app-db] dry_run_fail: RuntimeError: absent")
    assert result["app-db"].success is False
    assert "absent" in result["app-db"].detail


def test_parse_cli_log_multiple_creds_in_one_log():
    log = (
        "starting\n"
        "[a] created\n"
        "[b] verified\n"
        "[c] FAILED: RuntimeError: broken\n"
        "done\n"
    )
    result = parse_cli_log(log)
    assert set(result.keys()) == {"a", "b", "c"}
    assert result["a"].success and result["b"].success and not result["c"].success


def test_parse_cli_log_ignores_unrelated_lines():
    log = "Pre-flight: ok\nSummary: created=1\n[a] created"
    result = parse_cli_log(log)
    assert list(result.keys()) == ["a"]
