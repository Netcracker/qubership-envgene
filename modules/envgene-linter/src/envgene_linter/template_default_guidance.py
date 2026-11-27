"""Copyable, scoped template-default recipes for literal PLACE-12 candidates."""

from __future__ import annotations

import json
import re
from io import StringIO
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
        "3. These copies can be removed once the environments use a template that contains this ParameterSet:\n"
        + "\n".join(f"- {path}" for path in proposal.sources)
        + "\n\nKeep the references shown above. They select this ParameterSet after the file moves into the template."
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


_BINDING = {
    Category.DEPLOY: "deployParameterSets",
    Category.E2E: "e2eParameterSets",
    Category.TECHNICAL: "technicalConfigurationParameterSets",
}
_CATEGORY_TOKEN = {
    Category.DEPLOY: "deploy",
    Category.E2E: "pipeline",
    Category.TECHNICAL: "runtime",
}
# Substrings that often mark a site-specific address, account, or credential.
_CAUTION_TOKENS = (
    "url",
    "host",
    "user",
    "credential",
    "registry",
    "repo",
    "branch",
    "project",
)


def display_keys(entries: list, keys: list[str] | None = None) -> list[str]:
    if keys is not None:
        return list(keys)
    return [".".join(str(part) for part in path) for path, _ in entries]


def caution_keys(keys: list[str]) -> list[str]:
    found = []
    for key in keys:
        folded = key.casefold()
        if any(token in folded for token in _CAUTION_TOKENS):
            found.append(key)
    return found


def key_slug(key: str) -> str:
    return key.lower().replace("_", "-")


