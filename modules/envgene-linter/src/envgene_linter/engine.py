from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

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
from .rules.name1 import check as check_name1
from .rules.name2 import check as check_name2
from .rules.name3 import check as check_name3
from .rules.name4 import check as check_name4


@dataclass
class CheckResult:
    findings: list[Finding]
    skipped: list[str]


def run_check(root: Path) -> CheckResult:
    index = build_index(root)
    connections = compute_connections(index)
    catalogs = build_catalogs(index, connections)
    full = {env.full_name: compute(index, env, ALL_LAYERS) for env in index.environments}
    lower = {env.full_name: compute(index, env, LOWER_LAYERS) for env in index.environments}
    site = {env.full_name: compute(index, env, SITE_LAYERS) for env in index.environments}
    findings = [
        *check_place1(index, full, lower, site, catalogs),
        *check_place2(index, full, lower, site),
        *check_place3(index, full, lower, site, catalogs, connections),
        *check_place4(index, connections),
        *check_place6(index, connections),
        *check_place7(index, connections),
        *check_place8(index, connections),
        *check_place9(index, connections),
        *check_place10(index, connections),
        *check_sec1(index, connections),
        *check_sec3(index, connections),
        *check_sec4(index, connections),
        *check_sec5(index, connections),
        *check_int2(index, connections),
        *check_name1(index, connections),
        *check_name2(index, connections),
        *check_name3(index, connections),
        *check_name4(index, connections),
    ]
    return CheckResult(findings=findings, skipped=index.skipped)
