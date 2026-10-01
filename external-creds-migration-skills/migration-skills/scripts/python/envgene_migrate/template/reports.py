"""Stdout plan-report / migration-report; stderr progress (verbose-gated)."""

from __future__ import annotations

import sys
from typing import Any

from .plan_schema import iter_plan_entries, unbound_parameter_sets

_verbose: bool = False

def set_verbose(enabled: bool) -> None:
    global _verbose
    _verbose = bool(enabled)


def is_verbose() -> bool:
    return _verbose


def progress(msg: str, *, force: bool = False) -> None:
    """Per-cred / debug lines go to stderr only when --verbose, unless force."""
    if force or _verbose:
        print(msg, file=sys.stderr, flush=True)


def compute_gate(plan: dict[str, Any]) -> dict[str, Any]:
    """Gate verdict for plan: STOP / GO + blockers and decisions."""
    review = [
        (cred_id, src, fields)
        for src, bucket, cred_id, fields in iter_plan_entries(plan)
        if bucket == "to_review"
    ]
    confirm = [
        (cred_id, src, fields)
        for src, bucket, cred_id, fields in iter_plan_entries(plan)
        if bucket != "to_review"
    ]
    total = len(review) + len(confirm)
    unbound = unbound_parameter_sets(plan)
    runtime = plan.get("runtime_credential_macros") or []
    plan_errors = plan.get("plan_errors") or []
    technical_bound = plan.get("technical_bound_parameter_sets") or []

    blockers: list[str] = []
    decisions: list[str] = []
    questions: list[dict[str, Any]] = []
    info: list[str] = []

    for e in plan_errors:
        blockers.append(f"[CRITICAL] {e}")

    if runtime:
        ids = sorted({str(r.get("credId")) for r in runtime if r.get("credId")})
        files = sorted({str(r.get("file")) for r in runtime if r.get("file")})
        file_preview = ", ".join(files[:8]) + (
            f" +{len(files) - 8} more" if len(files) > 8 else ""
        )
        blockers.append(
            "[CRITICAL] Credential macros in technicalConfigurationParameters "
            f"({len(runtime)} hit(s); credIds: {', '.join(ids)}). "
            "Not migrated to credRef — pipeline fails after cutover if left. "
            f"Files: {file_preview}. Reply A or B, then re-plan."
        )
        questions.append(
            {
                "id": 1,
                "topic": "technical/runtime credential macros",
                "options": [
                    (
                        "A",
                        "I will remove these macros myself from the Template "
                        "files, then reply done for re-plan",
                    ),
                    (
                        "B",
                        "Run strip-technical-macros (CLI removes hits), "
                        "then re-plan",
                    ),
                ],
            }
        )

    # technical_bound names: verbose only (not an operator decision).
    if _verbose:
        info.append(
            f"[INFO] technical bound ParameterSets: {len(technical_bound)}, "
            f"runtime macro hits: {len(runtime)}"
            + (
                f" ({', '.join(str(n) for n in technical_bound[:12])}"
                + (
                    f" +{len(technical_bound) - 12} more)"
                    if len(technical_bound) > 12
                    else ")"
                )
                if technical_bound
                else ""
            )
        )

    # Unbound ParameterSets: INFO only — never a DECISION or apply target.
    if unbound:
        info.append(
            f"[INFO] unbound ParameterSets: {len(unbound)} "
            "(ignored — not bound to any template; apply will not touch)"
        )

    if review:
        decisions.append(
            f"[DECISION] {len(review)} credential(s) in to_review - confirm "
            "create / remoteRefPath / includeInCredentialTemplate."
        )

    deployer = (plan.get("to_delete") or {}).get("deployer_credentials") or []
    if deployer:
        decisions.append(
            f"[DECISION] {len(deployer)} app-deployer/*-creds.yml - "
            "set operator_decisions.deployer_delete: true (delete) or false "
            "(keep; warn pipeline may fail) before apply."
        )

    can_apply = not blockers and not decisions
    if blockers:
        verdict = "STOP"
        why = "Critical blockers must be cleared before apply."
    elif decisions:
        verdict = "STOP"
        why = (
            "No critical blockers, but decisions are still open - "
            "review OK, apply not yet."
        )
    else:
        verdict = "GO"
        why = "No blockers; decisions complete - commit plan, then apply."

    return {
        "verdict": verdict,
        "why": why,
        "can_apply": can_apply,
        "blockers": blockers,
        "decisions": decisions,
        "questions": questions,
        "info": info,
        "counts": {
            "credentials": total,
            "to_review": len(review),
            "auto": len(confirm),
            "unbound_parameter_sets": len(unbound),
            "technical_bound": len(technical_bound),
            "runtime_hits": len(runtime),
        },
    }


