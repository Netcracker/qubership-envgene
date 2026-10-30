import os
import subprocess
import sys
from pathlib import Path

from dpg.v1.cleanup import finalize_deployment
from dpg.v1.internal.deployment_plan.models import DeployPlan
from envgene_shared.utils.yaml_utils import openYaml


def publish_effective_set(rootdir: Path, environment_id: str, deployment_plan_path: Path | None, log_level: str) -> None:
    plan = (DeployPlan.from_dict(openYaml(deployment_plan_path) or [])
            if deployment_plan_path is not None and deployment_plan_path.is_file() else DeployPlan())
    plan.validate_namespaces()
    subprocess.run([
        sys.executable, "/python/es-pusher/src/espusher/main.py", "push",
        "-p", f"params.environment_id={environment_id}",
        "-p", f'params.commit_message=DEVOPS-001 Push effective set for "{environment_id}"',
        "-p", "params.overwrite=false",
        "--log-level", log_level,
    ], cwd=rootdir, check=True)
    finalize_deployment(rootdir, environment_id, {entry.namespace for entry in plan.entities})


if __name__ == "__main__":
    rootdir = Path(os.environ["CI_PROJECT_DIR"])
    environment_id = os.environ["FULL_ENV_NAME"]
    operation = os.getenv("OPERATION_TYPE", "DEPLOY")
    deploying = operation == "DEPLOY" or (operation == "BGD" and os.getenv("BGD_OPERATION") == "warmup")
    publish_effective_set(
        rootdir, environment_id,
        rootdir / "environments" / environment_id / "Inventory" / "delta-deploy-plan.yml" if deploying else None,
        os.getenv("ENVGENE_LOG_LEVEL", "INFO").upper(),
    )
