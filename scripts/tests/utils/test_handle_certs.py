import base64
import datetime
import logging
import os
from pathlib import Path

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

from envgenehelper import logger
from utils import handle_certs
from utils.handle_certs import (
    SYSTEM_CA_BUNDLE,
    configure_git_server_trust,
    install_certificates,
)

pytestmark = pytest.mark.unit


def _self_signed_pem(common_name: str, *, expired: bool = False) -> bytes:
    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
    now = datetime.datetime.now(datetime.timezone.utc)
    not_before = now - datetime.timedelta(days=2) if expired else now
    not_after = now - datetime.timedelta(days=1) if expired else now + datetime.timedelta(days=1)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(not_before)
        .not_valid_after(not_after)
        .sign(key, hashes.SHA256())
    )
    return cert.public_bytes(serialization.Encoding.PEM)


@pytest.fixture
def ca_env(monkeypatch, tmp_path):
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    ca_dir = tmp_path / "ca-certificates"
    ca_dir.mkdir()
    monkeypatch.setenv("CI_PROJECT_DIR", str(project_dir))
    monkeypatch.delenv("SSL_CERTIFICATES_BUNDLE", raising=False)
    # setenv first so monkeypatch restores the original state of the var set by install_certificates
    monkeypatch.setenv("REQUESTS_CA_BUNDLE", "")
    monkeypatch.delenv("REQUESTS_CA_BUNDLE")
    monkeypatch.setattr(handle_certs, "CA_CERTS_DIR", ca_dir)
    monkeypatch.setattr(handle_certs, "DEFAULT_CERT", tmp_path / "default_cert.pem")
    update_calls: list[list[str]] = []

    def fake_run(cmd, *args, **kwargs):
        update_calls.append(list(cmd))
        input_data = kwargs.get("input", b"")

        if cmd == ["base64", "-d"]:
            compact = b"".join(input_data.split())
            try:
                decoded = base64.b64decode(compact, validate=True)
            except Exception:
                return type("Result", (), {"returncode": 1, "stdout": b"", "stderr": b""})()
            return type("Result", (), {"returncode": 0, "stdout": decoded, "stderr": b""})()

        if cmd[:3] == ["openssl", "x509", "-noout"]:
            if not input_data:
                return type("Result", (), {"returncode": 1, "stdout": b"", "stderr": b""})()
            try:
                cert = x509.load_pem_x509_certificate(input_data)
            except ValueError:
                return type("Result", (), {"returncode": 1, "stdout": b"", "stderr": b""})()

            common_name = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
            now = datetime.datetime.now(datetime.timezone.utc)

            if "-checkend" in cmd:
                returncode = 0 if cert.not_valid_after_utc >= now else 1
                return type("Result", (), {"returncode": returncode, "stdout": b"", "stderr": b""})()

            issuer_name = cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
            output = (
                f"subject=CN={common_name}\n"
                f"issuer=CN={issuer_name}\n"
                f"notBefore={cert.not_valid_before_utc.isoformat()}\n"
                f"notAfter={cert.not_valid_after_utc.isoformat()}\n"
            )
            return type("Result", (), {"returncode": 0, "stdout": output.encode(), "stderr": b""})()

        return type("Result", (), {"returncode": 0, "stdout": b"", "stderr": b""})()

    monkeypatch.setattr(handle_certs.subprocess, "run", fake_run)
    return {"project_dir": project_dir, "ca_dir": ca_dir, "tmp_path": tmp_path, "update_calls": update_calls}


def _certs_dir(ca_env) -> Path:
    certs_dir = ca_env["project_dir"] / "configuration" / "certs"
    certs_dir.mkdir(parents=True)
    return certs_dir


def _ca_bundle_dir(ca_env) -> Path:
    ca_bundle_dir = ca_env["project_dir"] / "ca_bundle"
    ca_bundle_dir.mkdir()
    return ca_bundle_dir


