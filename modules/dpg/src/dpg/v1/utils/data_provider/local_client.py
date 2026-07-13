import os
import yaml
import functools
from pathlib import Path

from .middleware import DataProviderInterface, UnifiedAppDef, UnifiedRegDef

from dpg.v1.utils.registry import RegistryInfo, MavenConfig, RegistryType, AuthUserPassword

class LocalClient(DataProviderInterface):
    DEFAULT_PATH_TO_APPDEFS = os.getenv("LOCAL_APPDEFS_PATH", "AppDefs")
    DEFAULT_PATH_TO_REGDEFS = os.getenv("LOCAL_REGDEFS_PATH", "RegDefs")

    def __init__(self, root_dir: Path = None):
        self.root_dir = root_dir
        if self.root_dir is None:
            self.root_dir = Path(os.getcwd())

    @functools.cache
    def get_app_def(self, application: str) -> UnifiedAppDef:
        apppath = self.root_dir / Path(self.DEFAULT_PATH_TO_APPDEFS) / f"{application}.yml"
        if not apppath.exists():
            raise Exception("File with appdef & fallback client doesn't exists.")

        appdef_d = yaml.safe_load(apppath.read_text())
        if appdef_d is None:
            raise Exception(f"Can't dump yaml file: {apppath}")

        appdef = UnifiedAppDef(
            name=appdef_d.get("name"),
            group_id=appdef_d.get("groupId"),
            artifact_id=appdef_d.get('artifactId'),
            solution_descriptor=appdef_d.get("solutionDescriptor"),
            registry=appdef_d.get("registryName"),
            metadata=appdef_d.get("metadata", dict())
        )
        return appdef

    @functools.cache
    def get_reg_def(self, registry: str) -> UnifiedAppDef:
        regpath = self.root_dir / Path(self.DEFAULT_PATH_TO_REGDEFS) / f"{registry}.yml"
        if not regpath.exists():
            raise Exception("File with appdef & fallback client doesn't exists.")

        regdef_d = yaml.safe_load(regpath.read_text())
        if regdef_d is None:
            raise Exception(f"Can't dump yaml file: {regpath}")

        return UnifiedRegDef(
            name=regdef_d.get("name", ""),
            credential_id=regdef_d.get("credentialsId", ""),
            maven={
                "repo_domain_name": regdef_d["mavenConfig"].get("repositoryDomainName", ""),
                "full_repo_url": regdef_d["mavenConfig"].get("fullRepositoryUrl", ""),
                "snapshot_repo": regdef_d["mavenConfig"].get("targetSnapshot", ""),
                "staging_repo": regdef_d["mavenConfig"].get("targetStaging", ""),
                "release_repo": regdef_d["mavenConfig"].get("targetRelease", ""),
                "snapshot_group": regdef_d["mavenConfig"].get("snapshotGroup", ""),
                "release_group": regdef_d["mavenConfig"].get("releaseGroup", "")
            },
            docker={
                "snapshot_uri": regdef_d["dockerConfig"].get("snapshotUri", ""),
                "staging_uri": regdef_d["dockerConfig"].get("stagingUri", ""),
                "release_uri": regdef_d["dockerConfig"].get("RELEASE_URI", ""),
                "group_uri": regdef_d["dockerConfig"].get("releaseUri", ""),
            },
            helm={
                "release_repo": regdef_d["helmConfig"].get("targetRelease", ""),
                "snapshot_repo": regdef_d["helmConfig"].get("targetStaging", "")
            },
            helm_app={
                "release_repo": regdef_d["helmAppConfig"].get("targetRelease", ""),
                "staging_repo": regdef_d["helmAppConfig"].get("targetStaging", ""),
                "group_repo": regdef_d["helmAppConfig"].get("groupRepository", ""),
                "dev_repo": regdef_d["helmAppConfig"].get("targetDev", "")
            }
        )

    @functools.cache
    def get_registry_info(self, registry: str) -> RegistryInfo:
        regdef = self.get_reg_def(registry=registry)

        __type_reg = RegistryType.ARTIFACTORY
        __maven_config = MavenConfig(**{
            "targetRelease": regdef.maven.get("release_repo"),
            "targetStaging": regdef.maven.get("staging_repo"),
            "targetSnapshot": regdef.maven.get("snapshot_repo")
        })

        __url = regdef.maven.get("repo_domain_name")
        if not __url or __url == "":
            __url = regdef.maven.get("full_repo_url")

        __auth_config = AuthUserPassword(
            registry_url=__url,
            username="",
            password=""
        )

        # TODO: need to implement getting auth config from something config

        return RegistryInfo(
            url=__url,
            type=__type_reg,
            maven_config=__maven_config,
            auth_config=__auth_config
        )
