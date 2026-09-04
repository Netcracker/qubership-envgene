"""Core command facade — stateless entry points for calculate, map, and filter operations."""

import os
import re
import yaml
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Union, List, Optional

from dpg.v1.internal.deployment_plan import DeploymentPlanCalculator, DeployPlan
import dpg.v1.utils as utils


class DeploymentPlanGeneratorCommand:
    """Stateless facade over the three deployment-plan operations.

    Each method validates its inputs, delegates to the internal calculator,
    logs progress, and writes the result to *output_file*.
    """

    @staticmethod
    def calculate(applications: Union[str, list], output_file: Path = "deploy-plan.yaml", rootdir: Path = None) -> DeployPlan:
        if isinstance(applications, str):
            applications_content = utils.load_json_or_yaml(applications)
            if applications_content:
                applications = [applications_content] if isinstance(applications_content, dict) else applications_content
            else:
                applications = _split_application_list(applications)

        logging.info(
            f"Calculating deployment plan"
            f" [{len(applications)} application(s)]"
        )

        deploy_plan = DeploymentPlanCalculator(
            applications=applications,
            data_provider=utils.get_data_provider(root_dir=rootdir),
        ).calculate()

        wave_count = len({e.wave for e in deploy_plan.entities})
        app_count = len(deploy_plan.entities)
        logging.info(f"Deployment plan ready: {wave_count} wave(s), {app_count} application(s)")
        logging.debug(f"Plan details:\n{deploy_plan}")

        logging.info(f"Writing deploy plan to {output_file}..")
        with open(output_file, "w") as f:
            f.write(yaml.dump(deploy_plan.to_dict()))

        return deploy_plan

    @staticmethod
    def map(deploy_plan: Union[DeployPlan, Path, str], map: Union[Path, str], output_file: Path = "deploy-plan.yaml") -> DeployPlan:
        deploy_plan = resolve_deploy_plan(deploy_plan)
        logging.info(f"Input plan details:\n{deploy_plan}")

        if utils.is_file_path(map):
            with open(map, "r") as f:
                map = utils.load_json_or_yaml(f.read())

        if not isinstance(map, dict) or len(map.keys()) == 0:
            raise Exception("Map provided in input param `params.map` invalid.")

        deploy_plan = DeploymentPlanCalculator.map_namespaces_to_plan(deploy_plan, map=map)

        wave_count = len({e.wave for e in deploy_plan.entities})
        app_count = len(deploy_plan.entities)
        logging.info(f"Deployment plan ready: {wave_count} wave(s), {app_count} application(s)")
        logging.debug(f"Plan details:\n{deploy_plan}")

        logging.info(f"Writing deploy plan to {output_file}..")
        with open(output_file, "w") as f:
            f.write(yaml.dump(deploy_plan.to_dict()))

        return deploy_plan

    @staticmethod
    def filter(deploy_plan: Union[DeployPlan, Path, str], deploy_postfix_filter: Optional[str] = None, component_names_filter: Optional[str] = None, wave_filter: Optional[str] = None, namespace_filter: Optional[str] = None, output_file: Path = "deploy-plan.yaml") -> DeployPlan:
        deploy_postfix_filter = _parse_filter(deploy_postfix_filter)
        component_names_filter = _parse_filter(component_names_filter)
        wave_filter = _parse_filter(wave_filter)
        namespace_filter = _parse_filter(namespace_filter)

        deploy_plan = resolve_deploy_plan(deploy_plan)
        logging.info(f"Input plan details:\n{deploy_plan}")

        logging.debug(
            f"Active filters — "
            f"deploy_postfix: {deploy_postfix_filter or 'none'}, "
            f"component_names: {component_names_filter or 'none'}, "
            f"wave: {wave_filter or 'none'}, "
            f"namespace: {namespace_filter or 'none'}"
        )

        filtered_plan = _apply_filters(
            deploy_plan,
            deploy_postfix_filter=deploy_postfix_filter,
            component_names_filter=component_names_filter,
            wave_filter=wave_filter,
            namespace_filter=namespace_filter,
        )

        before, after = len(deploy_plan.entities), len(filtered_plan.entities)
        logging.info(f"Filtering complete: {before} → {after} application(s) retained")
        logging.debug(f"Filtered plan details:\n{filtered_plan}")

        logging.info(f"Writing deploy plan to {output_file}..")
        with open(output_file, "w") as f:
            f.write(yaml.dump(filtered_plan.to_dict(), sort_keys=False))

        return filtered_plan

    @staticmethod
    def merge(deploy_plans: List[Union[DeployPlan, Path, str]], output_file: Path = "deploy-plan.yaml") -> Optional[DeployPlan]:
        if len(deploy_plans) == 0:
            return None
        if len(deploy_plans) == 1:
            return deploy_plans[0]

        source = None

        for i in range(1, len(deploy_plans)):
            source = DeploymentPlanCalculator.merge(resolve_deploy_plan(deploy_plans[i-1]), resolve_deploy_plan(deploy_plans[i]))

        logging.debug(f"Merging plan details:\n{source}")
        logging.info(f"Writing deploy plan to {output_file}..")
        with open(output_file, "w") as f:
            f.write(yaml.dump(source.to_dict(), sort_keys=False))

        return source

