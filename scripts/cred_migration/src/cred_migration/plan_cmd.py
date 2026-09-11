"""Plan-generation orchestration.

Walks the repo, classifies cred entries per tier, runs shadow-platform heuristics, detects
orphaned Shared cred files, and composes the migration-plan.yaml structure.
"""

import re
from pathlib import Path

import yaml

from .classifier import Tier, build_signals, classify_tier_by_source_file
from .file_scanner import (
    find_consumer_files_instance,
    find_consumer_files_template,
    find_deployer_cred_files,
    find_generated_env_credentials,
    find_source_cred_files_instance,
    find_source_cred_files_template,
)
from .orphan_detector import collect_declared_from_cred_file, collect_referenced_from_consumer
from .plan_yaml import build_cred_entry, build_plan, build_source_group
from .template_scanner import (
    list_descriptors,
    list_env_template_solutions,
    scan_descriptor_creds,
    scan_parameters_creds,
    scan_solution_consumer_creds,
)


# ---- Tier default composition ----

_ENV_TIER_JINJA_DEFAULT = (
    "{{ current_env.cloud }}/{{ current_env.name }}/{{ current_env.namespace }}"
)
_PASSPORT_TIER_JINJA_DEFAULT = "{{ current_env.cloud }}"

_PASSPORT_CANDIDATE_SUGGESTION = (
    "looks like a Cloud Passport cred - value comes from Cloud Passport in the Instance repo. "
    "Remove from this plan if so. Keep only if EnvGene should manage this cluster-wide cred."
)


def _generate_template_plan(repo_root, generated_at):
    """Template-repo plan generator.

    Per Template Descriptor (`templates/env_templates/<name>.yaml`):
    - Trace descriptor → referenced templates (tenant, cloud, namespaces, composite_structure).
    - Walk each template for cred macros + follow deployParameterSets/e2eParameterSets refs.
    - Resolve paramset names to files via inner `name:` field, then scan those.
    - `technicalConfigurationParameterSets` is skipped (Assumption 5).
    - Emit one group per descriptor, sourceFile = `templates/external-credentials/<stem>.yml.j2`.
    """
    repo_root = Path(repo_root)
    credentials = []
    for descriptor_path in list_descriptors(repo_root):
        cred_template = (
            repo_root / "templates" / "external-credentials" / f"{descriptor_path.stem}.yml.j2"
        )
        rel_source = str(cred_template.relative_to(repo_root))

        discovered = scan_descriptor_creds(
            descriptor_path=descriptor_path, repo_root=repo_root
        )
        existing_ids = set()
        if cred_template.exists():
            try:
                existing_yaml = yaml.safe_load(cred_template.read_text()) or {}
                existing_ids = set(existing_yaml.keys())
            except yaml.YAMLError:
                existing_ids = set()
        all_cred_ids = existing_ids | set(discovered.keys())
        if not all_cred_ids:
            continue

        to_review = {}
        to_confirm = {}
        for cred_id in sorted(all_cred_ids):
            signals = build_signals(cred_id=cred_id, comment=None)
            if signals:
                # Shadow-platform match: use passport-tier defaults + explanatory suggestion.
                entry = build_cred_entry(
                    remote_ref_path=_PASSPORT_TIER_JINJA_DEFAULT,
                    create=False,
                    write_to_store=None,
                    suggestions=[_PASSPORT_CANDIDATE_SUGGESTION],
                )
                to_review[cred_id] = entry
            else:
                entry = build_cred_entry(
                    remote_ref_path=_ENV_TIER_JINJA_DEFAULT,
                    create=True,
                    write_to_store=None,
                    suggestions=None,
                )
                to_confirm[cred_id] = entry
        credentials.append(build_source_group(rel_source, to_review, to_confirm))

    return build_plan(
        repo_type="template",
        generated_at=generated_at,
        credentials=credentials,
        to_delete={},
    )


def compute_tier_defaults(tier, cluster, env, namespace):
    """Compose default remoteRefPath + create per tier, per Credential types section."""
    if tier == Tier.PASSPORT.value:
        return {"remote_ref_path": f"/{cluster}", "create": False}
    if tier == Tier.ENV.value:
        parts = [p for p in (cluster, env, namespace) if p]
        return {"remote_ref_path": "/" + "/".join(parts), "create": True}
    if tier == Tier.EXTERNAL.value:
        return {"remote_ref_path": "/external", "create": False}
    raise ValueError(f"unknown tier {tier!r}")


