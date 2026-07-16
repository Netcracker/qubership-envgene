from pathlib import Path

from envgenehelper import logger, openYaml, writeYamlToFile

NAMESPACE_MAP_FILE = "namespace-map.yml"


def compute_namespace_map(namespaces_dir: Path) -> dict[str, str]:
    """Build deployPostfix -> namespace name map from rendered ``Namespaces/`` folders."""
    if not namespaces_dir.is_dir():
        raise FileNotFoundError(f"Namespaces directory does not exist: {namespaces_dir}")

    namespace_map: dict[str, str] = {}
    for folder_path in sorted(namespaces_dir.iterdir()):
        if not folder_path.is_dir():
            continue

        namespace_file = folder_path / "namespace.yml"
        if not namespace_file.is_file():
            logger.warning(f"Skipping {folder_path}: namespace.yml not found")
            continue

        data = openYaml(namespace_file)
        ns_name = data.get("name")
        if not ns_name or not isinstance(ns_name, str):
            raise ValueError(f"'name' is missing or invalid in {namespace_file}")

        namespace_map[folder_path.name] = ns_name

    if not namespace_map:
        raise ValueError(f"No namespaces found under {namespaces_dir}")

    logger.info(f"Namespace map built: {namespace_map}")
    return namespace_map


def write_namespace_map(namespace_map: dict[str, str], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    writeYamlToFile(output_path, namespace_map)
    logger.info(f"Wrote namespace map to {output_path}")