def emit_gate_report(plan: dict[str, Any], *, repo_label: str = "") -> dict[str, Any]:
    """Print VERDICT / BLOCKERS / DECISIONS / Questions. Returns gate dict."""
    gate = compute_gate(plan)
    label = repo_label or plan.get("repo_type", "repo")
    print(f"[PLAN] {label}", flush=True)
    if plan.get("env_filter"):
        print(f"  scope: --env {plan['env_filter']} (debug filter)", flush=True)
    print("Wrote plan -> migration-plan.yaml", flush=True)
    print(flush=True)

    print(f"VERDICT: {gate['verdict']} - {gate['why']}", flush=True)
    print(flush=True)

    blockers = gate["blockers"]
    if blockers:
        print("BLOCKERS", flush=True)
        for i, b in enumerate(blockers, 1):
            print(f"  {i}. {b}", flush=True)
        print(flush=True)
    else:
        print("BLOCKERS: none", flush=True)
        print(flush=True)

    info = gate.get("info") or []
    if info:
        print("INFO", flush=True)
        for i, line in enumerate(info, 1):
            print(f"  {i}. {line}", flush=True)
        print(flush=True)

    decisions = gate["decisions"]
    if decisions:
        print("DECISIONS NEEDED", flush=True)
        for i, d in enumerate(decisions, 1):
            print(f"  {i}. {d}", flush=True)
        print(flush=True)
    else:
        print("DECISIONS NEEDED: none", flush=True)
        print(flush=True)

    questions = gate.get("questions") or []
    if questions:
        print("Questions for you:", flush=True)
        reply_bits: list[str] = []
        for q in questions:
            print(f"{q['id']}) {q['topic']}", flush=True)
            for letter, text in q["options"]:
                print(f"   {letter} - {text}", flush=True)
            reply_bits.append(f"{q['id']}A")
        print(f"Reply like: {', '.join(reply_bits)}", flush=True)
        print(flush=True)

    if gate["can_apply"]:
        print("CAN CONTINUE: yes - commit migration-plan.yaml, then apply.", flush=True)
    else:
        print(
            "CAN CONTINUE: review yes / apply no - clear blockers and decisions first.",
            flush=True,
        )
    print(flush=True)

    c = gate["counts"]
    print(
        f"Counts (short): creds={c['credentials']} "
        f"to_review={c['to_review']} auto={c['auto']} "
        f"technical_bound={c.get('technical_bound', 0)} "
        f"unbound_parameter_sets={c['unbound_parameter_sets']} "
        f"(ignored) "
        f"runtime_hits={c['runtime_hits']}",
        flush=True,
    )
    print(flush=True)
    return gate


