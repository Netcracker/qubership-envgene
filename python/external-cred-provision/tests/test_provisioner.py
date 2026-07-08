from unittest.mock import patch

import pytest

from external_cred_provision.provisioner import (
    CredentialEntry,
    ExternalCredProvisioner,
    PasswordGenerator,
    Strategy,
)


class TestPasswordGenerator:
    def test_default_length(self):
        assert len(PasswordGenerator.generate()) == PasswordGenerator.DEFAULT_LENGTH

    def test_custom_length(self):
        assert len(PasswordGenerator.generate(length=32)) == 32

    def test_chars_within_charset(self):
        for _ in range(20):
            assert all(c in PasswordGenerator.CHARS for c in PasswordGenerator.generate())


class TestParseCredential:
    VAULT_URI = "ref+vault://secret/data/env/my-cred"
    GCP_URI = "ref+gcpsecrets://my-project/my-secret"

    def _parse(self, cred_id, entry, provider_type="vault", store_id=None):
        with patch(
            "external_cred_provision.provisioner.MultiStoreProvider.parse_provider_type",
            return_value=(provider_type, store_id),
        ):
            return ExternalCredProvisioner._parse_credential(cred_id, entry)

    def test_valid_vault_create_if_absent(self):
        cred, errors = self._parse("my-cred", {
            "vals": self.VAULT_URI,
            "strategy": "create_if_absent",
            "data": {"username": "admin", "password": "_generateValue"},
        })
        assert errors == []
        assert isinstance(cred, CredentialEntry)
        assert cred.id == "my-cred"
        assert cred.strategy == Strategy.CREATE_IF_ABSENT
        assert cred.data == {"username": "admin", "password": "_generateValue"}

    def test_valid_vault_overwrite(self):
        cred, errors = self._parse("my-cred", {
            "vals": self.VAULT_URI,
            "strategy": "overwrite",
            "data": {"password": "_generateValue"},
        })
        assert errors == []
        assert cred.strategy == Strategy.OVERWRITE

    def test_valid_fail_if_absent_no_data_required(self):
        cred, errors = self._parse("my-cred", {
            "vals": self.VAULT_URI,
            "strategy": "fail_if_absent",
        })
        assert errors == []
        assert cred.data is None

    def test_missing_vals(self):
        _, errors = self._parse("my-cred", {"strategy": "fail_if_absent"})
        assert any("missing required field 'vals'" in e for e in errors)

    def test_missing_strategy(self):
        _, errors = self._parse("my-cred", {"vals": self.VAULT_URI})
        assert any("missing required field 'strategy'" in e for e in errors)

    def test_unknown_strategy(self):
        _, errors = self._parse("my-cred", {
            "vals": self.VAULT_URI,
            "strategy": "destroy_if_present",
        })
        assert any("unknown strategy" in e for e in errors)

    def test_data_required_for_create_if_absent(self):
        _, errors = self._parse("my-cred", {
            "vals": self.VAULT_URI,
            "strategy": "create_if_absent",
        })
        assert any("missing required field 'data'" in e for e in errors)

    def test_data_required_for_overwrite(self):
        _, errors = self._parse("my-cred", {
            "vals": self.VAULT_URI,
            "strategy": "overwrite",
        })
        assert any("missing required field 'data'" in e for e in errors)

    def test_string_data_rejected_for_vault(self):
        _, errors = self._parse("my-cred", {
            "vals": self.VAULT_URI,
            "strategy": "create_if_absent",
            "data": "_generateValue",
        }, provider_type="vault")
        assert any("plain-string data is not supported" in e for e in errors)

    def test_string_data_rejected_for_openbao(self):
        _, errors = self._parse("my-cred", {
            "vals": "ref+openbao://kv/data/env/my-cred",
            "strategy": "create_if_absent",
            "data": "_generateValue",
        }, provider_type="openbao")
        assert any("plain-string data is not supported" in e for e in errors)

    def test_string_data_allowed_for_gcp(self):
        cred, errors = self._parse("my-cred", {
            "vals": self.GCP_URI,
            "strategy": "create_if_absent",
            "data": "_generateValue",
        }, provider_type="gcp")
        assert errors == []
        assert cred.data == "_generateValue"

    def test_invalid_data_type(self):
        _, errors = self._parse("my-cred", {
            "vals": self.VAULT_URI,
            "strategy": "create_if_absent",
            "data": 42,
        })
        assert any("'data' must be a string or a dict" in e for e in errors)

    def test_store_id_propagated(self):
        cred, errors = self._parse("my-cred", {
            "vals": "ref+vault://secret/data/env/my-cred?secret_store_id=prod",
            "strategy": "fail_if_absent",
        }, provider_type="vault", store_id="prod")
        assert errors == []
        assert cred.store_id == "prod"

    def test_multiple_errors_collected(self):
        _, errors = self._parse("bad-cred", {})
        assert len(errors) >= 2  # both vals and strategy missing


class TestResolveData:
    provisioner = ExternalCredProvisioner(context_path="dummy")

    def test_literal_string_unchanged(self):
        assert self.provisioner._resolve_data("literal-value") == "literal-value"

    def test_generate_marker_string_produces_correct_length(self):
        result = self.provisioner._resolve_data("_generateValue")
        assert len(result) == PasswordGenerator.DEFAULT_LENGTH

    def test_generate_marker_string_uses_charset(self):
        result = self.provisioner._resolve_data("_generateValue")
        assert all(c in PasswordGenerator.CHARS for c in result)

    def test_dict_literal_values_unchanged(self):
        data = {"username": "admin", "password": "s3cr3t"}
        assert self.provisioner._resolve_data(data) == data

    def test_dict_generate_marker_field_replaced(self):
        result = self.provisioner._resolve_data({"username": "admin", "password": "_generateValue"})
        assert result["username"] == "admin"
        assert len(result["password"]) == PasswordGenerator.DEFAULT_LENGTH

    def test_dict_all_markers_generate_independently(self):
        result = self.provisioner._resolve_data({"a": "_generateValue", "b": "_generateValue"})
        assert len(result["a"]) == PasswordGenerator.DEFAULT_LENGTH
        assert len(result["b"]) == PasswordGenerator.DEFAULT_LENGTH
        assert result["a"] != result["b"]