def resolve_deploy_plan(deploy_plan: Union[DeployPlan, Path, str]) -> DeployPlan:
    if isinstance(deploy_plan, DeployPlan):
        return deploy_plan
    if utils.is_file_path(deploy_plan):
        with open(deploy_plan, "r") as f:
            deploy_plan = utils.load_json_or_yaml(f.read())
    return DeployPlan.from_dict(deploy_plan)


_FILTER_SEPARATOR_RE = re.compile(r"[;,\n ]+")


@dataclass
class Filter:
    include: set[str] = field(default_factory=set)
    exclude: set[str] = field(default_factory=set)

    def is_empty(self) -> bool:
        return not self.include and not self.exclude


def _parse_filter(value: str | None) -> Filter:
    """Parse a multi-value filter string into include/exclude sets.

    Tokens prefixed with ``!`` are treated as exclusions; all others as
    inclusions. Recognises semicolons, commas, newlines, and spaces as
    separators. An empty ``Filter`` (both sets empty) means *no filter*
    (accept everything).

    Examples::

        "core,ns"       → Filter(include={"core", "ns"})
        "!core"         → Filter(exclude={"core"})
        "core,!other"   → Filter(include={"core"}, exclude={"other"})
    """
    if not value:
        return Filter()
    include, exclude = set(), set()
    for token in _FILTER_SEPARATOR_RE.split(value):
        if not token:
            continue
        if token.startswith("!"):
            exclude.add(token[1:])
        else:
            include.add(token)
    return Filter(include=include, exclude=exclude)


_APPLICATION_SEPARATOR_RE = re.compile(r"[;,\n ]+")


def _split_application_list(value: str) -> list[str]:
    """Parse a multi-value applications string into an ordered list of app identifiers.

    Recognises semicolons, commas, newlines (including the literal ``\\n``
    CI systems sometimes send), and spaces as separators. Order is preserved
    since it drives wave-offset calculation.
    """
    value = value.replace("\\n", "\n")
    return [token for token in _APPLICATION_SEPARATOR_RE.split(value) if token]


def _matches_filter(value: str, f: Filter) -> bool:
    """Check whether *value* passes the filter.

    - Empty filter → accept all.
    - Include set non-empty → value must be in it.
    - Exclude set non-empty → value must not be in it.
    Both conditions apply simultaneously when both sets are non-empty.
    """
    if f.is_empty():
        return True
    if f.include and value not in f.include:
        return False
    if value in f.exclude:
        return False
    return True


def _apply_filters(
    plan: DeployPlan,
    deploy_postfix_filter: Filter,
    component_names_filter: Filter,
    wave_filter: Filter,
    namespace_filter: Filter,
) -> DeployPlan:
    """Return a new :class:`DeployPlan` containing only entities that pass all active filters.

    Every filter is *inclusive* by default; prefix a token with ``!`` to
    exclude it. An entity must pass **all** supplied filters to be retained.

    Args:
        plan: Source deployment plan.
        deploy_postfix_filter: Filter on ``deployPostfix`` values.
        component_names_filter: Filter on component names (prefix before ``:`` in version).
        wave_filter: Filter on wave numbers expressed as strings (e.g. ``{"0", "1"}``).
        namespace_filter: Filter on namespace values.

    Returns:
        Filtered :class:`DeployPlan` instance.
    """
    filtered: list[DeployPlanEntity] = [
        entity
        for entity in plan.entities
        if _matches_filter(entity.deploy_postfix, deploy_postfix_filter)
        and _matches_filter(entity.version.split(":", 1)[0], component_names_filter)
        and _matches_filter(str(entity.wave), wave_filter)
        and _matches_filter(entity.namespace, namespace_filter)
    ]
    return DeployPlan(entities=filtered)