# ---- Path parsing for tier context ----

_INSTANCE_ENV_SCOPE_RE = re.compile(
    r"^environments/(?P<cluster>[^/]+)/(?P<env>[^/]+)/Inventory/credentials/"
)
_INSTANCE_CLUSTER_SCOPE_RE = re.compile(
    r"^environments/(?P<cluster>[^/]+)/(?:cloud-passport|credentials)/"
)


def _parse_scope(source_file_rel):
    """Extract cluster/env context from a repo-relative source file path (best-effort)."""
    m = _INSTANCE_ENV_SCOPE_RE.match(source_file_rel)
    if m:
        return m.group("cluster"), m.group("env")
    m = _INSTANCE_CLUSTER_SCOPE_RE.match(source_file_rel)
    if m:
        return m.group("cluster"), None
    return None, None


# ---- Suggestion generation ----

def _make_suggestion(tier, cluster):
    """Suggestion text for entries in to_review with shadow-platform signals."""
    if cluster:
        return (
            f"if platform-shared: set remoteRefPath to /{cluster} and create=false "
            "(promotes to passport-tier shape)"
        )
    return "if platform-shared: set remoteRefPath to /<cluster> and create=false"


# ---- Main plan builder ----

def generate_plan(repo_root, repo_type, generated_at, namespace_placeholder="<ns>"):
    """Walk the repo, classify creds, detect orphans, return the plan dict."""
    repo_root = Path(repo_root)

    if repo_type == "template":
        return _generate_template_plan(repo_root, generated_at)

    source_files = find_source_cred_files_instance(repo_root)
    consumer_files = find_consumer_files_instance(repo_root)

    # Collect referenced cred-ids across all consumers (used for orphan detection).
    referenced = set()
    for cfile in consumer_files:
        try:
            consumer_yaml = yaml.safe_load(cfile.read_text()) or {}
        except yaml.YAMLError:
            continue
        referenced |= collect_referenced_from_consumer(consumer_yaml)

    # Build per-source-file groups.
    credentials = []
    declared_by_file = {}
    for src in source_files:
        rel = str(src.relative_to(repo_root))
        try:
            cred_yaml = yaml.safe_load(src.read_text()) or {}
        except yaml.YAMLError:
            cred_yaml = {}
        declared_by_file[rel] = collect_declared_from_cred_file(cred_yaml)

        tier = classify_tier_by_source_file(rel).value
        cluster, env = _parse_scope(rel)
        # env-tier defaults need placeholder for namespace (unknown at authoring time).
        defaults = compute_tier_defaults(tier, cluster, env, namespace_placeholder if tier == Tier.ENV.value else None)

        to_review = {}
        to_confirm = {}
        for cred_id in cred_yaml:
            signals = build_signals(cred_id=cred_id, comment=None)
            entry = build_cred_entry(
                remote_ref_path=defaults["remote_ref_path"],
                create=defaults["create"],
                write_to_store=True if repo_type == "instance" else None,
                suggestions=[_make_suggestion(tier, cluster)] if signals else None,
            )
            if signals:
                to_review[cred_id] = entry
            else:
                to_confirm[cred_id] = entry
        credentials.append(build_source_group(rel, to_review, to_confirm))

    # to_delete groups (instance repo only for now).
    to_delete = {}
    if repo_type == "instance":
        gen = [str(p.relative_to(repo_root)) for p in find_generated_env_credentials(repo_root)]
        if gen:
            to_delete["generated_env_credentials"] = gen
        dep = [str(p.relative_to(repo_root)) for p in find_deployer_cred_files(repo_root)]
        if dep:
            to_delete["deployer_credentials"] = dep
        # Orphaned Shared cred files: declared cred-ids never referenced anywhere.
        # Only consider repo/cluster-scoped Shared files (env-scoped are always env-tier - kept).
        orphan_candidates = {
            rel: ids for rel, ids in declared_by_file.items()
            if rel.startswith("environments/credentials/")
            or re.match(r"^environments/[^/]+/credentials/", rel)
        }
        from .orphan_detector import compute_orphaned_files
        orphans = sorted(compute_orphaned_files(orphan_candidates, referenced))
        if orphans:
            to_delete["unused_shared_credentials"] = orphans

    return build_plan(
        repo_type=repo_type,
        generated_at=generated_at,
        credentials=credentials,
        to_delete=to_delete,
    )
