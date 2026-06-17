"""
SD/DD Artifact Download tests.

UC-AD-SD-1..11 specify how the pipeline downloads Solution Descriptor artifacts
from Maven-compatible registries.  The actual HTTP download orchestration (Maven
metadata resolution, artifact streaming, aiohttp calls) runs inside artifact.py
and the Java Calculator — those paths are NOT reachable from pure Python unit
tests and are verified by CmdbCliTest.java (build_effective_set_generator/
effective-set-generator/src/test/java/.../CmdbCliTest.java) and integration
tests.

Python-level contracts tested here:
  parse_registry      — v1 vs v2 RegDef detection (UC-AD-SD-1..11 routing)
  MavenConfig         — trailing-slash normalisation; fullRepositoryUrl rejection
  Registry.resolve_auth    — v1 anonymous (UC-AD-SD-2) and basic auth (UC-AD-SD-1)
  RegistryV2.resolve_auth  — v2 anonymous, nexus/artifactory user_pass (UC-AD-SD-3..8)
  download_sd_by_appver    — SNAPSHOT version rejection (UC-AD-SD-11)
  multiply_sds_to_single   — EXTENDED mode multi-SD rejection
"""
import base64
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from scripts.build_env.tests.base_test import BaseTest

os.environ.setdefault("ENVIRONMENT_NAME", "env-01")
os.environ.setdefault("CLUSTER_NAME", "cluster-01")

_ARTIFACT_SEARCHER = Path(__file__).resolve().parents[4] / "python" / "artifact-searcher"
if str(_ARTIFACT_SEARCHER) not in sys.path:
    sys.path.insert(0, str(_ARTIFACT_SEARCHER))

_BUILD_ENV = Path(__file__).resolve().parents[2]
if str(_BUILD_ENV) not in sys.path:
    sys.path.insert(0, str(_BUILD_ENV))

from artifact_searcher.utils.models import (
    MavenConfig,
    MavenConfigV2,
    Registry,
    RegistryV2,
    parse_registry,
)
from artifact_searcher.auth_resolver import AUTH_METHOD_ANONYMOUS, AUTH_METHOD_USER_PASS
from process_sd import download_sd_by_appver, multiply_sds_to_single
from envgenehelper.sd_helper import MergeType

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

_MINIMAL_MAVEN = {
    "targetSnapshot": "snap",
    "targetStaging": "staging",
    "targetRelease": "release",
    "repositoryDomainName": "https://nexus.example.com/repository/maven/",
}

_MINIMAL_MAVEN_V2 = {
    "authConfig": "main",
    "repositoryDomainName": "https://nexus.example.com/repository/maven/",
    "targetSnapshot": "snap",
    "targetStaging": "staging",
    "targetRelease": "release",
}

_ENV_CREDS = {
    "nexus-creds": {
        "data": {
            "username": "ci-bot",
            "password": "s3cr3t",
        }
    }
}


def _expected_basic(username: str, password: str) -> dict:
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def _make_v1_registry(credentials_id: str = "") -> Registry:
    data = {"name": "my-nexus", "mavenConfig": _MINIMAL_MAVEN}
    if credentials_id:
        data["credentialsId"] = credentials_id
    return Registry.model_validate(data)


def _make_v2_registry(provider: str, auth_method: str, credentials_id: str = "") -> RegistryV2:
    auth_cfg = {"provider": provider, "authMethod": auth_method}
    if credentials_id:
        auth_cfg["credentialsId"] = credentials_id
    return RegistryV2.model_validate({
        "name": "my-nexus-v2",
        "version": "2.0",
        "authConfig": {"main": auth_cfg},
        "mavenConfig": _MINIMAL_MAVEN_V2,
    })


# ---------------------------------------------------------------------------
# parse_registry: v1 vs v2 routing
# ---------------------------------------------------------------------------

