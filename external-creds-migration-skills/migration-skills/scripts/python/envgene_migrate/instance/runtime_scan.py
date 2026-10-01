"""Scan Instance consumer YAML for runtime credential macros."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .macros import collect_runtime_macro_hits
from .yaml_io import open_yaml


def _env_consumer_files(repo: Path, scope: tuple[str, str] | None) -> list[Path]:
    """YAML files that may contain technicalConfigurationParameters."""
    env_root = repo / "environments"
    out: list[Path] = []

    # Unrestricted-mode consumers from apply._consumer_files — keep in sync.
    for pattern in (
        "environments/**/cloud-passport/*.yml",
        "environments/**/cloud-passport/*.yaml",
        "configuration/integration.yml",
        "configuration/registry.yml",
        "configuration/deployer.yml",
        "environments/**/app-deployer/deployer.yml",
    ):
        for p in repo.glob(pattern):
            if not p.is_file():
                continue
            if p.name.endswith("-creds.yml") or p.name.endswith("-creds.yaml"):
                continue
            out.append(p)

    if not env_root.is_dir():
        return out
    clusters = sorted(p for p in env_root.iterdir() if p.is_dir())
    if scope:
        clusters = [env_root / scope[0]]
    for cluster in clusters:
        if not cluster.is_dir():
            continue
        env_dirs = sorted(p for p in cluster.iterdir() if p.is_dir())
        if scope:
            env_dirs = [cluster / scope[1]]
        for env_dir in env_dirs:
            if env_dir.name in ("credentials", "cloud-passport", "parameters"):
                continue
            for name in ("cloud.yml", "cloud.yaml", "tenant.yml", "tenant.yaml"):
                p = env_dir / name
                if p.is_file():
                    out.append(p)
            # Namespaces/ are regenerated from Template on env-gen — out of Instance
            # migration scope (neither apply rewrite nor runtime GATE scan).
    return out


def scan_instance_runtime_macros(
    repo_root: Path, *, env_filter: str | None = None
) -> list[dict[str, Any]]:
    scope = None
    if env_filter:
        parts = env_filter.replace("\\", "/").strip().split("/")
        if len(parts) == 2:
            scope = (parts[0], parts[1])
    hits: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for path in _env_consumer_files(Path(repo_root), scope):
        data = open_yaml(path)
        if data is None:
            continue
        rel = str(path.relative_to(repo_root)).replace("\\", "/")
        for row in collect_runtime_macro_hits(data, file_path=rel):
            key = (row["file"], row["credId"])
            if key in seen:
                continue
            seen.add(key)
            hits.append(row)
    return sorted(hits, key=lambda r: (r["file"], r["credId"]))
