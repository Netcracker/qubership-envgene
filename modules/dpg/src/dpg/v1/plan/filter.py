"""Deployment plan filtering command — include-only filter by postfix, component, wave, namespace."""

import re
import yaml

from qubership_pipelines_common_library.v1.execution.exec_command import ExecutionCommand

from dpg.v1.internal.deployment_plan import DeployPlan, DeployPlanEntity
import dpg.v1.utils as utils


_FILTER_SEPARATOR_RE = re.compile(r"[;,\n ]+")


def _parse_filter(value: str | None) -> set[str]:
    """Parse a multi-value filter string into a set of non-empty tokens.

    Recognises semicolons, commas, newlines, and spaces as separators so that
    callers can pass values in any of those forms.

    Args:
        value: Raw filter string from input params, or ``None``.

    Returns:
        Set of stripped, non-empty tokens.  An empty set means *no filter*
        (accept everything).
    """
    if not value:
        return set()
    return {token for token in _FILTER_SEPARATOR_RE.split(value) if token}


def _matches_filter(value: str, filter_set: set[str]) -> bool:
    """Check whether *value* passes an include-only filter.

    An empty *filter_set* means the filter is disabled and every value is
    accepted.

    Args:
        value: The entity attribute to test.
        filter_set: Allowed values.  Empty means *accept all*.

    Returns:
        ``True`` when the value should be retained.
    """
    return not filter_set or value in filter_set


def _apply_filters(
    plan: DeployPlan,
    deploy_postfix_filter: set[str],
    component_names_filter: set[str],
    wave_filter: set[str],
    namespace_filter: set[str],
) -> DeployPlan:
    """Return a new :class:`DeployPlan` containing only entities that pass all active filters.

    Every filter is *inclusive*: an entity must match **all** supplied filters
    to be retained.  Omitting a filter (empty set) means that dimension is
    not constrained.

    Args:
        plan: Source deployment plan.
        deploy_postfix_filter: Allowed ``deployPostfix`` values.
        component_names_filter: Allowed component names (prefix before ``:`` in version).
        wave_filter: Allowed wave numbers expressed as strings (e.g. ``{"0", "1"}``).
        namespace_filter: Allowed namespace values.

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


class PlanDeploymentFilter(ExecutionCommand):
    """Filter a deployment plan with include-only rules.

    Reads a deployment plan from ``params.deployment_plan`` (file path or
    inline list), applies up to four independent include filters, and writes
    the result to an output YAML file.

    Mandatory params:
        params.deployment_plan: Path to a YAML/JSON file containing the plan list,
            or an inline list value forwarded from a previous pipeline step.

    Optional params:
        params.output_file: Destination file path (default: ``deployplan.yaml``).
        params.deploy_postfix_filter: Allowed ``deployPostfix`` values.
        params.component_names_filter: Allowed component names (part before ``:`` in version).
        params.wave_filter: Allowed wave numbers (e.g. ``0;1`` or ``0,1``).
        params.namespace_filter: Allowed namespace values.

    Output params:
        params.output_file: Filtered plan as a list (forwarded to next steps).
    """

    _DEFAULT_OUTPUT_FILE = "deploy-plan.yaml"

    def _validate(self) -> bool:
        if not self.context.validate([]):
            return False

        self._deployment_plan_input = self.context.input_param_get("params.deployment_plan", self._DEFAULT_OUTPUT_FILE)
        self._output_file = self.context.input_param_get("params.output_file", self._DEFAULT_OUTPUT_FILE)

        self._deploy_postfix_filter = _parse_filter(
            self.context.input_param_get("params.deploy_postfix_filter")
        )
        self._component_names_filter = _parse_filter(
            self.context.input_param_get("params.component_names_filter")
        )
        self._wave_filter = _parse_filter(
            self.context.input_param_get("params.wave_filter")
        )
        self._namespace_filter = _parse_filter(
            self.context.input_param_get("params.namespace_filter")
        )
        return True

    def _execute(self) -> None:
        raw = self._deployment_plan_input
        if utils.is_file_path(raw):
            with open(raw, "r") as f:
                raw = utils.load_json_or_yaml(f.read())
        deploy_plan = DeployPlan.from_dict(raw)
        self.context.logger.info(f"Input plan details:\n{deploy_plan}")

        self.context.logger.debug(
            f"Active filters — "
            f"deploy_postfix: {self._deploy_postfix_filter or 'none'}, "
            f"component_names: {self._component_names_filter or 'none'}, "
            f"wave: {self._wave_filter or 'none'}, "
            f"namespace: {self._namespace_filter or 'none'}"
        )

        filtered_plan = _apply_filters(
            deploy_plan,
            deploy_postfix_filter=self._deploy_postfix_filter,
            component_names_filter=self._component_names_filter,
            wave_filter=self._wave_filter,
            namespace_filter=self._namespace_filter,
        )

        before, after = len(deploy_plan.entities), len(filtered_plan.entities)
        self.context.logger.info(f"Filtering complete: {before} → {after} application(s) retained")
        self.context.logger.debug(f"Filtered plan details:\n{filtered_plan}")

        self.context.logger.info(f"Writing deploy plan to {self._output_file}..")
        with open(self._output_file, "w") as f:
            f.write(yaml.dump(filtered_plan.to_dict(), sort_keys=False))

        self.context.output_param_set("params.deployment_plan", filtered_plan.to_dict())
        self.context.output_params_save()
