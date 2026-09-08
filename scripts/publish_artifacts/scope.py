import shutil
from pathlib import Path

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
