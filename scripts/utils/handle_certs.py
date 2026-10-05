import base64
import binascii
import logging
import os
import subprocess
from pathlib import Path

from cryptography import x509

from envgenehelper import logger

CERTS_SUBDIR = Path("configuration") / "certs"
DEFAULT_CERT = Path("/default_cert.pem")
CA_CERTS_DIR = Path("/usr/local/share/ca-certificates")
SYSTEM_CA_BUNDLE = "/etc/ssl/certs/ca-certificates.crt"
BUNDLE_CERT_NAME = "ssl_certificates_bundle.crt"


def install_certificates() -> None:
    certs: dict[str, bytes] = {}

    bundle = os.getenv("SSL_CERTIFICATES_BUNDLE")
    if bundle:
        logger.info("SSL_CERTIFICATES_BUNDLE is set, installing...")
        certs[BUNDLE_CERT_NAME] = _decode_bundle(bundle)
    else:
        logger.info("SSL_CERTIFICATES_BUNDLE is not set, skipping")

    certs_dir = Path(os.environ["CI_PROJECT_DIR"]) / CERTS_SUBDIR
    cert_files = sorted(
        p for p in certs_dir.iterdir() if p.is_file() and not p.name.startswith(".")
    ) if certs_dir.is_dir() else []
    if cert_files:
        logger.info(f"Found certificates in {certs_dir}, installing...")
        for cert_file in cert_files:
            name = f"{cert_file.stem}.crt"
            if name in certs:
                logger.warning(f"Certificate {cert_file} replaces an earlier certificate installed as {name}")
            certs[name] = cert_file.read_bytes()
    else:
        logger.info(f"No certificates found in {certs_dir}, skipping")

    if not certs:
        if not DEFAULT_CERT.is_file():
            logger.info(f"No certificates found and default certificate does not exist: {DEFAULT_CERT}")
            return
        logger.info(f"Falling back to default certificate: {DEFAULT_CERT}")
        certs[f"{DEFAULT_CERT.stem}.crt"] = DEFAULT_CERT.read_bytes()

    for name, content in certs.items():
        target = CA_CERTS_DIR / name
        target.write_bytes(content)
        logger.info(f"Installing certificate: {target}")
        _log_certificates(name, content)

    subprocess.run(["update-ca-certificates"], check=True)
    os.environ["REQUESTS_CA_BUNDLE"] = SYSTEM_CA_BUNDLE
    logger.info(f"Certificate import completed, REQUESTS_CA_BUNDLE={SYSTEM_CA_BUNDLE}")


def _decode_bundle(value: str) -> bytes:
    try:
        return base64.b64decode("".join(value.split()), validate=True)
    except binascii.Error as e:
        raise ValueError("SSL_CERTIFICATES_BUNDLE is not valid base64") from e


def _log_certificates(name: str, content: bytes) -> None:
    if not logger.isEnabledFor(logging.DEBUG):
        return
    try:
        parsed = x509.load_pem_x509_certificates(content)
    except ValueError:
        logger.debug(f"No PEM certificate blocks found in {name}")
        return
    for num, cert in enumerate(parsed, start=1):
        logger.debug(
            f"Certificate #{num} in {name}: subject={cert.subject.rfc4514_string()}, "
            f"issuer={cert.issuer.rfc4514_string()}, "
            f"notBefore={cert.not_valid_before_utc}, notAfter={cert.not_valid_after_utc}"
        )
    logger.debug(f"Total: {len(parsed)} certificate(s) in {name}")
