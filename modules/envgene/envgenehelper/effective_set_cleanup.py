import logging
import re
import shutil
from pathlib import Path

import yaml as pyyaml

logger = logging.getLogger(__name__)

CONTEXTS = ("deployment", "runtime")
CLEANUP_CONTEXT = "cleanup"
MAPPING_FILE = "mapping.yaml"


def _read_mapping(effective_set: Path, context: str) -> dict[str, str]:
    mapping_path = effective_set / context / MAPPING_FILE
    if not mapping_path.is_file():
        return {}
    loaded = pyyaml.safe_load(mapping_path.read_text()) or {}
    if not isinstance(loaded, dict):
        return {}
    return {str(key): str(value) for key, value in loaded.items()}


def _namespace_dir(effective_set: Path, context: str, namespace: str, value: str) -> Path:
    folder = Path(value).name
    context_dir = effective_set / context
    namespace_dir = context_dir / folder
    if (not folder or folder in (".", "..") or namespace_dir.is_symlink()
            or not namespace_dir.resolve().is_relative_to(context_dir.resolve())):
        raise ValueError(f"Invalid effective set mapping for namespace '{namespace}'")
    return namespace_dir


def clean_namespaces(effective_set: Path, namespaces: str = "") -> None:
    mappings = {context: _read_mapping(effective_set, context) for context in CONTEXTS}
    selected = list(dict.fromkeys(filter(None, re.split(r"\\n|[;,\s]+", namespaces))))
    if not selected:
        selected = sorted(set().union(*(mapping.keys() for mapping in mappings.values())))

    for namespace in selected:
        found = False
        for context, mapping in mappings.items():
            if namespace not in mapping:
                continue
            found = True
            namespace_dir = _namespace_dir(effective_set, context, namespace, mapping[namespace])
            if not namespace_dir.is_dir():
                logger.warning("Namespace '%s' is absent from effective set context '%s'", namespace, context)
                continue
            marker = namespace_dir / ".cleaned"
            if marker.exists():
                logger.warning("Namespace '%s' is already cleaned in context '%s'", namespace, context)
            for application in namespace_dir.iterdir():
                if application.is_dir() and not application.is_symlink():
                    for content in application.iterdir():
                        if content.is_dir() and not content.is_symlink():
                            shutil.rmtree(content)
                        else:
                            content.unlink()
                    # Git needs a tracked file to preserve the application directory.
                    (application / ".gitkeep").touch()
                else:
                    application.unlink()
            marker.touch()
        if not found:
            logger.warning("Namespace '%s' is absent from the effective set", namespace)

    cleanup_context = effective_set / CLEANUP_CONTEXT
    if cleanup_context.is_dir() and not cleanup_context.is_symlink():
        shutil.rmtree(cleanup_context)
    else:
        cleanup_context.unlink(missing_ok=True)


def remove_cleaned_markers(effective_set: Path, namespaces: set[str]) -> None:
    for context in CONTEXTS:
        mapping = _read_mapping(effective_set, context)
        for namespace in namespaces & mapping.keys():
            namespace_dir = _namespace_dir(effective_set, context, namespace, mapping[namespace])
            marker = namespace_dir / ".cleaned"
            if not marker.is_file():
                continue
            if not any(path.is_file() and path.name not in (".cleaned", ".gitkeep")
                       for path in namespace_dir.rglob("*")):
                raise ValueError(f"No published application content for previously cleaned namespace '{namespace}'")
            marker.unlink()
