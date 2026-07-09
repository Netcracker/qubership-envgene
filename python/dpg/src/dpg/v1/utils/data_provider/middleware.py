import abc
from dataclasses import dataclass, field
from typing import Dict

@dataclass
class UnifiedAppDef:

    name: str
    group_id: str = ""
    artifact_id: str = ""
    solution_descriptor: bool = False
    registry: str = ""
    metadata: dict = field(default_factory=dict)

@dataclass
class UnifiedRegDef:

    name: str
    credential_id: str = ""
    maven: Dict[str, str] = field(
        default_factory=lambda: {
            "repo_domain_name": "",
            "full_repo_url": "",
            "snapshot_repo": "",
            "staging_repo": "",
            "release_repo": "",
            "snapshot_group": "",
            "release_group": ""
        })
    docker: Dict[str, str] = field(
        default_factory=lambda: {
            "snapshot_uri": "",
            "staging_uri": "",
            "release_uri": "",
            "group_uri": "",
            "snapshot_repo": "",
            "staging_repo": "",
            "release_repo": "",
            "group_name": ""
        }
    )
    go: Dict[str, str] = field(
        default_factory=lambda: {
            "release_repo": "",
            "snapshot_repo": "",
            "proxy_repo": ""
        }
    )
    raw: Dict[str, str] = field(
        default_factory=lambda: {
            "snapshot_repo": "",
            "release_repo": "",
            "staging_repo": "",
            "proxy_repo": ""
        }
    )
    npm: Dict[str, str] = field(
        default_factory=lambda: {
            "release_repo": "",
            "snapshot_repo": ""
        }
    )
    helm: Dict[str, str] = field(
        default_factory=lambda: {
            "release_repo": "",
            "snapshot_repo": ""
        }
    )
    helm_app: Dict[str, str] = field(
        default_factory=lambda: {
            "staging_repo": "",
            "release_repo": "",
            "group_repo": "",
            "dev_repo": ""
        }
    )

class DataProviderInterface(metaclass=abc.ABCMeta):
    def get_app_def(self, application: str) -> UnifiedAppDef:
        raise NotImplementedError

    def get_reg_def(self, registry: str) -> UnifiedRegDef:
        raise NotImplementedError