class TestInstallCertificates:
    @pytest.mark.unit
    def test_installs_certs_from_configuration_certs(self, ca_env):
        certs_dir = _certs_dir(ca_env)
        root = _self_signed_pem("corp-root-ca")
        (certs_dir / "corp-root.pem").write_bytes(root)
        (certs_dir / "intermediate.crt").write_bytes(_self_signed_pem("corp-intermediate-ca"))
        (certs_dir / "nested").mkdir()

        install_certificates()

        assert sorted(p.name for p in ca_env["ca_dir"].iterdir()) == ["corp-root.crt", "intermediate.crt"]
        assert (ca_env["ca_dir"] / "corp-root.crt").read_bytes() == root
        assert ca_env["update_calls"][-1] == ["update-ca-certificates"]
        assert os.environ["REQUESTS_CA_BUNDLE"] == SYSTEM_CA_BUNDLE

    @pytest.mark.unit
    def test_installs_certs_from_ca_bundle_dir(self, ca_env):
        (_ca_bundle_dir(ca_env) / "gitlab-root.pem").write_bytes(_self_signed_pem("gitlab-root-ca"))
        (_certs_dir(ca_env) / "corp-root.pem").write_bytes(_self_signed_pem("corp-root-ca"))

        install_certificates()

        assert sorted(p.name for p in ca_env["ca_dir"].iterdir()) == ["corp-root.crt", "gitlab-root.crt"]
        assert ca_env["update_calls"][-1] == ["update-ca-certificates"]

    @pytest.mark.unit
    def test_installs_multi_certificate_file(self, ca_env):
        chain = _self_signed_pem("corp-root-ca") + _self_signed_pem("corp-intermediate-ca")
        (_certs_dir(ca_env) / "chain.pem").write_bytes(chain)

        install_certificates()

        assert (ca_env["ca_dir"] / "chain.crt").read_bytes() == chain

    @pytest.mark.unit
    def test_later_source_replaces_same_target_name(self, monkeypatch, ca_env, caplog):
        from_certs_dir = _self_signed_pem("corp-from-certs-dir")
        (_ca_bundle_dir(ca_env) / "corp.pem").write_bytes(_self_signed_pem("corp-from-ca-bundle"))
        (_certs_dir(ca_env) / "corp.crt").write_bytes(from_certs_dir)
        monkeypatch.setattr(logger, "propagate", True)

        with caplog.at_level(logging.WARNING, logger=logger.name):
            install_certificates()

        assert (ca_env["ca_dir"] / "corp.crt").read_bytes() == from_certs_dir
        assert "replaces an earlier certificate installed as corp.crt" not in caplog.text

    @pytest.mark.unit
    def test_installs_decoded_bundle_and_certs_dir_without_default(self, monkeypatch, ca_env):
        (ca_env["tmp_path"] / "default_cert.pem").write_bytes(_self_signed_pem("image-default-ca"))
        (_certs_dir(ca_env) / "corp-root.pem").write_bytes(_self_signed_pem("corp-root-ca"))
        bundle = _self_signed_pem("bundle-ca")
        monkeypatch.setenv("SSL_CERTIFICATES_BUNDLE", base64.encodebytes(bundle).decode())

        install_certificates()

        installed = sorted(p.name for p in ca_env["ca_dir"].iterdir())
        bundle_name = next(name for name in installed if name != "corp-root.crt")
        assert installed == ["corp-root.crt", bundle_name]
        assert (ca_env["ca_dir"] / bundle_name).read_bytes() == bundle
        assert ca_env["update_calls"][-1] == ["update-ca-certificates"]

    @pytest.mark.unit
    def test_rejects_raw_pem_bundle(self, monkeypatch, ca_env):
        monkeypatch.setenv("SSL_CERTIFICATES_BUNDLE", _self_signed_pem("corp-root-ca").decode())

        with pytest.raises(ValueError, match="raw PEM content, not base64"):
            install_certificates()
        assert ca_env["update_calls"] == []

    @pytest.mark.unit
    def test_rejects_invalid_base64_bundle(self, monkeypatch, ca_env):
        monkeypatch.setenv("SSL_CERTIFICATES_BUNDLE", "not base64 !!!")

        with pytest.raises(ValueError, match="SSL_CERTIFICATES_BUNDLE is not valid base64"):
            install_certificates()
        assert ca_env["update_calls"] == [["base64", "-d"]]

    @pytest.mark.unit
    def test_rejects_expired_certificate(self, ca_env):
        (_certs_dir(ca_env) / "corp-root.pem").write_bytes(_self_signed_pem("corp-root-ca", expired=True))

        with pytest.raises(ValueError, match=r"Certificate validation failed for '.*corp-root\.pem.*'"):
            install_certificates()
        assert list(ca_env["ca_dir"].iterdir()) == []
        assert ca_env["update_calls"] == [["openssl", "x509", "-noout", "-checkend", "0"]]

    @pytest.mark.unit
    def test_rejects_file_without_pem_block(self, ca_env):
        certs_dir = _certs_dir(ca_env)
        (certs_dir / "readme.md").write_bytes(b"certificates go here")

        with pytest.raises(ValueError, match=r"Certificate validation failed for '.*readme\.md.*'"):
            install_certificates()
        assert list(ca_env["ca_dir"].iterdir()) == []
        assert ca_env["update_calls"] == []

    @pytest.mark.unit
    def test_falls_back_to_default_cert(self, ca_env):
        default_cert = _self_signed_pem("image-default-ca")
        (ca_env["tmp_path"] / "default_cert.pem").write_bytes(default_cert)

        install_certificates()

        assert [p.name for p in ca_env["ca_dir"].iterdir()] == ["default_cert.crt"]
        assert (ca_env["ca_dir"] / "default_cert.crt").read_bytes() == default_cert
        assert ca_env["update_calls"][-1] == ["update-ca-certificates"]

    @pytest.mark.unit
    def test_subdirectory_counts_as_source_and_blocks_default(self, ca_env):
        (ca_env["tmp_path"] / "default_cert.pem").write_bytes(_self_signed_pem("image-default-ca"))
        (_certs_dir(ca_env) / "nested").mkdir()

        install_certificates()

        assert list(ca_env["ca_dir"].iterdir()) == []
        assert ca_env["update_calls"] == []

    @pytest.mark.unit
    def test_skips_when_nothing_to_install(self, ca_env):
        _certs_dir(ca_env)

        install_certificates()

        assert list(ca_env["ca_dir"].iterdir()) == []
        assert ca_env["update_calls"] == []
        assert "REQUESTS_CA_BUNDLE" not in os.environ

    @pytest.mark.unit
    def test_fails_without_project_dir(self, monkeypatch, ca_env):
        monkeypatch.delenv("CI_PROJECT_DIR")

        with pytest.raises(ValueError, match="CI_PROJECT_DIR is not set"):
            install_certificates()
        assert ca_env["update_calls"] == []

    @pytest.mark.unit
    def test_logs_certificate_details_at_debug(self, monkeypatch, ca_env, caplog):
        (_certs_dir(ca_env) / "corp-root.pem").write_bytes(_self_signed_pem("corp-root-ca"))
        monkeypatch.setattr(logger, "propagate", True)

        with caplog.at_level(logging.DEBUG, logger=logger.name):
            install_certificates()

        assert "subject=CN=corp-root-ca" in caplog.text
        assert "Total: 1 certificate(s)" in caplog.text


