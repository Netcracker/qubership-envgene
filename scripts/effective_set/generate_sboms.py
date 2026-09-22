from os import path, makedirs
from pathlib import Path

from effective_set.dd_downloading import download_dd_and_zip_artifacts
from envgenehelper import getenv_with_error, openYaml, get_sboms_dir, logger
from envgenehelper.json_helper import writeJsonToFile
from envgenehelper.yaml_helper import writeYamlToFile
from sbom_generator.generate_bom import Generator, SBOMOutput, exclude_resolved_apps



def generate_sboms(deploy_plan) -> None:
    work_dir = getenv_with_error('CI_PROJECT_DIR')
    app_sboms_path = get_sboms_dir(work_dir)

    if deploy_plan is None or not deploy_plan.entities:
        logger.info('No deploy plan found, skipping SBOM generation')
        return

    apps_needing_sbom = exclude_resolved_apps(deploy_plan, app_sboms_path)
    if not apps_needing_sbom:
        logger.info('All applications already have SBOMs, skipping SBOM generation')
        return

    deploy_plan.entities = apps_needing_sbom
    dd_artifacts, _ = download_dd_and_zip_artifacts([app.version for app in apps_needing_sbom])
    sbom_and_regs: SBOMOutput = Generator.generate_bom_by_content(
        sd_content=deploy_plan, dd_artifacts=dd_artifacts, sbom_dir_path=app_sboms_path)

    for id, sbom in sbom_and_regs.sboms.items():
        app_name = id.split(":")[0]
        app_sbom_path = Path(f"{app_sboms_path}/{app_name}")
        app_sbom_path.mkdir(parents=True, exist_ok=True)
        writeJsonToFile(f'{app_sbom_path}/{id.replace(":", "-")}.sbom.json', sbom)

    curr_registries_path = f'{work_dir}/configuration/registry.yml'
    curr_registries = openYaml(curr_registries_path, allow_default=True)
    for id, reg in sbom_and_regs.registries.items():
        curr_registries[id] = reg.model_dump(mode='json')
    makedirs(path.dirname(curr_registries_path), exist_ok=True)
    writeYamlToFile(curr_registries_path, curr_registries)
