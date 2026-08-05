"""Apply orchestration: turns a migration-plan.yaml into Store writes + Git rewrites.

Depends on external-cred-provision CLI (injected as cli_runner in tests, subprocess in prod).
"""

import os
import subprocess
import tempfile
from pathlib import Path

import yaml

from .cli_output import parse_cli_log
from .context_from_plan import build_context_from_repo
from .macro_rewrite import CompositeMacroError, rewrite_dict
from .plan_yaml import load_plan
from .pre_flight import (
    PreFlightError,
    check_git_clean,
    check_single_store,
    check_store_auth_env,
)
from .source_rewriter import rewrite_source_entry
from .template_scanner import scan_descriptor_creds

# envgeneNullValue placeholder cannot be written to a Store.
_NULL_MARKER = "envgeneNullValue"

# YAML blocks eligible for macro rewrite (deployParameters + e2eParameters, plus ParameterSet
# top-level `parameters` + `applications[].parameters`). technicalConfigurationParameters is
# excluded per Assumption 5.
_REWRITE_BLOCKS = ("deployParameters", "e2eParameters", "parameters")


def _iter_plan_entries(plan):
    """Yield (source_file_rel, cred_id, plan_entry) tuples across to_review + to_confirm."""
    for group in plan.get("credentials", []):
        source_file = group["sourceFile"]
        for section in ("to_review", "to_confirm"):
            for cred_id, entry in (group.get(section) or {}).items():
                yield source_file, cred_id, entry


# ---- Source file rewrite ----

def rewrite_source_files(plan, repo_root, successful_cred_ids):
    """For each successfully-migrated cred, rewrite its source entry to type:external in Git."""
    repo_root = Path(repo_root)
    # Group plan entries by source file for one write per file.
    by_source = {}
    for source_file, cred_id, entry in _iter_plan_entries(plan):
        if cred_id not in successful_cred_ids:
            continue
        by_source.setdefault(source_file, {})[cred_id] = entry

    for source_file, entries in by_source.items():
        path = repo_root / source_file
        source_yaml = yaml.safe_load(path.read_text()) or {}
        for cred_id, plan_entry in entries.items():
            if cred_id in source_yaml:
                source_yaml[cred_id] = rewrite_source_entry(source_yaml[cred_id], plan_entry)
        path.write_text(
            yaml.safe_dump(source_yaml, sort_keys=False, default_flow_style=False, allow_unicode=True)
        )


# ---- Consumer file rewrite ----

def rewrite_consumer_file(path):
    """Walk a consumer YAML, rewrite macros in supported blocks, skip technicalConfigurationParameters."""
    consumer_yaml = yaml.safe_load(Path(path).read_text()) or {}
    changed = _rewrite_node(consumer_yaml)
    if changed:
        Path(path).write_text(
            yaml.safe_dump(consumer_yaml, sort_keys=False, default_flow_style=False, allow_unicode=True)
        )


def _rewrite_node(node, in_rewrite_scope=False):
    """Recursively find and rewrite macro-carrying dicts.

    A rewrite happens ONLY when we descend through a key listed in _REWRITE_BLOCKS - that block
    becomes the local scope in which macros are converted. technicalConfigurationParameters (and
    its children) are never entered.
    """
    changed = False
    if isinstance(node, dict):
        for key, value in list(node.items()):
            if key == "technicalConfigurationParameters":
                continue  # skip entirely
            if key in _REWRITE_BLOCKS and isinstance(value, dict):
                try:
                    new_dict = rewrite_dict(value)
                except CompositeMacroError:
                    raise  # propagate; apply-level handler translates to error report
                if new_dict != value:
                    node[key] = new_dict
                    changed = True
            else:
                if _rewrite_node(value, in_rewrite_scope):
                    changed = True
    elif isinstance(node, list):
        for item in node:
            if _rewrite_node(item, in_rewrite_scope):
                changed = True
    return changed


# ---- Deletion ----

def create_or_update_credential_template(cred_template_path, cred_entries_from_plan, descriptor_path):
    """Create/update Credential Template with type:external entries.

    For each cred-id in plan: infer type from existing file (if present) or from descriptor-scan
    (transitive template + paramset walk). Emit entry with remoteRefPath + create + properties.
    """
    cred_template_path = Path(cred_template_path)
    existing = {}
    if cred_template_path.exists():
        existing = yaml.safe_load(cred_template_path.read_text()) or {}

    inferred_types = {}
    if descriptor_path is not None:
        inferred_types = scan_descriptor_creds(
            descriptor_path=descriptor_path,
            repo_root=cred_template_path.parents[2],  # templates/external-credentials/<file>
        )

    output = dict(existing)
    for cred_id, plan_entry in cred_entries_from_plan.items():
        cred_type = existing.get(cred_id, {}).get("type") or inferred_types.get(cred_id) or "secret"
        entry = {
            "type": "external",
            "remoteRefPath": plan_entry["remoteRefPath"],
            "create": plan_entry.get("create", False),
        }
        if cred_type == "usernamePassword":
            entry["properties"] = [{"name": "username"}, {"name": "password"}]
        output[cred_id] = entry

    cred_template_path.parent.mkdir(parents=True, exist_ok=True)
    cred_template_path.write_text(
        yaml.safe_dump(output, sort_keys=False, default_flow_style=False, allow_unicode=True)
    )