class TestParseRegistry(BaseTest):
    """
    parse_registry dispatches RegDef dicts to Registry (v1) or RegistryV2 (v2).
    Detection rule: v2 if version=="2.0" OR "authConfig" key present, else v1.
    """

    def test_plain_dict_without_version_or_auth_config_returns_v1(self):
        data = {"name": "r", "mavenConfig": _MINIMAL_MAVEN}
        result = parse_registry(data)
        assert isinstance(result, Registry)
        assert not isinstance(result, RegistryV2)

    def test_version_field_set_to_other_value_returns_v1(self):
        # "1.0" is not the v2 sentinel — falls back to v1 path.
        data = {"name": "r", "version": "1.0", "mavenConfig": _MINIMAL_MAVEN}
        result = parse_registry(data)
        assert isinstance(result, Registry)

    @patch("artifact_searcher.utils.models.jsonschema.validate", return_value=None)
    @patch("artifact_searcher.utils.models.get_regdef_v2_schema", return_value={})
    def test_version_2_0_triggers_v2_path(self, _schema, _validate):
        data = {
            "name": "r",
            "version": "2.0",
            "authConfig": {"main": {"provider": "nexus", "authMethod": "user_pass"}},
            "mavenConfig": _MINIMAL_MAVEN_V2,
        }
        result = parse_registry(data)
        assert isinstance(result, RegistryV2)

    @patch("artifact_searcher.utils.models.jsonschema.validate", return_value=None)
    @patch("artifact_searcher.utils.models.get_regdef_v2_schema", return_value={})
    def test_auth_config_key_triggers_v2_path_even_without_version(self, _schema, _validate):
        # authConfig key is sufficient — version field is optional in v2.
        data = {
            "name": "r",
            "authConfig": {"main": {"provider": "nexus", "authMethod": "user_pass"}},
            "mavenConfig": _MINIMAL_MAVEN_V2,
        }
        result = parse_registry(data)
        assert isinstance(result, RegistryV2)

    def test_empty_dict_raises_validation_error(self):
        # Empty dict lacks all required fields → ValidationError, not silent None.
        with pytest.raises(ValidationError):
            parse_registry({})

    def test_missing_maven_config_raises_validation_error(self):
        # name present but mavenConfig absent → ValidationError.
        with pytest.raises(ValidationError):
            parse_registry({"name": "r"})


# ---------------------------------------------------------------------------
# MavenConfig validators
# ---------------------------------------------------------------------------

class TestMavenConfigValidators(BaseTest):
    """
    MavenConfig normalises repositoryDomainName to always have a trailing slash,
    and rejects fullRepositoryUrl if set (use repositoryDomainName instead).
    These validators run at parse time and affect URL construction inside
    artifact.py for all download paths.
    """

    def _make(self, domain: str, full_url: str = "") -> MavenConfig:
        data = dict(_MINIMAL_MAVEN)
        data["repositoryDomainName"] = domain
        if full_url:
            data["fullRepositoryUrl"] = full_url
        return MavenConfig.model_validate(data)

    def test_trailing_slash_added_when_missing(self):
        m = self._make("https://nexus.example.com/repository/maven")
        assert m.repository_domain_name.endswith("/")

    def test_trailing_slash_preserved_when_already_present(self):
        m = self._make("https://nexus.example.com/repository/maven/")
        assert m.repository_domain_name == "https://nexus.example.com/repository/maven/"

    def test_multiple_trailing_slashes_normalised_to_one(self):
        m = self._make("https://nexus.example.com/repository/maven///")
        assert m.repository_domain_name == "https://nexus.example.com/repository/maven/"

    def test_full_repository_url_raises_validation_error(self):
        # UC-AD-SD: fullRepositoryUrl is explicitly unsupported; parse must fail fast.
        with pytest.raises(ValidationError, match="not supported"):
            self._make(
                domain="https://nexus.example.com/repository/maven/",
                full_url="https://nexus.example.com/repository/maven/com/example/app/1.0/app-1.0.json",
            )


class TestMavenConfigValidatorsNegative(BaseTest):
    """Negative: MavenConfig rejects structurally invalid input."""

    def test_missing_required_field_raises_validation_error(self):
        # repositoryDomainName is required — absent → ValidationError, not AttributeError.
        with pytest.raises(ValidationError):
            MavenConfig.model_validate({
                "targetSnapshot": "snap",
                "targetStaging": "staging",
                "targetRelease": "release",
                # repositoryDomainName intentionally omitted
            })

    def test_empty_repository_domain_name_still_becomes_slash(self):
        # Edge case: empty string → rstrip("/") + "/" = "/". No exception raised.
        m = MavenConfig.model_validate({
            **_MINIMAL_MAVEN,
            "repositoryDomainName": "",
        })
        assert m.repository_domain_name == "/"


class TestMavenConfigV2Validators(BaseTest):
    """MavenConfigV2 applies the same trailing-slash normalisation as v1."""

    def _make(self, domain: str) -> MavenConfigV2:
        data = dict(_MINIMAL_MAVEN_V2)
        data["repositoryDomainName"] = domain
        return MavenConfigV2.model_validate(data)

    def test_trailing_slash_added_when_missing(self):
        m = self._make("https://artifactory.example.com/maven")
        assert m.repository_domain_name.endswith("/")

    def test_trailing_slash_preserved_when_already_present(self):
        m = self._make("https://artifactory.example.com/maven/")
        assert m.repository_domain_name == "https://artifactory.example.com/maven/"

    def test_missing_auth_config_field_raises_validation_error(self):
        # authConfig is required in MavenConfigV2 — absent → ValidationError.
        with pytest.raises(ValidationError):
            MavenConfigV2.model_validate({
                "repositoryDomainName": "https://artifactory.example.com/maven/",
                "targetSnapshot": "snap",
                "targetStaging": "staging",
                "targetRelease": "release",
                # authConfig intentionally omitted
            })


