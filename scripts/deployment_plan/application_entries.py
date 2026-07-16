from dataclasses import dataclass

DEPLOY_PLAN_FILE = "deploy-plan.yml"


@dataclass(frozen=True)
class ApplicationDeploymentEntry:
    version: str
    deploy_postfix: str
    namespace: str | None = None


def application_entries_from_sd(sd_config: dict) -> list[ApplicationDeploymentEntry]:
    applications = sd_config.get("applications", [])
    return [
        ApplicationDeploymentEntry(
            version=app["version"],
            deploy_postfix=app.get("deployPostfix", ""),
        )
        for app in applications
    ]


def application_entries_from_deploy_plan_entities(entities: list[dict]) -> list[ApplicationDeploymentEntry]:
    return [
        ApplicationDeploymentEntry(
            version=entity["version"],
            deploy_postfix=entity.get("deployPostfix", ""),
            namespace=entity.get("namespace") or None,
        )
        for entity in entities
    ]
