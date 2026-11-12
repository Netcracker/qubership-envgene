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
        "Publication and later instance cleanup:\n"
        "3. Publish the updated template artifact and update the participating environments before removing these copies:\n"
        + "\n".join(f"- {instance_root / path}" for path in proposal.sources)
        + "\n\nReview actual generation and other template consumers before removing source files.\n"
        "Local source comparison only. Published artifact equivalence remains unverified.\n"
        "INT-2 can retain Review for template-only references until their sources are resolved."
    )


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
        return _portable_template_hint(template_name, scope, paramset, application_note)
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
            f"Shared values for {scope.target} / {scope.category.value}.\n"
            f"ParameterSet YAML:\n{_yaml(_quoted(paramset))}\n\n"
            f"{location}{reason}\n"
            "Review all template consumers before removing instance overrides."
        )
    paramset = {"name": proposal.stem, **paramset}
    evidence = ""
    if proposal.definitions:
        evidence = (
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
        f"{evidence}"
        "Later ParameterSets override earlier values.\n"
        "Environment-specific ParameterSets are applied afterwards and keep priority.\n"
        "Review before removing matching instance entries. Keep their existing ParameterSet references for other overrides.\n"
        "Local source comparison only: artifact equivalence, Jinja output, and all template consumers remain unverified."
    )
