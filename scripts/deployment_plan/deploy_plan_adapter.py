from pathlib import Path

from envgenehelper.yaml_helper import openYaml

DEPLOY_PLAN_FILE = "deploy-plan.yml"


def deploy_plan_entities(deploy_plan_path: Path) -> list[dict]:
    entities = openYaml(deploy_plan_path)
    if not isinstance(entities, list):
        raise ValueError(f"Deploy plan at {deploy_plan_path} must be a YAML list")
    return entities
