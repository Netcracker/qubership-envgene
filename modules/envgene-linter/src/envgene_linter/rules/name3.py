"""NAME-3: filenames, directories, and namespaces use kebab-case."""

from __future__ import annotations

import re
from pathlib import Path

from ..connections import Connections, PROFILE_DIRS, compute_connections, resolve_named_reference
from ..discovery import ENV_DEFINITION_FILE, INVENTORY_DIR, paramset_stem
from ..model import Finding, Location, RepoIndex, Severity
from ..rulemeta import RULES

_KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_FILE_SUFFIXES = (".yml.j2", ".yaml.j2", ".json.j2", ".yml", ".yaml", ".json")
_DIRECTORY_KINDS = frozenset(
    {"Cluster directory", "Environment directory", "Namespace"}
)
_LAYOUT_DIRECTORIES = frozenset(
    {
        "Inventory",
        "Namespaces",
        "parameters",
        "credentials",
        "Credentials",
        "resource_profiles",
        "rp_override",
        "Profiles",
        "configuration",
        "configurations",
        "shared-template-variables",
        "shared_template_variables",
        "cloud-passport",
        "cloud-passports",
        "app-deployer",
        "cloud-deployer",
    }
)
_HINT = (
    "Review whether this name can be kebab-case. "
    "Do not rename it if generation or other logic still depends on the current spelling."
)


def check(index: RepoIndex, connections: Connections | None = None) -> list[Finding]:
    connections = connections or compute_connections(index)
    findings: list[Finding] = []
    files = {path: path for path in connections.selected_paths}
    # Naming uses the selected record, never an unrelated alias of its target.
    for physical, file in connections.parameter_files.items():
        files[physical] = file.path

    targets: dict[str, set[str]] = {}
    for uses in connections.parameter_uses.values():
        for use in uses:
            targets.setdefault(use.environment, set()).add(use.target)
    for cluster in index.clusters.values():
        if not cluster.environments:
            continue
        _maybe(findings, cluster.name, "Cluster directory", cluster.path)
        for env in cluster.environments:
            _maybe(findings, env.name, "Environment directory", env.path)
            definition = env.path / INVENTORY_DIR / ENV_DEFINITION_FILE
            if definition.is_file():
                files[definition.resolve()] = definition
            used_targets = set(targets.get(env.full_name, ()))
            for target, reference in env.resource_profile_bindings.items():
                if resolve_named_reference(
                    index, env, reference, index.resource_profiles, PROFILE_DIRS
                ):
                    used_targets.add(target)
            ns_root = env.path / "Namespaces"
            for target in sorted(used_targets):
                child = ns_root / target
                if (
                    target.lower() != "cloud"
                    and target not in {".", ".."}
                    and target == child.name
                    and child.parent == ns_root
                    and child.is_dir()
                    and child.resolve().is_relative_to(index.root)
                ):
                    _maybe(findings, target, "Namespace", child)
    environments = index.root / "environments"
    for path in sorted(files.values()):
        if (
            path.is_relative_to(environments)
            and path.resolve().is_relative_to(index.root)
            and ".git" not in path.relative_to(environments).parts
            and path.name.endswith(_FILE_SUFFIXES)
        ):
            _maybe(findings, paramset_stem(path), "File", path)
    findings.sort(key=lambda item: (item.path.as_posix(), item.key, item.line))
    return findings


def _maybe(findings: list[Finding], name: str, kind: str, path: Path) -> None:
    if kind in _DIRECTORY_KINDS and (
        name in _LAYOUT_DIRECTORIES or ".git" in path.parts
    ):
        return
    if _KEBAB.fullmatch(name):
        return
    findings.append(_finding(name, kind, path))


def _finding(name: str, kind: str, path: Path) -> Finding:
    meta = RULES["NAME-3"]
    return Finding(
        rule="NAME-3",
        severity=Severity.INFORMATION,
        path=path,
        line=1,
        column=1,
        issue_type=meta.default_issue_type,
        action=meta.default_action,
        key=name,
        scope=kind,
        message=f"{kind} {name!r} is not kebab-case.",
        hint=_HINT,
        related=(),
        locations=(Location(path, 1, 1),),
    )
