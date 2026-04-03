import pathlib
from envgenehelper import *


def get_excluded_dirs_for_namespace_role(role: NamespaceRole, origin_template_exists: bool,
                                         peer_template_exists: bool) -> list[str]:
    common_dir = 'from_template'
    origin_dir = 'from_origin_template'
    peer_dir = 'from_peer_template'
    if role == NamespaceRole.ORIGIN and origin_template_exists:
        return [common_dir, peer_dir]
    if role == NamespaceRole.PEER and peer_template_exists:
        return [common_dir, origin_dir]
    return [origin_dir, peer_dir]


PARAMSET_LAYER_FILE_MASKS = ["*.json", "*.yml", "*.yaml", "*.j2"]
RESOURCE_PROFILE_LAYER_FILE_MASKS = ["*.yml", "*.yaml"]


def iter_role_template_files(base_dir: str, masks: list[str], excluded_dirs: list[str]):
    root = pathlib.Path(base_dir)
    if not root.exists():
        return
    for mask in masks:
        for f in root.rglob(mask):
            if not f.is_file():
                continue
            file_path = str(f)
            if any(excluded_dir in file_path for excluded_dir in excluded_dirs):
                continue
            yield extractNameFromFile(file_path), file_path
