"""Review complete instance ParameterSets for relocation with their bindings intact."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ruamel.yaml.scalarbool import ScalarBoolean

from .model import Category, Layer, RepoIndex, Scope
from .paramset_sources import resolve_reference
from .template_context import TemplateContext
from .yaml_values import equal
from .yamlio import leaves, plain


@dataclass(frozen=True)
class ParamsetRelocation:
    reference: str
    destination: str
    payload: dict[str, Any]
    sources: tuple[str, ...]
    bindings: tuple[tuple[str, tuple[str, ...]], ...]
    version_note: str = ""


def propose_relocation(
    index: RepoIndex,
    template_name: str,
    artifact_name: str,
    scope: Scope,
    entries: list,
    context: TemplateContext | None,
) -> ParamsetRelocation | None:
    if context is None or not entries:
        return None
    owners = entries[0][1]
    references = {leaf.provenance.reference for _, leaf in owners}
    if len(references) != 1 or len(owners) < 2:
        return None
    reference = next(iter(references))
    documents, payloads, paths = [], [], []
    for env, leaf in owners:
        if env.template_identity is None or any(
            selector != env.template_identity[1] for selector in env.artifact_selectors
        ):
            return None
        source = leaf.provenance.file
        selected = resolve_reference(index, env, reference, include_unavailable=True)
        if (
            source.layer is not Layer.ENVIRONMENT
            or len(selected) != 1
            or selected[0].file.path.resolve() != source.path.resolve()
            or source.loaded is None
        ):
            return None
        doc = source.loaded.doc
        if (
            doc.get("name") != reference
            or source.stem != reference
            or set(doc) - {"name", "version", "parameters", "applications"}
            or ("parameters" in doc and not isinstance(doc["parameters"], dict))
            or ("applications" in doc and not isinstance(doc["applications"], list))
            or any(
                set(app) - {"appName", "name", "parameters"}
                for app in doc.get("applications", []) or []
            )
            or (scope.category is Category.E2E and source.applications)
        ):
            return None
        containers = [(("parameters",), source.parameters)]
        containers.extend(
            (("applications", number, "parameters"), parameters)
            for number, _, parameters in source.applications
        )
        expected = {
            (*container, *path)
            for container, parameters in containers
            for path, _ in leaves(parameters)
        }
        covered = {
            value.provenance.yaml_path
            for _, values in entries
            for participant, value in values
            if participant.full_name == env.full_name
            and value.provenance.file.path.resolve() == source.path.resolve()
        }
        if not expected or expected != covered:
            return None
        payload = {"name": reference, "parameters": plain(source.parameters)}
        if doc.get("applications"):
            payload["applications"] = plain(doc["applications"])
        documents.append(doc)
        payloads.append(payload)
        paths.append(source.path)
    if len({path.resolve() for path in paths}) != len(owners) or any(
        equal(payloads[0], payload) is not True for payload in payloads[1:]
    ):
        return None
    participants = {env.full_name for env, _ in owners}
    physical_sources = {path.resolve() for path in paths}
    for env in index.environments:
        selectors = set(env.artifact_selectors)
        if env.template_identity is not None:
            selectors.add(env.template_identity[1])
        affected_artifact = any(
            selector.split(":", 1)[0] == artifact_name for selector in selectors
        )
        for category, targets in env.bindings.items():
            for target, bound in targets.items():
                for other_reference in bound:
                    expected_binding = (
                        env.full_name in participants
                        and category is scope.category
                        and target == scope.target
                        and other_reference == reference
                    )
                    if expected_binding:
                        continue
                    if other_reference == reference and affected_artifact:
                        return None
                    for selected in resolve_reference(
                        index, env, other_reference, include_unavailable=True
                    ):
                        try:
                            physical = selected.file.path.resolve()
                        except (OSError, RuntimeError):
                            continue
                        if physical in physical_sources:
                            return None
    destination = context.relocation_destination(
        template_name,
        scope,
        reference,
        participants=tuple(env.full_name for env, _ in owners),
    )
    if destination is None:
        return None
    payload = payloads[0]
    versions = [doc.get("version") for doc in documents]
    note = ""
    if any(version is not None for version in versions):
        if all(
            isinstance(version, (int, float))
            and not isinstance(version, (bool, ScalarBoolean))
            for version in versions
        ) and all(equal(versions[0], version) is True for version in versions):
            payload["version"] = versions[0]
        else:
            note = "Source version fields differ or are not numeric. The proposed file omits the deprecated version field."
    return ParamsetRelocation(
        reference=reference,
        destination=destination,
        payload=payload,
        sources=tuple(
            sorted(path.relative_to(index.root).as_posix() for path in paths)
        ),
        bindings=tuple(
            (env.full_name, tuple(env.bound_targets(scope.category)[scope.target]))
            for env, _ in owners
        ),
        version_note=note,
    )
