"""Copyable, scoped template-default recipes for literal PLACE-12 candidates."""

from __future__ import annotations

import json
from io import StringIO
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.scalarbool import ScalarBoolean
from ruamel.yaml.scalarstring import DoubleQuotedScalarString

from .model import Category, Scope
from .paramset_merge import MergePlan, parameter_payload, selector
from .paramset_relocation import ParamsetRelocation
from .template_context import TemplateContext


def _quoted(value: Any) -> Any:
    if isinstance(value, str):
        return DoubleQuotedScalarString(value)
    if isinstance(value, (bool, ScalarBoolean)):
        return bool(value)
    if isinstance(value, int):
        return int(value)
    if isinstance(value, float):
        return float(value)
    if isinstance(value, dict):
        return {
            str(key) if isinstance(key, str) else _quoted(key): _quoted(child)
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [_quoted(child) for child in value]
    return value


def _yaml(value: dict) -> str:
    yaml = YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.default_flow_style = False
    stream = StringIO()
    yaml.dump(value, stream)
    return stream.getvalue().rstrip()


def _template_file(context: TemplateContext | None, relative: str) -> str:
    return str(context.directory.parent / relative) if context is not None else relative


def _yaml_selector(path: tuple[str | int, ...]) -> str:
    return "".join(
        f"[{part}]" if isinstance(part, int) else f".{part}" for part in path
    ).lstrip(".")


def build_relocation_hint(
    proposal: ParamsetRelocation,
    scope: Scope,
    *,
    context: TemplateContext,
    instance_root: Path,
) -> str:
    field = f"envTemplate.{scope.category.binding_field}.{scope.target}"
    bindings = "\n".join(
        f"- {environment}: {field} = {json.dumps(references, ensure_ascii=False)}"
        for environment, references in proposal.bindings
    )
    note = f"{proposal.version_note}\n\n" if proposal.version_note else ""
    return (
        "Whole ParameterSet transfer candidate.\n"
        "Template repository changes:\n"
        f"1. Create file: {_template_file(context, proposal.destination)}\n"
        "Keep the existing ParameterSet name. Create its parent directory if absent.\n\n"
        f"ParameterSet YAML:\n{_yaml(_quoted(proposal.payload))}\n\n"
        f"{note}"
        "2. Keep the existing Environment Inventory bindings and reference order.\n"
        f"Existing reference lists (no edits required):\n{bindings}\n\n"
        "No descriptor override is needed. Only environments selecting this reference use the ParameterSet.\n\n"
        "Instance repository changes:\n"
        "3. Publish the updated template artifact and update the participating environments before removing these copies:\n"
        + "\n".join(f"- {instance_root / path}" for path in proposal.sources)
        + "\n\nReview actual generation and other template consumers before removing source files.\n"
        "Local source comparison only. Published artifact equivalence remains unverified.\n"
        "INT-2 can retain Review for template-only references until their sources are resolved."
    )


def build_merge_hint(plan: MergePlan, context: TemplateContext) -> str:
    target = plan.target
    if target.reason:
        return (
            "Template relocation proposal not generated.\n"
            f"Review: {target.reason}\nExisting file: {target.path}"
        )
    text = "Template repository changes:\n"
    if target.attachment.selection_evidence:
        text += (
            "Resolved ParameterSet references:\n"
            + "\n".join("- " + value for value in target.attachment.selection_evidence)
            + "\n\n"
        )
    if plan.additions:
        payload = {
            "name": target.reference,
            **parameter_payload(plan.scope, plan.additions),
        }
        fragment = (
            "ParameterSet JSON:\n"
            + json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False)
            if target.path.suffix == ".json"
            else "ParameterSet YAML:\n" + _yaml(_quoted(payload))
        )
        text += (
            f"Merge into file: {target.path}\n"
            "Merge only the shown fields. Preserve other fields and values.\n"
            f"{fragment}\n\n"
        )
        if plan.scope.application is not None:
            text += (
                f"Match the application by appName/name {json.dumps(plan.scope.application)}. "
                "Merge its parameters, or append that application entry if absent. Keep other applications.\n\n"
            )
    elif plan.accepted:
        text += f"Reuse file: {target.path}\nThe shown common values are already present.\n\n"
    else:
        text += f"Review: no keys can be merged or reused in {target.path}.\n"
    for path, state in plan.states.items():
        if state == "conflict":
            text += (
                f"Conflict: {selector(('parameters', *path))}"
                + (
                    f" in application {json.dumps(plan.scope.application)}"
                    if plan.scope.application
                    else ""
                )
                + ". Keep the template and instance entries unchanged.\n"
            )
    if not plan.accepted:
        return text
    proposal = target.attachment
    if plan.original_binding:
        text += (
            "Keep the existing Environment Inventory bindings and reference order.\n"
        )
    elif proposal.reference_present:
        text += f"Keep the existing reference {json.dumps(target.reference)} in its current position.\n"
    else:
        field = next(
            iter(
                (
                    proposal.attachment["cloud"]
                    if plan.scope.target == "cloud"
                    else proposal.attachment["namespaces"][0]
                )["template_override"]
            )
        )
        text += (
            f"Edit file: {_template_file(context, proposal.descriptor)}"
            f":{proposal.entry_position[0]}:{proposal.entry_position[1]}\n"
            f"YAML path: {_yaml_selector(proposal.entry_path)}.template_override.{field}\n"
            f'Append "{target.reference}" as the last item. Keep existing references in their current order.\n'
            f"Descriptor YAML:\n{_yaml(_quoted(proposal.attachment))}\n\n"
        )
    return text


