"""YAML I/O — prefer envgenehelper, else ruyaml/ruamel round-trip."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _load_backend():
    try:
        from envgenehelper.yaml_helper import openYaml, writeYamlToFile  # type: ignore

        return openYaml, writeYamlToFile
    except ImportError:
        pass
    try:
        from ruyaml import YAML  # type: ignore
    except ImportError:
        from ruamel.yaml import YAML  # type: ignore

    yaml = YAML(typ="rt")
    yaml.preserve_quotes = True
    yaml.default_flow_style = False

    def open_yaml(path: str | Path) -> Any:
        p = Path(path)
        if not p.is_file():
            return None
        with p.open("r", encoding="utf-8") as fh:
            return yaml.load(fh)

    def write_yaml(path: str | Path, data: Any) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8") as fh:
            yaml.dump(data, fh)

    return open_yaml, write_yaml


open_yaml, write_yaml = _load_backend()


def try_decrypt_cred_file(path: Path) -> Any:
    """Load a credential YAML; decrypt via envgenehelper.crypt when needed."""
    data = open_yaml(path)
    if data is None:
        return None
    try:
        from envgenehelper import crypt  # type: ignore

        if crypt.is_cred_file(str(path)):
            # crypt APIs vary; best-effort in-memory decrypt of data map
            if hasattr(crypt, "decrypt_cred_data"):
                return crypt.decrypt_cred_data(data)
    except ImportError:
        pass
    except Exception as exc:  # noqa: BLE001 — surface to caller as preflight later
        if "SOPS" in str(exc).upper() or "AGE" in str(exc).upper():
            raise RuntimeError(
                f"Encrypted file requires SOPS_AGE_KEY: {path}"
            ) from exc
        raise
    return data