def update_template_descriptor(descriptor_path, cred_template_rel_path):
    """Add `external_credential_template` field to a Template Descriptor YAML if missing."""
    descriptor_path = Path(descriptor_path)
    if not descriptor_path.exists():
        return
    desc = yaml.safe_load(descriptor_path.read_text()) or {}
    if "external_credential_template" in desc:
        return
    desc["external_credential_template"] = f"{{{{ templates_dir }}}}/{cred_template_rel_path}"
    descriptor_path.write_text(
        yaml.safe_dump(desc, sort_keys=False, default_flow_style=False, allow_unicode=True)
    )


def _find_template_descriptor(repo_root, solution_dir):
    """Find `<solution>.yaml` (or .yml) sibling of the solution dir. Legacy — unused."""
    repo_root = Path(repo_root)
    solution_dir = Path(solution_dir)
    for ext in (".yaml", ".yml"):
        candidate = solution_dir.parent / f"{solution_dir.name}{ext}"
        if candidate.exists():
            return candidate
    return None


def _find_descriptor_by_stem(repo_root, stem):
    """Find `templates/env_templates/<stem>.yaml` (or .yml). Returns None if missing."""
    base = Path(repo_root) / "templates" / "env_templates"
    for ext in (".yaml", ".yml"):
        candidate = base / f"{stem}{ext}"
        if candidate.exists():
            return candidate
    return None


def delete_to_delete_files(plan, repo_root):
    """Remove every file listed under any group in plan['to_delete']."""
    repo_root = Path(repo_root)
    for group in (plan.get("to_delete") or {}).values():
        for rel in group:
            path = repo_root / rel
            if path.exists():
                path.unlink()


# ---- Default subprocess CLI runner (prod) ----

def default_cli_runner(context_path, dry_run=False):
    """Invoke external-cred-provision via subprocess. Returns (log_text, exit_code)."""
    cmd = ["external-cred-provision"]
    if dry_run:
        cmd.append("--dry-run")
    cmd.append(str(context_path))
    result = subprocess.run(cmd, capture_output=True, text=True)
    log_text = result.stdout + result.stderr
    return log_text, result.returncode


# ---- Top-level orchestration ----

def run_apply(plan_path, repo_root, cli_runner=None, dry_run=False, skip_pre_flight=False):
    """Execute the apply flow. Returns a migration-report dict.

    cli_runner: callable(context_path, dry_run) -> (log_text, exit_code). Defaults to
    the subprocess-based real invocation.
    """
    repo_root = Path(repo_root)
    plan = load_plan(plan_path)
    cli_runner = cli_runner or default_cli_runner

    # Instance-repo-only concerns: secret-stores.yml + pre-flight + Store writes.
    if plan.get("repo_type") == "instance":
        stores_path = repo_root / "configuration" / "secret-stores.yml"
        secret_stores = yaml.safe_load(stores_path.read_text()) or {}
        if not skip_pre_flight:
            check_single_store(secret_stores)
            store_type = next(iter(secret_stores.values()))["type"]
            check_store_auth_env([store_type])
            check_git_clean(repo_root)
        # Delegate context construction to the shared builder (also used by
        # envgene-external-context-generator CLI).
        context, skipped = build_context_from_repo(plan, repo_root)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tf:
            os.chmod(tf.name, 0o600)
            yaml.safe_dump(context, tf, sort_keys=False, default_flow_style=False)
            tmp_path = tf.name
        try:
            log_text, exit_code = cli_runner(tmp_path, dry_run=dry_run)
        finally:
            os.unlink(tmp_path)
        outcomes = parse_cli_log(log_text)
        successful = {cid for cid, o in outcomes.items() if o.success}
        failed = {cid: outcomes[cid].detail or "" for cid in outcomes if not outcomes[cid].success}
    else:
        # Template-repo: no Store I/O. Everything in plan counted as success.
        successful = {cid for _, cid, _ in _iter_plan_entries(plan)}
        failed = {}
        skipped = []

    # Git rewrites — only if not dry-run.
    if not dry_run:
        if plan.get("repo_type") == "template":
            # Create/update Credential Template + update Template Descriptor per descriptor.
            # Convention: cred template stem == descriptor stem.
            for group in plan.get("credentials", []):
                source_file = group["sourceFile"]
                cred_template_path = repo_root / source_file
                entries = {}
                for section in ("to_review", "to_confirm"):
                    entries.update(group.get(section) or {})
                if not entries:
                    continue
                descriptor = _find_descriptor_by_stem(repo_root, cred_template_path.stem.replace(".yml", ""))
                create_or_update_credential_template(
                    cred_template_path=cred_template_path,
                    cred_entries_from_plan=entries,
                    descriptor_path=descriptor,
                )
                if descriptor:
                    update_template_descriptor(
                        descriptor_path=descriptor,
                        cred_template_rel_path=str(cred_template_path.relative_to(
                            repo_root / "templates"
                        )),
                    )
        else:
            rewrite_source_files(plan, repo_root, successful)

        # Consumer files scanned per repo type via file_scanner.
        from .file_scanner import (
            find_consumer_files_instance,
            find_consumer_files_template,
        )
        finder = (
            find_consumer_files_instance if plan.get("repo_type") == "instance"
            else find_consumer_files_template
        )
        for cfile in finder(repo_root):
            rewrite_consumer_file(cfile)
        delete_to_delete_files(plan, repo_root)

    return {
        "store_writes": {
            "succeeded": len(successful),
            "failed": len(failed),
            "skipped_envgene_null_value": len(skipped) if plan.get("repo_type") == "instance" else 0,
        },
        "failed_creds": failed,
        "skipped_creds": skipped if plan.get("repo_type") == "instance" else [],
    }
