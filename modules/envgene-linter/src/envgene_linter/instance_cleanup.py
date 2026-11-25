"""Grouped instance cleanup instructions for confirmed portions of a proposal."""

from collections import defaultdict
from pathlib import Path

from .paramset_merge import selector
from .paramset_sources import resolve_reference


def cleanup_hint(index, scope, entries, accepted=None) -> str:
    removed: dict[Path, set[tuple]] = {}
    documents = {}
    blocked = set()
    owners = {env.full_name for _, values in entries for env, _ in values}
    safe_sources = {}
    for path, values in entries:
        if accepted is not None and path not in accepted:
            continue
        for _, leaf in values:
            file = leaf.provenance.file
            physical = file.path.resolve()
            if physical not in safe_sources:
                safe_sources[physical] = all(
                    env.full_name in owners
                    and category is scope.category
                    and target == scope.target
                    for env in index.environments
                    for category, targets in env.bindings.items()
                    for target, references in targets.items()
                    for reference in references
                    for selected in resolve_reference(
                        index, env, reference, include_unavailable=True
                    )
                    if selected.file.path.resolve() == physical
                )
            position = file.loaded.exact_position(leaf.provenance.yaml_path)
            if not safe_sources[physical] or position is None:
                blocked.add(physical)
                continue
            removed.setdefault(physical, set()).add(leaf.provenance.yaml_path)
            documents[physical] = file.loaded.doc
    review = "".join(
        "\nCleanup Review: inspect other consumers or anchored entries in "
        f"{_relative(index, path)} before removing keys."
        for path in sorted(blocked, key=lambda item: _relative(index, item))
    )
    if not removed:
        return review
    return (
        "\n\nInstance repository changes:\n"
        + _render_groups(index, removed, documents)
        + review
    )


def _relative(index, path: Path) -> str:
    try:
        return path.resolve().relative_to(index.root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _at(doc, path: tuple):
    node = doc
    for part in path:
        if isinstance(node, dict) and part in node:
            node = node[part]
        elif isinstance(node, list) and isinstance(part, int) and 0 <= part < len(node):
            node = node[part]
        else:
            return None
    return node


def _rollup(paths: set[tuple], doc) -> set[tuple]:
    current = set(paths)
    if doc is None:
        return current
    changed = True
    while changed:
        changed = False
        for parent in {path[:-1] for path in current if path}:
            if _parameters_container(parent):
                continue
            node = _at(doc, parent)
            if isinstance(node, dict):
                expected = {parent + (key,) for key in node}
            elif isinstance(node, list):
                expected = {parent + (index,) for index in range(len(node))}
            else:
                continue
            if expected and expected <= current:
                current.difference_update(expected)
                current.add(parent)
                changed = True
                break
    return current


def _parameters_container(path: tuple) -> bool:
    if path == ("parameters",):
        return True
    return (
        len(path) == 3
        and path[0] == "applications"
        and isinstance(path[1], int)
        and path[2] == "parameters"
    )


def _whole_parameter(path: tuple) -> bool:
    if path[:1] == ("parameters",) and len(path) <= 2:
        return True
    return (
        len(path) >= 3
        and path[0] == "applications"
        and isinstance(path[1], int)
        and path[2] == "parameters"
        and len(path) <= 4
    )


def _render_groups(index, removed: dict[Path, set[tuple]], documents) -> str:
    groups: dict[tuple[tuple, ...], list[Path]] = defaultdict(list)
    for physical, paths in removed.items():
        rolled = tuple(sorted(_rollup(paths, documents.get(physical)), key=selector))
        groups[rolled].append(physical)
    blocks = []
    ordered = sorted(
        groups.items(),
        key=lambda item: _relative(index, min(item[1], key=lambda path: _relative(index, path))),
    )
    for paths, files in ordered:
        whole = [selector(path) for path in paths if _whole_parameter(path)]
        partial = [selector(path) for path in paths if not _whole_parameter(path)]
        lines = ["Files:"]
        lines.extend(
            f"- {_relative(index, path)}"
            for path in sorted(files, key=lambda path: _relative(index, path))
        )
        lines.extend([
            "",
            "Remove the keys below from the files above. "
            "Keep other parameters and their existing ParameterSet references.",
        ])
        if whole:
            lines.extend(["", "Remove the whole key:", *(f"- {item}" for item in whole)])
        if partial:
            lines.extend([
                "",
                "Remove only these fields; keep the rest of the key:",
                *(f"- {item}" for item in partial),
            ])
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)
