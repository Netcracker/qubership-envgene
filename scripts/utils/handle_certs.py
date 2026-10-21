import os
import re
import subprocess
import tempfile
from pathlib import Path
from envgenehelper import logger

DEFAULT_CERT = Path("/default_cert.pem")
CA_CERTS_DIR = Path("/usr/local/share/ca-certificates")
SYSTEM_CA_BUNDLE = "/etc/ssl/certs/ca-certificates.crt"
GIT_SERVER_CA_FILE = Path("/tmp/ci_ca.pem")
BASHRC = Path.home() / ".bashrc"

CA_BUNDLE_SUBDIR = Path("ca_bundle")
CERTS_SUBDIR = Path("configuration") / "certs"

_PEM_BLOCK = re.compile(
    rb"-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----",
    re.DOTALL,
)


def _append_bashrc(variable: str, value: str) -> None:
    with BASHRC.open("a", encoding="utf-8") as file:
        file.write(f"export {variable}={value}\n")


def configure_git_server_trust() -> None:
    value = os.getenv("CI_SERVER_TLS_CA_FILE")
    if not value:
        return

    if Path(value).is_file():
        ca_file = value
    else:
        GIT_SERVER_CA_FILE.write_text(f"{value}\n", encoding="utf-8")
        ca_file = str(GIT_SERVER_CA_FILE)

    os.environ["GIT_SSL_CAINFO"] = ca_file
    _append_bashrc("GIT_SSL_CAINFO", ca_file)

    logger.info(f"Git trusts the CI server certificate, GIT_SSL_CAINFO={ca_file}")


def _certificate_filename(source: str) -> str:
    basename = Path(source).name
    stem = re.sub(r"\.[^.]*$", "", basename)
    return f"{stem}.crt"


def _decode_bundle(value: str) -> bytes:
    if "BEGIN CERTIFICATE" in value:
        raise ValueError(
            "SSL_CERTIFICATES_BUNDLE appears to contain raw PEM content, "
            "not base64. Please base64-encode your certificate bundle "
            "before setting this variable."
        )

    result = subprocess.run(
        ["base64", "-d"],
        input=(value + "\n").encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )

    if result.returncode != 0:
        raise ValueError("SSL_CERTIFICATES_BUNDLE is not valid base64")

    return result.stdout


def _debug_print_certificates(file: Path, label: str) -> None:
    if not logger.isEnabledFor(10):
        return
    logger.debug(f"=== {label} ===")
    if not file.exists():
        logger.debug(f"File does not exist: {file}")
        return

    cert_num = 0
    block = bytearray()

    with file.open("rb") as stream:
        for raw_line in stream:
            line = raw_line.rstrip(b"\n").removesuffix(b"\r")

            if line == b"-----BEGIN CERTIFICATE-----":
                block = bytearray(line + b"\n")
                continue

            if block:
                block.extend(line + b"\n")

                if line == b"-----END CERTIFICATE-----":
                    cert_num += 1
                    logger.debug(
                        f"--- Certificate #{cert_num} "
                        f"in {file} ---"
                    )
                    result = subprocess.run(
                        [
                            "openssl",
                            "x509",
                            "-noout",
                            "-subject",
                            "-issuer",
                            "-dates",
                        ],
                        input=bytes(block),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL,
                        check=False,
                    )
                    if result.returncode == 0:
                        logger.debug(result.stdout.decode(errors="replace"))
                    else:
                        logger.debug("(openssl could not decode this block)")
                    block = bytearray()

    if cert_num == 0:
        logger.debug(f"No PEM certificate blocks found in {file}")
    else:
        logger.debug(f"Total: {cert_num} certificate(s)")
    logger.debug(f"=== End {label} ===")