def _kebab(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "shared"


def attachment_phrase(scope: Scope) -> str:
    binding = _BINDING[scope.category]
    if scope.target == "cloud":
        return f"cloud.template_override.{binding} (Cloud)"
    return (
        f"namespaces[{scope.target}].template_override.{binding} "
        f'(Namespace "{scope.target}")'
    )


def parameter_set_base(template: str, scope: Scope, identity: tuple = ()) -> str:
    """Name stem before ``-shared``, without a colliding-key suffix."""
    pairs = [(item[0], item[1]) for item in identity if len(item) >= 2]
    suffixes = []
    env_specific = bool(pairs)
    for full_name, reference in pairs:
        prefix = str(full_name).replace("/", "-") + "-"
        if reference.startswith(prefix) and len(reference) > len(prefix):
            suffixes.append(reference[len(prefix) :])
        else:
            env_specific = False
            break
    if env_specific and len(set(suffixes)) == 1:
        return f"{template}-{suffixes[0]}"
    references = list(dict.fromkeys(reference for _, reference in pairs))
    if len(references) == 1:
        parts = [template, scope.target, references[0]]
        if scope.application:
            parts.append(_kebab(scope.application))
        return "-".join(parts)
    parts = [template, scope.target]
    if scope.application:
        parts.append(_kebab(scope.application))
    parts.append(_CATEGORY_TOKEN[scope.category])
    return "-".join(parts)


def assign_shared_name(
    base: str,
    keys: list[str],
    *,
    disambiguate: bool,
    used: set[str],
) -> str:
    stem = f"{base}-{key_slug(keys[0])}" if disambiguate and keys else base
    name = f"{stem}-shared"
    number = 2
    while name.casefold() in used:
        name = f"{stem}-{number}-shared"
        number += 1
    used.add(name.casefold())
    return name


def render_review_suggestion(
    template_name: str,
    artifact: str,
    scope: Scope,
    entries: list,
    shared_name: str,
    *,
    keys: list[str],
    agreed: int | None,
    exception_lines: tuple[str, ...] = (),
    application_note: str = "",
    destination: str | None = None,
    action: str = "create-name",
    step_note: str | None = None,
    conflicts: tuple[str, ...] = (),
    document: dict | None = None,
) -> str:
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
    body = document if document is not None else {"name": shared_name, **paramset}
    if agreed is None:
        updated = "the environments that share these values"
    else:
        noun = "environment" if agreed == 1 else "environments"
        updated = f"the {agreed} {noun}"
    same = "the same key" if len(keys) == 1 else f"the same {len(keys)} keys"
    application = (
        f" (inside application {scope.application})" if scope.application else ""
    )
    lines = [
        "REVIEW ONLY. Nothing is applied automatically.",
        "",
        "Check first (a person decides):",
        "1. Should every environment using this template get these values?",
        "2. Does any environment set one of them on purpose to be different?",
        "If unsure, stop. Nothing needs to change.",
    ]
    cautious = caution_keys(keys)
    if cautious:
        lines.append("Look twice at: " + ", ".join(cautious))
    lines.extend(["", "Steps:", ""])
    if action == "blocked":
        lines.append("1. Template repo: Template relocation proposal not generated.")
        if step_note:
            lines.append(f"   Review: {step_note}")
        if destination:
            lines.append(f"   File: {destination}")
    elif action == "keep":
        lines.append(
            f"1. Template repo: Reuse file: {destination}. "
            "It already has these keys. Leave the file unchanged."
        )
    elif action == "add":
        lines.append(
            f"1. Template repo: Merge into file: {destination}. "
            "Leave the other parameters as they are."
        )
        lines.append("")
        fragment = _yaml(_quoted(body))
        if str(destination).endswith(".json"):
            lines.append("ParameterSet JSON:")
            lines.append(
                json.dumps(
                    body,
                    ensure_ascii=False,
                    indent=2,
                    allow_nan=False,
                )
            )
        else:
            lines.append("ParameterSet YAML:")
            lines.append(fragment)
        lines.append("")
    else:
        if destination:
            lines.append(f"1. Template repo: Create file: {destination}")
            lines.append("")
            lines.append("ParameterSet YAML:")
            lines.append(_yaml(_quoted(body)))
            lines.append("")
        else:
            lines.append(f'1. Template repo: create ParameterSet "{shared_name}":')
            lines.append("")
            lines.append(_yaml(_quoted(body)))
            lines.append("")
    if conflicts:
        lines.extend(f"Conflict: {conflict}. Leave it in the instance." for conflict in conflicts)
    lines.append("")
    if action == "blocked":
        lines.append("2. Stop here. Fix the template input, then run the check again.")
        if exception_lines:
            lines.append("   Keep as they are:")
            lines.extend(f"   - {line}" for line in exception_lines)
    elif action == "keep":
        lines.append(
            step_note
            or f'2. Template repo: "{shared_name}" is already connected. Do not change the descriptor.'
        )
    elif step_note:
        lines.append(f"2. {step_note}")
    elif application_note:
        lines.append(
            "2. Template repo: the default Application object has no e2eParameters field. "
            f'Confirm renderer support before connecting "{shared_name}".'
        )
    elif action == "add":
        lines.append(
            f'2. Template repo: "{shared_name}" stays the ParameterSet name. '
            f'In "{template_name}", keep its current reference.'
        )
    else:
        lines.append(
            f'2. Template repo: in "{template_name}", add "{shared_name}" '
            f"to the end of {attachment_phrase(scope)}."
        )
    if action != "blocked":
        lines.extend(
            [
                "",
                f"3. Template repo: release a new version of {artifact} and update {updated} to it.",
                "   Do not continue until this is done, otherwise they lose these values.",
                "",
                f"4. Instance repo: delete {same} from the files listed above{application}.",
            ]
        )
        if exception_lines:
            lines.append("   Keep as they are:")
            lines.extend(f"   - {line}" for line in exception_lines)
        lines.extend(
            [
                "",
                "5. Instance repo: run envgene-linter check -i <instance> -t <template>.",
                "   This finding should be gone.",
            ]
        )
    return "\n".join(lines)


def local_parameter_set_path(context: TemplateContext, shared_name: str) -> str:
    return str(context.directory / "parameters" / f"{shared_name}.yml")


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
    keys: list[str] | None = None,
    agreed: int | None = None,
    exception_lines: tuple[str, ...] = (),
    shared_name: str | None = None,
) -> str:
    """Build a portable recipe or a scoped local template recipe."""
    application_note = (
        "The default EnvGene Application object has no e2eParameters field. Confirm renderer support."
        if scope.category is Category.E2E and scope.application is not None
        else ""
    )
    shown_keys = display_keys(entries, keys)
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
        chosen = shared_name or assign_shared_name(
            parameter_set_base(template_name, scope, identity),
            shown_keys,
            disambiguate=False,
            used=set(),
        )
        participant_count = agreed
        if participant_count is None and identity:
            participant_count = len({item[0] for item in identity if item})
        return render_review_suggestion(
            template_name,
            artifact,
            scope,
            entries,
            chosen,
            keys=shown_keys,
            agreed=participant_count,
            exception_lines=exception_lines,
            application_note=application_note,
        )
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
