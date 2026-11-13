"""Located instance cleanup instructions for confirmed portions of a proposal."""

from .paramset_merge import selector
from .paramset_sources import resolve_reference


def cleanup_hint(index, scope, entries, accepted=None) -> str:
    records, blocked = set(), set()
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
                blocked.add(str(file.path))
                continue
            records.add(
                (str(file.path), *position, selector(leaf.provenance.yaml_path))
            )
    review = "".join(
        f"\nCleanup Review: inspect other consumers or anchored entries in {path} before removing keys."
        for path in sorted(blocked)
    )
    if not records:
        return review
    return (
        "\n\nInstance repository changes:\n"
        "Publish the updated template artifact, update the participating environments, and verify generation.\n"
        "Then remove only these entries. Keep other parameters and their existing ParameterSet references:\n"
        + "\n".join(
            f"- {file}:{line}:{column}\n  Remove YAML path: {path}"
            for file, line, column, path in sorted(records)
        )
        + review
    )