# ---------------------------------------------------------------------------
# Registry (v1) resolve_auth
# ---------------------------------------------------------------------------

class TestRegistryV1ResolveAuth(BaseTest):
    """
    UC-AD-SD-1 — credentialsId present and env_creds contain the credential
    → Authorization: Basic header.

    UC-AD-SD-2 — credentialsId absent (anonymous registry) → None.
    """

    def test_no_credentials_id_returns_none(self):
        reg = _make_v1_registry(credentials_id="")
        assert reg.resolve_auth({"any": {"data": {"username": "u", "password": "p"}}}) is None

    def test_none_env_creds_returns_none(self):
        reg = _make_v1_registry(credentials_id="nexus-creds")
        assert reg.resolve_auth(None) is None

    def test_empty_env_creds_returns_none(self):
        reg = _make_v1_registry(credentials_id="nexus-creds")
        assert reg.resolve_auth({}) is None

    def test_credential_key_absent_from_env_creds_returns_none(self):
        # credentialsId is set but not present in env_creds — silently returns None.
        reg = _make_v1_registry(credentials_id="nexus-creds")
        assert reg.resolve_auth({"other-creds": {"data": {"username": "u", "password": "p"}}}) is None

    def test_valid_credentials_return_basic_auth_header(self):
        # UC-AD-SD-1: credentialsId + matching env_creds → Basic base64 header.
        reg = _make_v1_registry(credentials_id="nexus-creds")
        result = reg.resolve_auth(_ENV_CREDS)
        assert result == _expected_basic("ci-bot", "s3cr3t")

    def test_basic_auth_header_key_is_authorization(self):
        reg = _make_v1_registry(credentials_id="nexus-creds")
        result = reg.resolve_auth(_ENV_CREDS)
        assert "Authorization" in result
        assert result["Authorization"].startswith("Basic ")

    def test_basic_auth_value_is_base64_encoded_user_colon_pass(self):
        reg = _make_v1_registry(credentials_id="nexus-creds")
        result = reg.resolve_auth(_ENV_CREDS)
        encoded = result["Authorization"].removeprefix("Basic ")
        decoded = base64.b64decode(encoded).decode()
        assert decoded == "ci-bot:s3cr3t"

    def test_credential_found_but_username_missing_returns_none(self):
        # Credential exists but data has no username → resolve_auth returns None silently.
        creds = {"nexus-creds": {"data": {"password": "s3cr3t"}}}
        reg = _make_v1_registry(credentials_id="nexus-creds")
        assert reg.resolve_auth(creds) is None

    def test_credential_found_but_password_missing_returns_none(self):
        # Credential exists but data has no password → resolve_auth returns None silently.
        creds = {"nexus-creds": {"data": {"username": "ci-bot"}}}
        reg = _make_v1_registry(credentials_id="nexus-creds")
        assert reg.resolve_auth(creds) is None

    def test_credential_found_but_data_empty_returns_none(self):
        # Credential entry exists but data dict is empty → returns None.
        creds = {"nexus-creds": {"data": {}}}
        reg = _make_v1_registry(credentials_id="nexus-creds")
        assert reg.resolve_auth(creds) is None


# ---------------------------------------------------------------------------
# RegistryV2 resolve_auth
# ---------------------------------------------------------------------------

