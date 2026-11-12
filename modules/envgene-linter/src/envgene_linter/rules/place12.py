"""PLACE-12: conservative review of shared template-default candidates."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from ..diagnostics import skip_check
from ..effective import EffectiveLeaf, EnvEffective
from ..model import (
    Action,
    EnvModel,
    Finding,
    IssueType,
    Layer,
    Location,
    ParamsetFile,
    RepoIndex,
    Scope,
    Severity,
)
from ..paramset_relocation import propose_relocation
from ..paramset_sources import resolve_reference
from ..passport import Catalogs, resolve_passport
from ..security_values import is_secret_parameter_name, literal_name
from ..template_context import TemplateContext
from ..template_default_guidance import (
    build_relocation_hint,
    build_template_default_hint,
)
from ..yaml_values import equal

RULE = "PLACE-12"


def _tagged(value: Any) -> bool:
    return getattr(getattr(value, "tag", None), "value", None) is not None


def _literal(value: Any) -> bool:
    if equal(value, value) is not True:
        return False
    pending, seen = [value], set()
    for _ in range(20000):
        if not pending:
            return True
        node = pending.pop()
        if node is None or _tagged(node):
            return False
        if isinstance(node, str):
            if any(
                marker in node
                for marker in (
                    "${",
                    "{{",
                    "{%",
                    "{#",
                    "ENC[",
                    "[encrypted:",
                    "envgen.creds.",
                )
            ):
                return False
        elif isinstance(node, (dict, list)):
            if id(node) in seen:
                return False
            seen.add(id(node))
            if isinstance(node, dict):
                if any(
                    isinstance(key, str) and is_secret_parameter_name(key)
                    for key in node
                ):
                    return False
                pending.extend(node)
                pending.extend(node.values())
            else:
                pending.extend(node)
    return False


def _raw_literal(leaf: EffectiveLeaf) -> bool:
    loaded = leaf.provenance.file.loaded
    if loaded is None:
        return False
    value = loaded.doc
    try:
        for part in leaf.provenance.yaml_path:
            if _tagged(value):
                return False
            value = value[part]
    except (KeyError, IndexError, TypeError):
        return False
    return _literal(value)


def _cluster(index: RepoIndex, env: EnvModel) -> Path | None:
    try:
        return index.clusters[env.cluster].path.resolve()
    except (OSError, RuntimeError):
        return None


def _owned_source(index: RepoIndex, env: EnvModel, leaf: EffectiveLeaf) -> bool:
    if leaf.provenance.layer is Layer.REPOSITORY:
        return False
    try:
        source = leaf.provenance.file.path.resolve()
        cluster = _cluster(index, env)
        repository = (index.root / "environments/parameters").resolve()
        return (
            cluster is not None
            and source.is_relative_to(cluster)
            and not source.is_relative_to(repository)
        )
    except (OSError, RuntimeError):
        return False


def _available(file: ParamsetFile) -> bool:
    if file.error or file.is_jinja or file.unavailable or file.loaded is None:
        return False
    doc = file.loaded.doc
    if not isinstance(doc, dict) or _tagged(doc):
        return False
    parameters, applications = doc.get("parameters"), doc.get("applications")
    if parameters is not None and (
        not isinstance(parameters, dict) or _tagged(parameters)
    ):
        return False
    if applications is None:
        return True
    if not isinstance(applications, list) or _tagged(applications):
        return False
    return all(
        isinstance(app, dict)
        and not _tagged(app)
        and literal_name(app.get("appName") or app.get("name"))
        and isinstance(app.get("parameters"), dict)
        and not _tagged(app["parameters"])
        for app in applications
    )


def _complete(
    index: RepoIndex, env: EnvModel, full: dict[str, EnvEffective], catalogs: Catalogs
) -> bool:
    reason = (
        None
        if env.parameter_bindings_complete
        else "ParameterSet binding membership is invalid or dynamic"
    )
    if env.full_name not in full or env.full_name not in catalogs.env:
        reason = "effective parameter or passport context is unavailable"
    for targets in env.bindings.values():
        for references in targets.values():
            for reference in references:
                entries = resolve_reference(
                    index, env, reference, include_unavailable=True
                )
                if not entries or any(not _available(entry.file) for entry in entries):
                    reason = "selected ParameterSet input is unavailable, invalid, or unrendered"
    passport = resolve_passport(index, env)
    selected = passport.file
    if passport.note or (
        selected is not None
        and (
            selected.error
            or selected.is_jinja
            or selected.loaded is None
            or not isinstance(selected.loaded.doc, dict)
            or _tagged(selected.loaded.doc)
        )
    ):
        reason = "selected Cloud Passport input is missing, ambiguous, unavailable, or unrendered"
    if reason:
        skip_check(index, RULE, env.path / "Inventory/env_definition.yml", reason)
    return reason is None


def _candidate(
    index: RepoIndex,
    participants: list[EnvModel],
    scope: Scope,
    path: tuple,
    full: dict[str, EnvEffective],
    catalogs: Catalogs,
) -> list[tuple[EnvModel, EffectiveLeaf]]:
    if not path or not all(isinstance(part, str) for part in path):
        return []
    if any(not _literal(part) or is_secret_parameter_name(part) for part in path):
        return []
    if not _literal(scope.target) or (
        scope.application is not None and not _literal(scope.application)
    ):
        return []
    if any(path[0] in catalogs.env[env.full_name] for env in participants):
        return []
    owners = [
        (env, full[env.full_name].scopes.get(scope, {}).get(path))
        for env in participants
    ]
    if any(leaf is None for _, leaf in owners):
        return []
    first = owners[0][1].value
    if not _literal(first) or any(
        equal(first, leaf.value) is not True for _, leaf in owners
    ):
        return []
    identifiers = {
        name for env in participants for name in (env.cluster, env.name, env.full_name)
    }
    if isinstance(first, str) and first in identifiers:
        return []
    if any(
        not _owned_source(index, env, leaf) or not _raw_literal(leaf)
        for env, leaf in owners
    ):
        return []
    sources = {
        (leaf.provenance.file.path.resolve(), leaf.provenance.yaml_path)
        for _, leaf in owners
    }
    return owners if len(sources) >= 2 else []


def check(
    index: RepoIndex,
    full: dict[str, EnvEffective],
    catalogs: Catalogs,
    template_repo: Path | None = None,
) -> list[Finding]:
    context = TemplateContext(template_repo) if template_repo is not None else None
    all_references = tuple(
        sorted(
            {
                reference
                for env in index.environments
                for targets in env.bindings.values()
                for values in targets.values()
                for reference in values
            }
        )
    )
    groups = defaultdict(list)
    for env in sorted(index.environments, key=lambda item: item.full_name):
        if env.template_identity is not None:
            name, reference = env.template_identity
            artifact_name = reference.split(":", 1)[0]
            if artifact_name.strip():
                groups[name, artifact_name].append(env)
    findings = []
    for (name, artifact_name), environments in sorted(groups.items()):
        if len(environments) < 2:
            continue
        complete = [_complete(index, env, full, catalogs) for env in environments]
        if not all(complete):
            continue
        scopes = {scope for env in environments for scope in full[env.full_name].scopes}
        for scope in sorted(
            scopes,
            key=lambda item: (item.target, item.category.value, item.application or ""),
        ):
            participants = [
                env
                for env in environments
                if env.bound_targets(scope.category).get(scope.target)
            ]
            if len(participants) < 2:
                continue
            paths = set(full[participants[0].full_name].scopes.get(scope, {}))
            for env in participants[1:]:
                paths &= set(full[env.full_name].scopes.get(scope, {}))
            candidates = defaultdict(list)
            for path in sorted(paths, key=lambda item: tuple(map(str, item))):
                owners = _candidate(index, participants, scope, path, full, catalogs)
                if owners:
                    # Preserve original selected references and physical source membership.
                    identity = tuple(
                        (
                            env.full_name,
                            leaf.provenance.reference,
                            leaf.provenance.file.path.resolve(),
                        )
                        for env, leaf in owners
                    )
                    candidates[identity].append((path, owners))
            for identity, entries in candidates.items():
                locations = {}
                for _, owners in entries:
                    for _, leaf in owners:
                        line, column = leaf.provenance.position
                        source = leaf.provenance.file.path
                        locations.setdefault(
                            (source.resolve(), line, column),
                            Location(source, line, column),
                        )
                ordered = tuple(
                    sorted(
                        locations.values(),
                        key=lambda item: (item.path.as_posix(), item.line, item.column),
                    )
                )
                primary = ordered[0]
                keys = [owners[0][1].key for _, owners in entries]
                references = sorted(
                    {leaf.provenance.reference for _, leaf in entries[0][1]}
                )
                source_description = ", ".join(
                    repr(reference) for reference in references
                )
                count = len(entries)
                relocation = propose_relocation(
                    index, name, artifact_name, scope, entries, context
                )
                hint = (
                    build_relocation_hint(
                        relocation, scope, context=context, instance_root=index.root
                    )
                    if relocation is not None
                    else build_template_default_hint(
                        name,
                        artifact_name,
                        scope,
                        [(path, owners[0][1].value) for path, owners in entries],
                        context=context,
                        identity=identity,
                        source_references=all_references,
                    )
                )
                if context is not None:
                    hint = (
                        f"Instance repository: {index.root.absolute()}\n"
                        f"Template repository: {context.directory.parent}\n\n" + hint
                    )
                findings.append(
                    Finding(
                        rule=RULE,
                        severity=Severity.INFORMATION,
                        issue_type=IssueType.INFORMATION,
                        action=Action.REVIEW,
                        path=primary.path,
                        line=primary.line,
                        column=primary.column,
                        key=keys[0] if count == 1 else ", ".join(keys),
                        scope=f"template {name} {artifact_name} {scope}",
                        locations=ordered,
                        message=(
                            f"ParameterSet {source_description} contains {count} shared parameter{'s' if count != 1 else ''} "
                            f"with the same values in {len(participants)} environments "
                            f"using template {name!r} from {artifact_name!r}."
                        ),
                        hint=hint,
                        related=tuple(
                            f"{env.full_name} (artifact {env.template_identity[1]!r}): "
                            f"{leaf.key}: {leaf.provenance.describe()}"
                            for _, owners in entries
                            for env, leaf in owners
                        ),
                    )
                )
    return findings