class TestConfigureGitServerTrust:
    @pytest.fixture(autouse=True)
    def git_env(self, monkeypatch, tmp_path):
        monkeypatch.delenv("CI_SERVER_TLS_CA_FILE", raising=False)
        # setenv first so monkeypatch restores the original state of the var set by the function
        monkeypatch.setenv("GIT_SSL_CAINFO", "")
        monkeypatch.delenv("GIT_SSL_CAINFO")
        monkeypatch.setattr(handle_certs, "GIT_SERVER_CA_FILE", tmp_path / "ci_ca.pem")

    @pytest.mark.unit
    def test_uses_path_from_variable(self, monkeypatch, tmp_path):
        ca_file = tmp_path / "gitlab-ca.pem"
        ca_file.write_bytes(_self_signed_pem("gitlab-ca"))
        monkeypatch.setenv("CI_SERVER_TLS_CA_FILE", str(ca_file))

        configure_git_server_trust()

        assert os.environ["GIT_SSL_CAINFO"] == str(ca_file)
        assert not handle_certs.GIT_SERVER_CA_FILE.exists()

    @pytest.mark.unit
    def test_writes_pem_text_to_file(self, monkeypatch):
        pem = _self_signed_pem("gitlab-ca").decode()
        monkeypatch.setenv("CI_SERVER_TLS_CA_FILE", pem)

        configure_git_server_trust()

        assert os.environ["GIT_SSL_CAINFO"] == str(handle_certs.GIT_SERVER_CA_FILE)
        assert handle_certs.GIT_SERVER_CA_FILE.read_text() == f"{pem}\n"

    @pytest.mark.unit
    def test_skips_when_variable_is_unset(self):
        configure_git_server_trust()

        assert "GIT_SSL_CAINFO" not in os.environ
