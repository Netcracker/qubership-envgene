from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import rule_config
from .connections import compute_connections
from .discovery import build_index
from .effective import ALL_LAYERS, LOWER_LAYERS, SITE_LAYERS, compute
from .model import Finding
from .passport import build_catalogs
from .rules.place1 import check as check_place1
from .rules.place2 import check as check_place2
from .rules.place3 import check as check_place3
from .rules.place4 import check as check_place4
from .rules.place6 import check as check_place6
from .rules.place7 import check as check_place7
from .rules.place8 import check as check_place8
from .rules.place9 import check as check_place9
from .rules.place10 import check as check_place10
from .rules.sec1 import check as check_sec1
from .rules.sec3 import check as check_sec3
from .rules.sec4 import check as check_sec4
from .rules.sec5 import check as check_sec5
from .rules.int2 import check as check_int2
from .rules.int3 import check as check_int3
from .rules.int4 import check as check_int4
from .rules.name1 import check as check_name1
from .rules.name2 import check as check_name2
from .rules.name3 import check as check_name3
from .rules.name4 import check as check_name4
from .rules.name8 import check as check_name8


@dataclass
class CheckResult:
    findings: list[Finding]
    skipped: list[str]
    disabled_rules: tuple[str, ...] = ()


def run_check(root: Path) -> CheckResult:
    disabled = rule_config.disabled_rules()
    if len(disabled) == len(rule_config.RULES):
        return CheckResult(findings=[], skipped=[], disabled_rules=disabled)
    index = build_index(root)
    connections = compute_connections(index)
    catalogs = build_catalogs(index, connections)
    full = {env.full_name: compute(index, env, ALL_LAYERS) for env in index.environments}
    lower = {env.full_name: compute(index, env, LOWER_LAYERS) for env in index.environments}
    site = {env.full_name: compute(index, env, SITE_LAYERS) for env in index.environments}
    checks = [
        ("PLACE-1", check_place1, (index, full, lower, site, catalogs)),
        ("PLACE-2", check_place2, (index, full, lower, site)),
        ("PLACE-3", check_place3, (index, full, lower, site, catalogs, connections)),
        ("PLACE-4", check_place4, (index, connections)),
        ("PLACE-6", check_place6, (index, connections)),
        ("PLACE-7", check_place7, (index, connections)),
        ("PLACE-8", check_place8, (index, connections)),
        ("PLACE-9", check_place9, (index, connections)),
        ("PLACE-10", check_place10, (index, connections)),
        ("SEC-1", check_sec1, (index, connections)),
        ("SEC-3", check_sec3, (index, connections)),
        ("SEC-4", check_sec4, (index, connections)),
        ("SEC-5", check_sec5, (index, connections)),
        ("INT-2", check_int2, (index, connections)),
        ("INT-3", check_int3, (index, connections)),
        ("INT-4", check_int4, (index, connections)),
        ("NAME-1", check_name1, (index, connections)),
        ("NAME-2", check_name2, (index, connections)),
        ("NAME-3", check_name3, (index, connections)),
        ("NAME-4", check_name4, (index, connections)),
        ("NAME-8", check_name8, (index, connections)),
    ]
    findings = []
    for rule, check, args in checks:
        if rule not in disabled:
            findings.extend(check(*args))
    return CheckResult(findings=findings, skipped=index.skipped, disabled_rules=disabled)