def emit_plan_report(plan: dict[str, Any], *, repo_label: str = "") -> None:
    gate = emit_gate_report(plan, repo_label=repo_label)

    if not _verbose:
        print(
            "Details omitted (pass --verbose for to_review list, "
            "unbound ParameterSets, runtime hits).",
            flush=True,
        )
        if gate["verdict"] == "STOP":
            print(
                "Next: answer Questions (A/B/C…) → write decisions into "
                "migration-plan.yaml.",
                flush=True,
            )
        else:
            print("Next: commit migration-plan.yaml → run apply.", flush=True)
        return

    review = [
        (cred_id, src, fields)
        for src, bucket, cred_id, fields in iter_plan_entries(plan)
        if bucket == "to_review"
    ]
    confirm = [
        (cred_id, src, fields)
        for src, bucket, cred_id, fields in iter_plan_entries(plan)
        if bucket != "to_review"
    ]

    will_store = sum(
        1
        for _, _, _, f in iter_plan_entries(plan)
        if f.get("writeToStore", True) is True
    )
    rewrite_only = sum(
        1
        for _, _, _, f in iter_plan_entries(plan)
        if f.get("writeToStore") is False
    )

    print("═══ DETAILS (--verbose) ═══", flush=True)
    print(flush=True)
    if plan.get("repo_type") == "instance":
        print(f"  store write: {will_store}; rewrite-only: {rewrite_only}", flush=True)
        print(flush=True)

    if review:
        print(f"═══ TO REVIEW ({len(review)}) ═══", flush=True)
        for cred_id, src, fields in review:
            print(f"  {cred_id}  ({src})", flush=True)
            print(
                f"    suggested: {fields.get('remoteRefPath')} "
                f"create:{fields.get('create')} "
                f"writeToStore:{fields.get('writeToStore', True)}",
                flush=True,
            )
            for w in fields.get("suggestions") or []:
                print(f"    note: {w}", flush=True)
            print(flush=True)

    if confirm:
        print(f"═══ AUTO ({len(confirm)}) ═══", flush=True)
        for cred_id, src, fields in confirm:
            print(
                f"  {cred_id}  ({src}) → {fields.get('remoteRefPath')} "
                f"create:{fields.get('create')}",
                flush=True,
            )
        print(flush=True)

    unbound = unbound_parameter_sets(plan)
    if unbound:
        print(f"═══ UNBOUND PARAMETER SETS ({len(unbound)}) — ignored ═══", flush=True)
        for row in unbound:
            print(
                f"  {row.get('name')}  ({row.get('path')}) "
                f"credIds={len(row.get('credIds') or [])} "
                f"— not bound; apply will not touch",
                flush=True,
            )
        print(flush=True)

    runtime = plan.get("runtime_credential_macros") or []
    if runtime:
        print(f"═══ RUNTIME MACROS ({len(runtime)}) ═══", flush=True)
        for row in runtime[:30]:
            print(
                f"  {row.get('credId')}  ({row.get('file')}) [{row.get('source')}]",
                flush=True,
            )
        if len(runtime) > 30:
            print(f"  … and {len(runtime) - 30} more", flush=True)
        print(flush=True)

    stale = plan.get("stale_credential_template_entries") or []
    if stale:
        print(f"═══ STALE CT ({len(stale)}) ═══", flush=True)
        for row in stale[:20]:
            print(f"  {row.get('credId')}  ({row.get('sourceFile')})", flush=True)
        print(flush=True)

    if gate["verdict"] == "STOP":
        print(
            "Next: answer Questions → set decision in migration-plan.yaml.",
            flush=True,
        )
    else:
        print("Next: commit migration-plan.yaml → run apply.", flush=True)


def emit_migration_report(
    *,
    repo_label: str,
    store_ok: int = 0,
    store_fail: int = 0,
    git_ok: int = 0,
    git_fail: int = 0,
    macro_ok: int = 0,
    macro_fail: int = 0,
    warnings: list[str] | None = None,
) -> None:
    print(f"[APPLY] Executing migration plan for {repo_label}", flush=True)
    print(flush=True)
    print("Summary:", flush=True)
    print(f"  Store writes:        {store_ok} succeeded, {store_fail} failed", flush=True)
    print(f"  Git rewrites:        {git_ok} succeeded, {git_fail} failed", flush=True)
    print(f"  Macro replacements:  {macro_ok} succeeded, {macro_fail} failed", flush=True)
    if warnings:
        print(flush=True)
        print("Warnings:", flush=True)
        for w in warnings:
            print(f"  {w}", flush=True)
    print(flush=True)
    if store_fail or git_fail or macro_fail:
        print("Migration finished with failures.", flush=True)
    else:
        print("Migration complete. Commit changes and proceed to next step.", flush=True)
