import shutil
from pathlib import Path

from envgenehelper.business_helper import pubreg_transient_dir
from regdefv2_adapter.regdefv2_adapter import REGDEFS_DIRNAME

SCOPE_TOP_LEVEL_DIRS = ["appdefs", "regdefs", "configuration", "sboms", "environments", "cmdb-import"]


def copy_scope(work_dir: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for name in SCOPE_TOP_LEVEL_DIRS:
        src = work_dir / name
        if src.exists():
            shutil.copytree(src, dest / name, dirs_exist_ok=True)

    templates_src = work_dir / "tmp" / "templates"
    if templates_src.exists():
        shutil.copytree(templates_src, dest / "templates", dirs_exist_ok=True)

    app_artifacts_src = work_dir / "tmp" / "app-artifacts"
    if app_artifacts_src.exists():
        for dd_json in app_artifacts_src.rglob("dd.json"):
            rel = dd_json.relative_to(app_artifacts_src)
            target = dest / "app-artifacts" / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dd_json, target)

    regdefv2_regdefs_src = pubreg_transient_dir(work_dir) / REGDEFS_DIRNAME
    if regdefv2_regdefs_src.exists():
        shutil.copytree(regdefv2_regdefs_src, dest / regdefv2_regdefs_src.relative_to(work_dir), dirs_exist_ok=True)
