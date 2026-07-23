import json
import re
import yaml
import copy
import uuid6
import logging
from pathlib import Path
from typing import Tuple, List

from .models import DeployPlan, DeployPlanEntity, GenerationType

import dpg.v1.utils as utils
from dpg.v1.utils.data_provider import DataProviderInterface
from dpg.v1.internal.sd import SolutionDescriptorParser
from dpg.v1.internal.artifact_descriptor import DDFinder
from dpg.v1.internal.common import CommonSettings

class DeploymentPlanCalculator:
    _RE_NS_APP_VER = re.compile(r'^(?P<namespace>[^:]+):(?P<name>[^:]+):(?P<version>.+)$')
    _RE_APP_VER    = re.compile(r'^(?P<name>[^:]+):(?P<version>.+)$')

    def __init__(self, applications: List[str] | List[dict], data_provider: DataProviderInterface):
        self.applications = applications
        self.data_provider = data_provider

    @classmethod
    def map_namespaces_to_plan(cls, deploy_plan: DeployPlan, map: dict) -> DeployPlan:
        """This method should map namespaces by postfixes to deploy plan"""

        # TODO: do it based on input map
        map_namespaces = map
        map_deploypostfixes = {v: k for k, v in map_namespaces.items()}

        cdeploy_plan = copy.deepcopy(deploy_plan)
        for entity in cdeploy_plan.entities:
            if entity.deploy_postfix == "":
                entity.deploy_postfix = map_deploypostfixes[entity.namespace]
            else:
                entity.namespace = map_namespaces[entity.deploy_postfix]

        return cdeploy_plan

        logging.debug(f"Namespace mapping applied..")
        return deploy_plan

    def calculate(self) -> DeployPlan:
        deploy_plan = self.__collect_waves()
        deploy_plan = self.__enrich_plan_generation_types(deploy_plan=deploy_plan)

        if not self.__validate_deploy_plan(deploy_plan):
            raise Exception("Validation of deploy plan failed.")

        return deploy_plan

    def __enrich_plan_generation_types(self, deploy_plan: DeployPlan):
        run_uuid = uuid6.uuid7()
        for entity in deploy_plan.entities:
            appname, version = entity.version.split(":")
            appdef = self.data_provider.get_app_def(application=appname)

            generation_type = appdef.metadata.get(CommonSettings.METADATA_KEY_GENERATION_TYPE, "UniqForApp")
            try:
                generation_type = GenerationType(generation_type)
            except ValueError:
                logging.error(f"Invalid type of generation provided in metadata AppDef for `{entity.version}`. Provided: {generation_type}. Avaiable types of generation: `{GenerationType.__members__.values()}`")
                raise ValueError(f"Invalid type of generation provided in metadata AppDef for `{entity.version}`. Provided: {generation_type}. Avaiable types of generation: `{GenerationType.__members__.values()}`")

            entity.generation_type = generation_type
            # we should provide generation id only for UniqForRun
            if entity.generation_type == GenerationType.UNIQ_FOR_RUN:
                entity.generation_id = run_uuid

        return deploy_plan

    def __validate_deploy_plan(self, deploy_plan: DeployPlan) -> bool:
        for entity in deploy_plan.entities:
            if entity.deploy_postfix == "" and entity.namespace == "":
                raise ValueError(
                    f"Cannot determine namespace for '{entity.version}' in wave {entity.wave}: "
                    "no deployPostfix set and version is not in 'namespace:name:version' format"
                )
        return True

    def __resolve_content(self, app) -> Tuple[dict | None, bool]:
        match app:
            case dict():
                content = app
            case str() if utils.is_file_path(app):
                content = self.__read_file(Path(app))
            case str():
                name = self._parse_app(app)["version"].split(":")[0]
                appdef = self.data_provider.get_app_def(application=name)
                if not appdef.solution_descriptor:
                    return None, False

                content = DDFinder(data_provider=self.data_provider).get(app)
            case _:
                return None, False

        if not content:
            return None, False
        return content, content.get("type") == "solutionDeploy"

    @classmethod
    def _parse_app(cls, app: str) -> dict:
        if m := cls._RE_NS_APP_VER.match(app):
            return {"version": f"{m['name']}:{m['version']}", "namespace": m['namespace']}
        if m := cls._RE_APP_VER.match(app):
            return {"version": app, "namespace": ""}
        raise ValueError(f"Cannot parse app identifier: '{app}'")

    @staticmethod
    def __read_file(path: Path) -> dict | None:
        with open(path, encoding="utf-8") as f:
            if path.suffix in (".yaml", ".yml"):
                return yaml.safe_load(f)
            if path.suffix == ".json":
                return json.load(f)
        return None

    def __collect_waves(self) -> DeployPlan:
        entities = []
        wave_index = 0

        for app in self.applications:
            logging.info(f"Resolving for {app}")
            content, is_sd = self.__resolve_content(app)

            if not is_sd:
                logging.debug(f"Adding standalone application: {app}")
                entities.append(DeployPlanEntity(wave=wave_index, deployPostfix="", **self._parse_app(app)))
                continue

            sd = SolutionDescriptorParser.parse(filepath=app, content=content)
            collected_waves = sd.collect_waves()
            sd_app_count = sum(len(v) for v in collected_waves.values())
            logging.debug(f"Solution descriptor {app} resolved: {len(collected_waves)} wave(s),"
                      f" {sd_app_count} application(s), offset: {wave_index}")

            for wave, waveapps in collected_waves.items():
                for entity in waveapps:
                    entity.wave = wave_index + wave
                    entities.append(entity)
            wave_index += max(collected_waves.keys()) + 1

        return DeployPlan(entities=entities)

