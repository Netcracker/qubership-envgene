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
from utils.handle_certs import BUNDLE_CERT_NAME, SYSTEM_CA_BUNDLE, install_certificates


def _self_signed_pem(common_name: str) -> bytes:
    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=1))
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
    monkeypatch.setattr(handle_certs.subprocess, "run", lambda cmd, check: update_calls.append(cmd))
    return {"project_dir": project_dir, "ca_dir": ca_dir, "tmp_path": tmp_path, "update_calls": update_calls}


def _certs_dir(ca_env) -> Path:
    certs_dir = ca_env["project_dir"] / "configuration" / "certs"
    certs_dir.mkdir(parents=True)
    return certs_dir


class TestInstallCertificates:
    @pytest.mark.unit
    def test_installs_certs_from_configuration_certs(self, ca_env):
        certs_dir = _certs_dir(ca_env)
        (certs_dir / "corp-root.pem").write_bytes(b"root")
        (certs_dir / "intermediate.crt").write_bytes(b"intermediate")
        (certs_dir / "nested").mkdir()

        install_certificates()

        assert sorted(p.name for p in ca_env["ca_dir"].iterdir()) == ["corp-root.crt", "intermediate.crt"]
        assert (ca_env["ca_dir"] / "corp-root.crt").read_bytes() == b"root"
        assert ca_env["update_calls"] == [["update-ca-certificates"]]
        assert os.environ["REQUESTS_CA_BUNDLE"] == SYSTEM_CA_BUNDLE

    @pytest.mark.unit
    def test_skips_hidden_files_in_certs_dir(self, ca_env):
        certs_dir = _certs_dir(ca_env)
        (certs_dir / ".gitkeep").write_bytes(b"")
        (certs_dir / "corp-root.pem").write_bytes(b"root")

        install_certificates()

        assert [p.name for p in ca_env["ca_dir"].iterdir()] == ["corp-root.crt"]

    @pytest.mark.unit
    def test_warns_when_certificates_share_target_name(self, monkeypatch, ca_env, caplog):
        certs_dir = _certs_dir(ca_env)
        (certs_dir / "corp.crt").write_bytes(b"first")
        (certs_dir / "corp.pem").write_bytes(b"second")
        monkeypatch.setattr(logger, "propagate", True)

        with caplog.at_level(logging.WARNING, logger=logger.name):
            install_certificates()

        assert (ca_env["ca_dir"] / "corp.crt").read_bytes() == b"second"
        assert "replaces an earlier certificate installed as corp.crt" in caplog.text

    @pytest.mark.unit
    def test_installs_decoded_bundle_and_certs_dir_without_default(self, monkeypatch, ca_env):
        (ca_env["tmp_path"] / "default_cert.pem").write_bytes(b"default")
        (_certs_dir(ca_env) / "corp-root.pem").write_bytes(b"root")
        encoded = base64.encodebytes(b"bundle-content").decode()
        monkeypatch.setenv("SSL_CERTIFICATES_BUNDLE", encoded)

        install_certificates()

        assert sorted(p.name for p in ca_env["ca_dir"].iterdir()) == ["corp-root.crt", BUNDLE_CERT_NAME]
        assert (ca_env["ca_dir"] / BUNDLE_CERT_NAME).read_bytes() == b"bundle-content"
        assert ca_env["update_calls"] == [["update-ca-certificates"]]

    @pytest.mark.unit
    def test_rejects_invalid_base64_bundle(self, monkeypatch, ca_env):
        monkeypatch.setenv("SSL_CERTIFICATES_BUNDLE", "not base64 !!!")

        with pytest.raises(ValueError, match="SSL_CERTIFICATES_BUNDLE is not valid base64"):
            install_certificates()
        assert ca_env["update_calls"] == []

    @pytest.mark.unit
    def test_falls_back_to_default_cert(self, ca_env):
        (ca_env["tmp_path"] / "default_cert.pem").write_bytes(b"default")

        install_certificates()

        assert [p.name for p in ca_env["ca_dir"].iterdir()] == ["default_cert.crt"]
        assert ca_env["update_calls"] == [["update-ca-certificates"]]

    @pytest.mark.unit
    def test_skips_when_nothing_to_install(self, ca_env):
        _certs_dir(ca_env)

        install_certificates()

        assert list(ca_env["ca_dir"].iterdir()) == []
        assert ca_env["update_calls"] == []
        assert "REQUESTS_CA_BUNDLE" not in os.environ

    @pytest.mark.unit
    def test_logs_certificate_details_at_debug(self, monkeypatch, ca_env, caplog):
        (_certs_dir(ca_env) / "corp-root.pem").write_bytes(_self_signed_pem("corp-root-ca"))
        monkeypatch.setattr(logger, "propagate", True)

        with caplog.at_level(logging.DEBUG, logger=logger.name):
            install_certificates()

        assert "subject=CN=corp-root-ca" in caplog.text
        assert "Total: 1 certificate(s) in corp-root.crt" in caplog.text
