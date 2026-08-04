"""Smart Calculator CLI mock for BDD tests.

Implements the validation rules that the real Java Calculator CLI enforces:
  1. deployPostfix matching: each entry in deploy-plan.yml must resolve to an existing Namespace folder.
  2. Cross-level references: Cloud cannot reference Namespace params; Tenant cannot reference Cloud/Namespace.
  3. Cross-context references: deployParameters / e2eParameters / technicalConfigurationParameters
     cannot reference each other within the same object.

On success writes minimal topology+pipeline stubs to --output so the pipeline considers ES done.
"""
import os
import re
import sys
from pathlib import Path

import yaml

PARAM_TYPES = ("deployParameters", "e2eParameters", "technicalConfigurationParameters")
MACRO_RE = re.compile(r"\$\{([^}]+)\}")


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _load_deploy_plan(env_dir: Path) -> list:
    dp_path = env_dir / "Inventory" / "deploy-plan.yml"
    if not dp_path.exists():
        return []
    with open(dp_path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or []
    return data if isinstance(data, list) else []


def _get_namespace_folders(env_dir: Path) -> set:
    ns_dir = env_dir / "Namespaces"
    if not ns_dir.exists():
        return set()
    return {p.name for p in ns_dir.iterdir() if p.is_dir()}


def _get_bg_domain(env_dir: Path) -> dict:
    return _load_yaml(env_dir / "bg_domain.yml")


def _collect_params(yaml_data: dict) -> dict:
    result = {}
    for pt in PARAM_TYPES:
        for k, v in (yaml_data.get(pt) or {}).items():
            result[k] = (v, pt)
    return result


# ── Validation 1: deployPostfix ───────────────────────────────────────────────

def check_deploy_postfix(env_dir: Path) -> list:
    entries = _load_deploy_plan(env_dir)
    ns_folders = _get_namespace_folders(env_dir)
    bg = _get_bg_domain(env_dir)
    origin_ns = (bg.get("originNamespace") or {}).get("name", "")
    peer_ns = (bg.get("peerNamespace") or {}).get("name", "")

    unmatched = []
    for entry in entries:
        dp = entry.get("deployPostfix") or entry.get("namespace", "")
        if dp in ns_folders:
            continue
        if origin_ns and (dp + "-origin") == origin_ns and origin_ns in ns_folders:
            continue
        if peer_ns and (dp + "-peer") == peer_ns and peer_ns in ns_folders:
            continue
        unmatched.append(dp)

    if unmatched:
        joined = ", ".join(f'"{u}"' for u in unmatched)
        return [f"Cannot find Namespace folder in Environment Instance for deployPostfix: {joined}"]
    return []


# ── Validation 2: cross-level references ─────────────────────────────────────

def check_cross_level(env_dir: Path, tenant: dict, cloud: dict) -> list:
    cloud_params = _collect_params(cloud)
    ns_all_params: dict = {}
    ns_dir = env_dir / "Namespaces"
    for ns_path in (ns_dir.iterdir() if ns_dir.exists() else []):
        if ns_path.is_dir():
            ns_yaml = _load_yaml(ns_path / "namespace.yml")
            ns_all_params.update(_collect_params(ns_yaml))

    errors = []
    cloud_name = cloud.get("name", "cloud")
    tenant_name = tenant.get("name", "tenant")

    for pt in PARAM_TYPES:
        for k, v in (cloud.get(pt) or {}).items():
            if not isinstance(v, str):
                continue
            for ref in MACRO_RE.findall(v):
                if ref in ns_all_params:
                    errors.append(
                        f"Invalid parameter reference '${{{ref}}}' in Cloud '{cloud_name}': "
                        f"Cloud level parameters cannot reference Namespace level parameters"
                    )

    for pt in PARAM_TYPES:
        for k, v in (tenant.get(pt) or {}).items():
            if not isinstance(v, str):
                continue
            for ref in MACRO_RE.findall(v):
                if ref in cloud_params:
                    errors.append(
                        f"Invalid parameter reference '${{{ref}}}' in Tenant '{tenant_name}': "
                        f"Tenant level parameters cannot reference Cloud level parameters"
                    )
                elif ref in ns_all_params:
                    errors.append(
                        f"Invalid parameter reference '${{{ref}}}' in Tenant '{tenant_name}': "
                        f"Tenant level parameters cannot reference Namespace level parameters"
                    )

    return errors


# ── Validation 3: cross-context references ───────────────────────────────────

def check_cross_context(entity_name: str, yaml_data: dict) -> list:
    errors = []
    for src_type in PARAM_TYPES:
        for k, v in (yaml_data.get(src_type) or {}).items():
            if not isinstance(v, str):
                continue
            for ref in MACRO_RE.findall(v):
                for dst_type in PARAM_TYPES:
                    if dst_type == src_type:
                        continue
                    if ref in (yaml_data.get(dst_type) or {}):
                        errors.append(
                            f"Invalid parameter reference '${{{ref}}}' in {entity_name}: "
                            f"Parameters in '{src_type}' cannot reference parameters from '{dst_type}'"
                        )
    return errors


# ── Output: write minimal effective-set stubs ─────────────────────────────────

def write_effective_set(output_dir: Path) -> None:
    for ctx in ("topology", "pipeline"):
        d = output_dir / ctx
        d.mkdir(parents=True, exist_ok=True)
        (d / "parameters.yaml").write_text("{}\n", encoding="utf-8")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    args = sys.argv[1:]
    ci_project_dir = os.environ.get("CI_PROJECT_DIR", "")

    def _resolve(s: str) -> str:
        return s.replace("$CI_PROJECT_DIR", ci_project_dir)

    env_id = next((a.split("=", 1)[1] for a in args if a.startswith("--env-id=")), "")
    envs_path = _resolve(next((a.split("=", 1)[1] for a in args if a.startswith("--envs-path=")), ""))
    output = _resolve(next((a.split("=", 1)[1] for a in args if a.startswith("--output=")), ""))

    if not env_id or not envs_path:
        print("ERROR: missing --env-id or --envs-path", file=sys.stderr)
        sys.exit(1)

    cluster, env = env_id.split("/", 1)
    env_dir = Path(envs_path) / cluster / env

    # 1. deployPostfix matching
    dp_errors = check_deploy_postfix(env_dir)
    if dp_errors:
        for e in dp_errors:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    # 2. Load tenant / cloud
    tenant = _load_yaml(env_dir / "tenant.yml")
    cloud = _load_yaml(env_dir / "cloud.yml")

    # 3. Cross-level references
    level_errors = check_cross_level(env_dir, tenant, cloud)
    if level_errors:
        for e in level_errors:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    # 4. Cross-context references
    ctx_errors: list = []
    ctx_errors.extend(check_cross_context(f"Tenant '{tenant.get('name', 'tenant')}'", tenant))
    ctx_errors.extend(check_cross_context(f"Cloud '{cloud.get('name', 'cloud')}'", cloud))
    ns_dir = env_dir / "Namespaces"
    for ns_path in (ns_dir.iterdir() if ns_dir.exists() else []):
        if ns_path.is_dir():
            ns_yml = _load_yaml(ns_path / "namespace.yml")
            ctx_errors.extend(check_cross_context(f"Namespace '{ns_path.name}'", ns_yml))
    if ctx_errors:
        for e in ctx_errors:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    # 5. Write effective-set output stubs
    if output:
        write_effective_set(Path(output))

    print("Calculator CLI mock: validation passed, effective set written.")


if __name__ == "__main__":
    main()
