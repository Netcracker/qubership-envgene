"""PLACE-12: conservative review of shared template-default candidates."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import replace
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
from ..instance_cleanup import cleanup_hint
from ..paramset_merge import MergePlanner, selector as _merge_selector
from ..paramset_relocation import propose_relocation
from ..paramset_sources import resolve_reference
from ..passport import Catalogs, resolve_passport
from ..security_values import is_secret_parameter_name, literal_name
from ..template_context import TemplateContext
from ..yamlio import plain
from ..template_default_guidance import (
    assign_shared_name,
    attachment_phrase,
    local_parameter_set_path,
    parameter_set_base,
    render_review_suggestion,
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


def _agreement_floor(count: int) -> int:
    """Shared values needed: all but at most floor(N/4) participants."""
    return count - count // 4


def _application_note(scope: Scope) -> str:
    if scope.category.value == "e2e" and scope.application is not None:
        return (
            "The default EnvGene Application object has no e2eParameters field. "
            "Confirm renderer support."
        )
    return ""


def _review(
    template: str,
    artifact: str,
    scope: Scope,
    entries: list,
    shared_name: str,
    keys: list[str],
    agreed: int,
    exception_lines: tuple[str, ...],
    *,
    roots: tuple[str, str] | None = None,
    **extra,
) -> str:
    text = render_review_suggestion(
        template,
        artifact,
        scope,
        entries,
        shared_name,
        keys=keys,
        agreed=agreed,
        exception_lines=exception_lines,
        application_note=_application_note(scope),
        **extra,
    )
    if roots:
        instance, template_root = roots
        text = (
            f"Instance repository: {instance}\n"
            f"Template repository: {template_root}\n\n" + text
        )
    return text


def _review_lines(index, scope: Scope, entries) -> str:
    return "\n".join(
        line
        for line in cleanup_hint(index, scope, entries).splitlines()
        if line.startswith("Cleanup Review:")
    )


def _splice_reviews(hint: str, reviews: str) -> str:
    if not reviews:
        return hint
    block = "\n".join(f"   {line}" for line in reviews.splitlines())
    marker = "\n5. Instance repo:"
    if marker in hint:
        return hint.replace(marker, "\n" + block + marker, 1)
    return f"{hint}\n{block}"


def _conflict_labels(plan, scope: Scope) -> tuple[str, ...]:
    labels = []
    for path, state in plan.states.items():
        if state != "conflict":
            continue
        label = _merge_selector(("parameters", *path))
        if scope.application:
            label += f" in application {scope.application}"
        labels.append(label)
    return tuple(labels)


def _exception_line(env: EnvModel, key: str, leaf: EffectiveLeaf | None) -> str:
    if leaf is None:
        return f"{env.full_name}: {key} is absent"
    if not _literal(leaf.value):
        return f"{env.full_name}: {key} = a different value"
    shown = json.dumps(plain(leaf.value), ensure_ascii=False)
    return f"{env.full_name}: {key} = {shown}"


def _candidate(
    index: RepoIndex,
    participants: list[EnvModel],
    scope: Scope,
    path: tuple,
    full: dict[str, EnvEffective],
    catalogs: Catalogs,
) -> tuple[list[tuple[EnvModel, EffectiveLeaf]], tuple[str, ...]]:
    if not path or not all(isinstance(part, str) for part in path):
        return [], ()
    if any(not _literal(part) or is_secret_parameter_name(part) for part in path):
        return [], ()
    if not _literal(scope.target) or (
        scope.application is not None and not _literal(scope.application)
    ):
        return [], ()
    if any(path[0] in catalogs.env[env.full_name] for env in participants):
        return [], ()
    observed = [
        (env, full[env.full_name].scopes.get(scope, {}).get(path))
        for env in participants
    ]
    groups: list[list[tuple[EnvModel, EffectiveLeaf]]] = []
    for env, leaf in observed:
        if leaf is None:
            continue
        for group in groups:
            if equal(group[0][1].value, leaf.value) is True:
                group.append((env, leaf))
                break
        else:
            groups.append([(env, leaf)])
    floor = _agreement_floor(len(participants))
    winners = [group for group in groups if len(group) >= floor]
    if len(winners) != 1:
        return [], ()
    owners = winners[0]
    first = owners[0][1].value
    if not _literal(first):
        return [], ()
    identifiers = {
        name for env in participants for name in (env.cluster, env.name, env.full_name)
    }
    if isinstance(first, str) and first in identifiers:
        return [], ()
    if any(
        not _owned_source(index, env, leaf) or not _raw_literal(leaf)
        for env, leaf in owners
    ):
        return [], ()
    sources = {
        (leaf.provenance.file.path.resolve(), leaf.provenance.yaml_path)
        for _, leaf in owners
    }
    if len(sources) < 2:
        return [], ()
    agreed = {env.full_name for env, _ in owners}
    key = owners[0][1].key
    exceptions = tuple(
        _exception_line(env, key, leaf)
        for env, leaf in observed
        if env.full_name not in agreed
    )
    return owners, exceptions


def check(
    index: RepoIndex,
    full: dict[str, EnvEffective],
    catalogs: Catalogs,
    template_repo: Path | None = None,
) -> list[Finding]:
    context = (
        TemplateContext(template_repo, index=index)
        if template_repo is not None
        else None
    )
    planner = MergePlanner(context) if context is not None else None
    pending = []
    portable = []
    moves = []
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
            paths = set()
            for env in participants:
                paths |= set(full[env.full_name].scopes.get(scope, {}))
            candidates = defaultdict(list)
            for path in sorted(paths, key=lambda item: tuple(map(str, item))):
                owners, exceptions = _candidate(
                    index, participants, scope, path, full, catalogs
                )
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
                    candidates[identity].append((path, owners, exceptions))
            for identity, entries in candidates.items():
                locations = {}
                for _, owners, _exceptions in entries:
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
                keys = [owners[0][1].key for _, owners, _exceptions in entries]
                references = sorted(
                    {leaf.provenance.reference for _, leaf in entries[0][1]}
                )
                source_description = ", ".join(
                    repr(reference) for reference in references
                )
                count = len(entries)
                exception_lines = tuple(
                    line for _, _owners, lines in entries for line in lines
                )
                agreed = len(entries[0][1])
                environment_count = (
                    f"{agreed} of {len(participants)}"
                    if exception_lines
                    else str(len(participants))
                )
                comparable = [
                    (path, owners) for path, owners, _exceptions in entries
                ]
                merge = (
                    planner.propose(
                        name,
                        scope,
                        [(path, owners[0][1].value) for path, owners in comparable],
                        tuple(references),
                        participants=tuple(env.full_name for env, _ in comparable[0][1]),
                    )
                    if planner
                    else None
                )
                relocation = (
                    None
                    if merge or exception_lines
                    else propose_relocation(
                        index, name, artifact_name, scope, comparable, context
                    )
                )
                shown_entries = [
                    (path, owners[0][1].value) for path, owners in comparable
                ]
                hint = ""
                reviews = (
                    _review_lines(index, scope, comparable) if context is not None else ""
                )
                if merge is not None:
                    pending.append(
                        (
                            len(findings),
                            merge,
                            scope,
                            shown_entries,
                            keys,
                            agreed,
                            exception_lines,
                            name,
                            artifact_name,
                            reviews,
                        )
                    )
                elif relocation is not None:
                    moves.append(
                        (
                            len(findings),
                            relocation,
                            scope,
                            shown_entries,
                            keys,
                            agreed,
                            exception_lines,
                            name,
                            artifact_name,
                            reviews,
                        )
                    )
                else:
                    portable.append(
                        (
                            len(findings),
                            {
                                "template": name,
                                "artifact": artifact_name,
                                "scope": scope,
                                "entries": shown_entries,
                                "identity": identity,
                                "keys": keys,
                                "agreed": agreed,
                                "exception_lines": exception_lines,
                                "local": context is not None,
                                "source_references": all_references,
                                "reviews": reviews,
                            },
                        )
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
                            f"with the same values in {environment_count} environments "
                            f"using template {name!r} from {artifact_name!r}."
                        ),
                        hint=hint,
                        related=tuple(
                            f"{env.full_name} (artifact {env.template_identity[1]!r}): "
                            f"{leaf.key}: {leaf.provenance.describe()}"
                            for _, owners, _exceptions in entries
                            for env, leaf in owners
                        ),
                    )
                )
    roots = None
    if context is not None:
        roots = (str(index.root.absolute()), str(context.directory.parent))
    # Names that would collide get the first parameter in the stem, including the first group.
    bases = [
        parameter_set_base(data["template"], data["scope"], data["identity"])
        for _, data in portable
    ]
    repeats = {
        base for base in bases if bases.count(base) > 1
    }
    used_names: set[str] = set()
    for (number, data), base in zip(portable, bases):
        shared = assign_shared_name(
            base,
            data["keys"],
            disambiguate=base in repeats,
            used=used_names,
        )
        extra = {}
        if data["local"] and context is not None:
            extra["destination"] = local_parameter_set_path(context, shared)
            extra["roots"] = roots
            if not _application_note(data["scope"]):
                proposal = context.propose(
                    data["template"],
                    data["artifact"],
                    data["scope"],
                    data["entries"],
                    identity=data["identity"],
                    source_references=data["source_references"],
                    participants=tuple(item[0] for item in data["identity"]),
                )
                if proposal is not None and proposal.reason:
                    extra["action"] = "blocked"
                    extra.pop("destination", None)
                    extra["step_note"] = proposal.reason
                elif proposal is not None:
                    note = (
                        f'In "{data["template"]}", add "{shared}" to the end of '
                        f"{attachment_phrase(data['scope'])}."
                    )
                    if proposal.descriptor:
                        descriptor = context.directory.parent / proposal.descriptor
                        note += f" Descriptor: {descriptor}."
                    if proposal.selection_evidence:
                        resolved = "; ".join(proposal.selection_evidence)
                        note += f" Resolved ParameterSet references: {resolved}."
                    extra["step_note"] = note
        findings[number] = replace(
            findings[number],
            hint=_splice_reviews(
                _review(
                    data["template"],
                    data["artifact"],
                    data["scope"],
                    data["entries"],
                    shared,
                    data["keys"],
                    data["agreed"],
                    data["exception_lines"],
                    **extra,
                ),
                data["reviews"],
            ),
        )
    for (
        number,
        relocation,
        scope,
        entries,
        keys,
        agreed,
        exception_lines,
        template_name,
        artifact_name,
        reviews,
    ) in moves:
        note = (
            "Whole ParameterSet transfer candidate. "
            "Keep the existing Environment Inventory bindings and reference order. "
            f'They already select "{relocation.reference}".'
        )
        if relocation.version_note:
            note = f"{note} {relocation.version_note}"
        findings[number] = replace(
            findings[number],
            hint=_splice_reviews(
                _review(
                    template_name,
                    artifact_name,
                    scope,
                    entries,
                    relocation.reference,
                    keys,
                    agreed,
                    exception_lines,
                    destination=str(context.directory.parent / relocation.destination),
                    roots=(str(index.root.absolute()), str(context.directory.parent)),
                    step_note=note,
                    document=relocation.payload,
                ),
                reviews,
            ),
        )
    for (
        number,
        merge,
        scope,
        entries,
        keys,
        agreed,
        exception_lines,
        template_name,
        artifact_name,
        reviews,
    ) in pending:
        target = merge.target
        conflicts = _conflict_labels(merge, scope)
        if target.reason:
            hint = _review(
                template_name,
                artifact_name,
                scope,
                [],
                target.reference,
                keys,
                agreed,
                exception_lines,
                destination=str(target.path),
                action="blocked",
                step_note=target.reason,
                conflicts=conflicts,
                roots=roots,
            )
        elif merge.additions:
            if merge.original_binding or (
                target.attachment is not None and target.attachment.reference_present
            ):
                note = (
                    "Keep the existing Environment Inventory bindings and reference order."
                    if merge.original_binding
                    else f'Keep the existing reference "{target.reference}" in its current position.'
                )
            else:
                note = (
                    f'In "{template_name}", add "{target.reference}" to the end of '
                    f"{attachment_phrase(scope)}."
                )
                if target.attachment is not None and target.attachment.descriptor:
                    descriptor = context.directory.parent / target.attachment.descriptor
                    note += f" Descriptor: {descriptor}."
            moved = [
                key
                for key, (path, _value) in zip(keys, entries)
                if merge.states.get(path) in {"add", "reuse"}
            ]
            hint = _review(
                template_name,
                artifact_name,
                scope,
                merge.additions,
                target.reference,
                moved or keys,
                agreed,
                exception_lines,
                destination=str(target.path),
                action="add",
                step_note=note,
                conflicts=conflicts,
                roots=roots,
            )
        elif merge.accepted:
            hint = _review(
                template_name,
                artifact_name,
                scope,
                entries,
                target.reference,
                keys,
                agreed,
                exception_lines,
                destination=str(target.path),
                action="keep",
                conflicts=conflicts,
                roots=roots,
            )
        else:
            hint = _review(
                template_name,
                artifact_name,
                scope,
                [],
                target.reference,
                keys,
                agreed,
                exception_lines,
                destination=str(target.path),
                action="blocked",
                step_note="These keys differ from the template file.",
                conflicts=conflicts,
                roots=roots,
            )
        findings[number] = replace(
            findings[number], hint=_splice_reviews(hint, reviews)
        )
    return findings