class TestRegistryV2ResolveAuth(BaseTest):
    """
    UC-AD-SD-3..8 — RegistryV2 authConfig block governs auth header resolution.

    AWS (UC-AD-SD-9) and GCP (UC-AD-SD-10) providers require cloud SDK calls
    (AWSCodeArtifactHelper, GcpCredentialsProvider) — those paths are NOT
    reachable from unit tests and are verified by integration tests.
    """

    def test_anonymous_auth_method_returns_none(self):
        # UC-AD-SD-8 (anonymous): no Authorization header emitted.
        reg = _make_v2_registry("nexus", AUTH_METHOD_ANONYMOUS)
        assert reg.resolve_auth({}) is None

    def test_anonymous_does_not_require_credentials_in_env(self):
        reg = _make_v2_registry("nexus", AUTH_METHOD_ANONYMOUS)
        assert reg.resolve_auth(None) is None

    def test_nexus_user_pass_returns_basic_auth_header(self):
        # UC-AD-SD-3: nexus + user_pass → Basic Authorization.
        reg = _make_v2_registry("nexus", AUTH_METHOD_USER_PASS, credentials_id="nexus-creds")
        result = reg.resolve_auth(_ENV_CREDS)
        assert result == _expected_basic("ci-bot", "s3cr3t")

    def test_artifactory_user_pass_returns_basic_auth_header(self):
        # UC-AD-SD-5: artifactory + user_pass → Basic Authorization.
        reg = _make_v2_registry("artifactory", AUTH_METHOD_USER_PASS, credentials_id="nexus-creds")
        result = reg.resolve_auth(_ENV_CREDS)
        assert result == _expected_basic("ci-bot", "s3cr3t")

    def test_v2_basic_auth_value_is_correctly_encoded(self):
        reg = _make_v2_registry("nexus", AUTH_METHOD_USER_PASS, credentials_id="nexus-creds")
        result = reg.resolve_auth(_ENV_CREDS)
        encoded = result["Authorization"].removeprefix("Basic ")
        decoded = base64.b64decode(encoded).decode()
        assert decoded == "ci-bot:s3cr3t"

    def test_missing_credential_in_env_creds_raises(self):
        # credentialsId references a credential that isn't in env_creds → ValueError.
        reg = _make_v2_registry("nexus", AUTH_METHOD_USER_PASS, credentials_id="nexus-creds")
        with pytest.raises(ValueError, match="not found in decrypted credentials"):
            reg.resolve_auth({})

    def test_auth_config_name_mismatch_raises(self):
        # mavenConfig.authConfig references "main" but registry.authConfig has no such key.
        reg = RegistryV2.model_validate({
            "name": "r",
            "version": "2.0",
            "authConfig": {
                "other": {"provider": "nexus", "authMethod": "user_pass", "credentialsId": "c"}
            },
            "mavenConfig": {
                "authConfig": "main",  # "main" not in authConfig dict
                "repositoryDomainName": "https://nexus.example.com/",
                "targetSnapshot": "s",
                "targetStaging": "s",
                "targetRelease": "r",
            },
        })
        with pytest.raises(ValueError, match="not found in registry"):
            reg.resolve_auth({})


# ---------------------------------------------------------------------------
# UC-AD-SD-11: SNAPSHOT version rejection
# ---------------------------------------------------------------------------

class TestSnapshotRejection(BaseTest):
    """
    UC-AD-SD-11 — SNAPSHOT versions of Solution Descriptor artifacts are
    rejected immediately by download_sd_by_appver before any network call.
    This ensures only stable releases enter the effective set.
    """

    def test_snapshot_suffix_raises_value_error(self):
        with pytest.raises(ValueError, match="SNAPSHOT"):
            download_sd_by_appver("my-app", "1.2.3-SNAPSHOT", MagicMock())

    def test_snapshot_anywhere_in_version_raises(self):
        # Even unconventional strings containing SNAPSHOT are rejected.
        with pytest.raises(ValueError, match="SNAPSHOT"):
            download_sd_by_appver("my-app", "SNAPSHOT-1.2.3", MagicMock())

    def test_snapshot_substring_raises(self):
        with pytest.raises(ValueError, match="SNAPSHOT"):
            download_sd_by_appver("my-app", "1.0.0-SNAPSHOT-RELEASE", MagicMock())

    def test_release_version_passes_snapshot_guard(self):
        # A non-SNAPSHOT version should NOT raise from the SNAPSHOT check.
        # The function will fail later when trying to read AppDef files from disk,
        # but that is a different error — the SNAPSHOT guard itself is not triggered.
        with pytest.raises(Exception) as exc_info:
            download_sd_by_appver("my-app", "1.2.3", MagicMock())
        assert "SNAPSHOT" not in str(exc_info.value)


# ---------------------------------------------------------------------------
# multiply_sds_to_single: EXTENDED mode constraint
# ---------------------------------------------------------------------------

class TestMultiplySdsExtended(BaseTest):
    """
    EXTENDED merge mode requires exactly one SD; multiple SDs are ambiguous and
    must be rejected immediately rather than silently merging or discarding.
    """

    def test_single_sd_in_extended_mode_accepted(self):
        sd = {"applications": []}
        result = multiply_sds_to_single([sd], MergeType.EXTENDED)
        assert result == sd

    def test_multiple_sds_in_extended_mode_raises(self):
        sds = [{"applications": []}, {"applications": []}]
        with pytest.raises(ValueError, match="Multiple SDs not supported"):
            multiply_sds_to_single(sds, MergeType.EXTENDED)

    def test_three_sds_in_extended_mode_raises(self):
        sds = [{"applications": []}, {"applications": []}, {"applications": []}]
        with pytest.raises(ValueError, match="Multiple SDs not supported"):
            multiply_sds_to_single(sds, MergeType.EXTENDED)

    def test_multiple_sds_in_basic_mode_are_merged(self):
        # BASIC mode merges multiple SDs — no exception expected.
        sds = [{"applications": []}, {"applications": []}]
        result = multiply_sds_to_single(sds, MergeType.BASIC)
        assert "applications" in result
