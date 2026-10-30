import subprocess

from envgene_shared.utils.logger import logger
from envgene_shared.utils.collections_utils import split_multi_value_param


def clean_effective_set(ctx) -> None:
    logger.info("Cleaning effective set namespaces with argo-dpg cleanup structure")
    subprocess.run([
        "argo-dpg", "cleanup", "structure",
        "-p", f"params.environment_id={ctx.full_env_name}",
        "-p", f"params.rootdir={ctx.work_dir}",
        "-p", f"params.namespace_names={';'.join(split_multi_value_param(ctx.params.get('NAMESPACE_NAMES') or ''))}",
        "-p", f"params.commit_message=Clean effective set for {ctx.full_env_name}",
        "--log-level", ctx.params.get("ENVGENE_LOG_LEVEL") or "INFO",
    ], check=True)