def _validate_bundle(file: Path, label: str) -> None:
    count = 0
    failed = False
    content = file.read_bytes()

    for block in _PEM_BLOCK.findall(content):
        count += 1

        result = subprocess.run(
            ["openssl", "x509", "-noout", "-checkend", "0"],
            input=block + b"\n",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )

        if result.returncode != 0:
            logger.warning(f"Certificate #{count} in {label} is expired or invalid")
            failed = True

    if count == 0:
        logger.warning(f"No valid PEM certificate blocks found in {label}")
        failed = True

    if failed:
        raise ValueError(f"Certificate validation failed for '{label}'")


def _install_certificate_file(ca_file: Path, label: str | None = None) -> None:
    label = label or str(ca_file)

    if not ca_file.is_file():
        logger.warning(f"CA file '{label}' not found or empty, skipping")
        return

    _debug_print_certificates(ca_file, f"Certificates in source file BEFORE import ({ca_file})")
    _validate_bundle(ca_file, label)
    local_name = _certificate_filename(str(ca_file))
    target = CA_CERTS_DIR / local_name
    target.write_bytes(ca_file.read_bytes())
    subprocess.run(["update-ca-certificates"], check=True)
    logger.info(f"certs from '{label}' added to trusted root")
    os.environ["REQUESTS_CA_BUNDLE"] = SYSTEM_CA_BUNDLE
    _append_bashrc("REQUESTS_CA_BUNDLE", SYSTEM_CA_BUNDLE)
    _debug_print_certificates(
        target,
        f"Certificates AFTER import "
        f"(installed file {target})",
    )

    logger.info(f"Certificate import completed successfully for '{label}'")


def _install_certificates_from_dir(directory: Path) -> None:
    with os.scandir(directory) as entries:
        for entry in entries:
            if not entry.is_file(follow_symlinks=False):
                continue

            cert = Path(entry.path)
            logger.info(f"Installing certificate: {cert}")
            _install_certificate_file(cert, f"{cert.name} (from {directory})")


def install_certificates() -> None:
    project_dir = os.getenv("CI_PROJECT_DIR")
    if not project_dir:
        raise ValueError("CI_PROJECT_DIR is not set")
    ca_bundle_dir = Path(project_dir) / CA_BUNDLE_SUBDIR
    certs_dir = Path(project_dir) / CERTS_SUBDIR
    certs_applied = 0
    bundle = os.getenv("SSL_CERTIFICATES_BUNDLE")
    if bundle:
        logger.info("SSL_CERTIFICATES_BUNDLE is set, installing...")
        bundle_content = _decode_bundle(bundle)
        fd, bundle_path = tempfile.mkstemp(prefix="ssl_bundle_", dir="/tmp")
        bundle_file = Path(bundle_path)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(bundle_content)

            _install_certificate_file(
                bundle_file,
                "SSL_CERTIFICATES_BUNDLE",
            )
        finally:
            if bundle_file.exists():
                bundle_file.unlink()

        certs_applied = 1
    else:
        logger.info("SSL_CERTIFICATES_BUNDLE is not set, skipping")

    if ca_bundle_dir.is_dir() and any(ca_bundle_dir.iterdir()):
        logger.info(f"Found certificates in {ca_bundle_dir}, installing...")
        _install_certificates_from_dir(ca_bundle_dir)
        certs_applied = 1
    else:
        logger.info(f"No certificates found in {ca_bundle_dir}, skipping")

    if certs_dir.is_dir() and any(certs_dir.iterdir()):
        logger.info(f"Found certificates in {certs_dir}, installing...")
        _install_certificates_from_dir(certs_dir)
        certs_applied = 1
    else:
        logger.info(f"No certificates found in {certs_dir}, skipping")

    if certs_applied == 0:
        if DEFAULT_CERT.is_file():
            logger.info(f"Falling back to default certificate: {DEFAULT_CERT}")
            _install_certificate_file(
                DEFAULT_CERT,
                f"default certificate ({DEFAULT_CERT})",
            )
        else:
            logger.info(f"No certificates found and default certificate does not exist: {DEFAULT_CERT}")