def _portable_template_hint(
    template_name: str, scope: Scope, paramset: dict, application_note: str
) -> str:
    shared_name = "<shared-paramset-name>"
    recipe = (
        "Proposed template changes (template repository not inspected):\n"
        "1. Add a shared ParameterSet to the template repository with these repeated values.\n"
        f'Replace "{shared_name}" with an unused ParameterSet name. '
        "Use the same name for the ParameterSet filename and reference.\n\n"
        f"ParameterSet YAML:\n{_yaml(_quoted({'name': shared_name, **paramset}))}\n\n"
    )
    if application_note:
        recipe += f"2. Confirm renderer support before connecting this ParameterSet.\n{application_note}\n\n"
    else:
        binding = {
            Category.DEPLOY: "deployParameterSets",
            Category.E2E: "e2eParameterSets",
            Category.TECHNICAL: "technicalConfigurationParameterSets",
        }[scope.category]
        association = (
            "Cloud association"
            if scope.target == "cloud"
            else f"Namespace association for {json.dumps(scope.target, ensure_ascii=False)}"
        )
        recipe += (
            f"2. In environment template {json.dumps(template_name, ensure_ascii=False)}, select the existing {association}.\n"
            f"Append the reference below as the last item in template_override.{binding}.\n"
            "Create template_override and this list if absent. Match the existing list's indentation.\n"
            "Keep the existing references in their current order and preserve other associations and override fields.\n"
        )
        if scope.target == "cloud":
            recipe += "If cloud is a path string, convert it to object form with the same value in template_path.\n"
        recipe += (
            f'\nReference item to append:\n- "{shared_name}"\n\n'
            "3. Publish the updated template artifact, update the participating environments, and verify generation.\n"
            "Then remove only the shown duplicate parameter entries from the instance ParameterSets.\n"
            "Keep other parameters and their existing ParameterSet references.\n\n"
        )
    return (
        recipe
        + "Keep intentional instance overrides and review template consumers before removing matching entries.\n"
        "Supply -t PATH (--template-repo PATH) for exact destination files and local source comparisons."
    )


def build_template_default_hint(
    template_name: str,
    artifact: str,
    scope: Scope,
    entries: list[tuple[tuple[str, ...], Any]],
    *,
    context: TemplateContext | None = None,
    identity: tuple = (),
    source_references: tuple[str, ...] = (),
    cleanup: str = "",
) -> str:
    """Build a portable recipe or a scoped local template recipe."""
    application_note = (
        "The default EnvGene Application object has no e2eParameters field. Confirm renderer support."
        if scope.category is Category.E2E and scope.application is not None
        else ""
    )
    parameters = {}
    for path, value in entries:
        target = parameters
        for part in path[:-1]:
            target = target.setdefault(part, {})
        target[path[-1]] = value
    paramset = {"parameters": parameters}
    if scope.application is not None:
        paramset = {
            "applications": [{"appName": scope.application, "parameters": parameters}]
        }
    if context is None:
        hint = _portable_template_hint(template_name, scope, paramset, application_note)
        return hint + (cleanup if not application_note else "")
    proposal = None
    if application_note:
        reason = application_note
    else:
        proposal = context.propose(
            template_name,
            artifact,
            scope,
            entries,
            identity=identity,
            source_references=source_references,
            participants=tuple(item[0] for item in identity),
        )
        reason = proposal.reason
    if proposal is None or proposal.attachment is None:
        location = (
            f"Local descriptor: {_template_file(context, proposal.descriptor)}.\n"
            if proposal and proposal.descriptor
            else ""
        )
        if proposal and proposal.entry_path:
            location += f"YAML entry: {_yaml_selector(proposal.entry_path)}\n"
        return (
            "Template relocation proposal not generated.\n"
            f"Shared instance values for {scope.target} / {scope.category.value} (observation only).\n"
            f"ParameterSet YAML:\n{_yaml(_quoted(paramset))}\n\n"
            f"{location}{reason}"
        )
    paramset = {"name": proposal.stem, **paramset}
    evidence = ""
    if proposal.selection_evidence:
        evidence += (
            "Resolved ParameterSet references:\n"
            + "\n".join("- " + value for value in proposal.selection_evidence)
            + "\n\n"
        )
    if proposal.definitions:
        evidence += (
            "Local source definitions (selection and final values unverified):\n"
            + "\n".join("- " + definition for definition in proposal.definitions)
            + "\n\n"
        )
    entry = (
        proposal.attachment["cloud"]
        if scope.target == "cloud"
        else proposal.attachment["namespaces"][0]
    )
    binding = next(iter(entry["template_override"]))
    location = (
        "existing cloud entry"
        if scope.target == "cloud"
        else f'existing namespaces entry for "{scope.target}"'
    )
    descriptor_file = _template_file(context, proposal.descriptor)
    if proposal.entry_position is not None:
        descriptor_file += f":{proposal.entry_position[0]}:{proposal.entry_position[1]}"
    selector = _yaml_selector(proposal.entry_path)
    return (
        "Template repository changes:\n"
        f"1. Create file: {_template_file(context, f'templates/parameters/{proposal.stem}.yml')}\n"
        "Create its parent directory if absent.\n\n"
        f"ParameterSet YAML:\n{_yaml(_quoted(paramset))}\n\n"
        f"2. Edit file: {descriptor_file}\n"
        f"Update the {location}.\n"
        f"YAML path: {selector}.template_override.{binding}\n"
        f'Append "{proposal.stem}" as the last item in template_override.{binding}.\n'
        "Create template_override and this list if absent.\n"
        "Merge the shown fields into this entry.\n"
        "Preserve other descriptor entries and override fields.\n"
        "Keep the order of existing references.\n\n"
        f"Descriptor YAML:\n{_yaml(_quoted(proposal.attachment))}\n\n"
        f"{evidence}{cleanup}"
    )
