import base64
import binascii
import logging
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from cryptography import x509

from envgenehelper import logger

CA_BUNDLE_SUBDIR = Path("ca_bundle")
CERTS_SUBDIR = Path("configuration") / "certs"
DEFAULT_CERT = Path("/default_cert.pem")
CA_CERTS_DIR = Path("/usr/local/share/ca-certificates")
SYSTEM_CA_BUNDLE = "/etc/ssl/certs/ca-certificates.crt"
BUNDLE_CERT_NAME = "ssl_certificates_bundle.crt"
GIT_SERVER_CA_FILE = Path("/tmp/ci_ca.pem")

_PEM_BLOCK = re.compile(rb"-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----", re.DOTALL)


def configure_git_server_trust() -> None:
    value = os.getenv("CI_SERVER_TLS_CA_FILE")
    if not value:
        return
    if _is_existing_file(value):
        ca_file = value  
    else:
        GIT_SERVER_CA_FILE.write_text(f"{value}\n") 
        ca_file = str(GIT_SERVER_CA_FILE)
    os.environ["GIT_SSL_CAINFO"] = ca_file
    logger.info(f"Git trusts the CI server certificate, GIT_SSL_CAINFO={ca_file}")


def install_certificates() -> None:
    project_dir = os.getenv("CI_PROJECT_DIR")
    if not project_dir:
        raise ValueError("CI_PROJECT_DIR is not set")

    certs: dict[str, bytes] = {}
    source_found = False

    bundle = os.getenv("SSL_CERTIFICATES_BUNDLE")
    if bundle:
        logger.info("SSL_CERTIFICATES_BUNDLE is set, installing...")
        certs[BUNDLE_CERT_NAME] = _decode_bundle(bundle)
        source_found = True
    else:
        logger.info("SSL_CERTIFICATES_BUNDLE is not set, skipping")

    for subdir in (CA_BUNDLE_SUBDIR, CERTS_SUBDIR):
        certs_dir = Path(project_dir) / subdir
        entries = sorted(certs_dir.iterdir()) if certs_dir.is_dir() else []
        if not entries:
            logger.info(f"No certificates found in {certs_dir}, skipping")
            continue
        logger.info(f"Found certificates in {certs_dir}, installing...")
        source_found = True
        for entry in entries:
            if not entry.is_file():
                continue
            name = f"{entry.stem}.crt"
            if name in certs:
                logger.warning(f"Certificate {entry} replaces an earlier certificate installed as {name}")
            certs[name] = entry.read_bytes()

    if not source_found:
        if not DEFAULT_CERT.is_file():
            logger.info(f"No certificates found and default certificate does not exist: {DEFAULT_CERT}")
            return
        logger.info(f"Falling back to default certificate: {DEFAULT_CERT}")
        certs[f"{DEFAULT_CERT.stem}.crt"] = DEFAULT_CERT.read_bytes()

    if not certs:
        return

    parsed = {name: _validate_source(name, content) for name, content in certs.items()}

    for name, content in certs.items():
        target = CA_CERTS_DIR / name
        target.write_bytes(content)
        logger.info(f"Installing certificate: {target}")
        _log_certificates(name, parsed[name])

    subprocess.run(["update-ca-certificates"], check=True)
    os.environ["REQUESTS_CA_BUNDLE"] = SYSTEM_CA_BUNDLE
    logger.info(f"Certificate import completed, REQUESTS_CA_BUNDLE={SYSTEM_CA_BUNDLE}")


def _is_existing_file(value: str) -> bool:
    try:
        return Path(value).is_file()
    except OSError:
        return False


def _decode_bundle(value: str) -> bytes:
    if "BEGIN CERTIFICATE" in value:
        raise ValueError(
            "SSL_CERTIFICATES_BUNDLE appears to contain raw PEM content, not base64. "
            "Please base64-encode your certificate bundle before setting this variable."
        )
    try:
        return base64.b64decode("".join(value.split()), validate=True)
    except binascii.Error as e:
        raise ValueError("SSL_CERTIFICATES_BUNDLE is not valid base64") from e


def _validate_source(name: str, content: bytes) -> list[x509.Certificate]:
    blocks = _PEM_BLOCK.findall(content)
    if not blocks:
        raise ValueError(f"No valid PEM certificate blocks found in {name}")
    now = datetime.now(timezone.utc)
    parsed: list[x509.Certificate] = []
    failed = False
    for num, block in enumerate(blocks, start=1):
        try:
            cert = x509.load_pem_x509_certificate(block)
        except ValueError:
            logger.warning(f"Certificate #{num} in {name} is expired or invalid")
            failed = True
            continue
        if cert.not_valid_after_utc < now:
            logger.warning(f"Certificate #{num} in {name} is expired or invalid")
            failed = True
            continue
        parsed.append(cert)
    if failed:
        raise ValueError(f"Certificate validation failed for '{name}'")
    return parsed


def _log_certificates(name: str, parsed: list[x509.Certificate]) -> None:
    if not logger.isEnabledFor(logging.DEBUG):
        return
    for num, cert in enumerate(parsed, start=1):
        logger.debug(
            f"Certificate #{num} in {name}: subject={cert.subject.rfc4514_string()}, "
            f"issuer={cert.issuer.rfc4514_string()}, "
            f"notBefore={cert.not_valid_before_utc}, notAfter={cert.not_valid_after_utc}"
        )
    logger.debug(f"Total: {len(parsed)} certificate(s) in {name}")

