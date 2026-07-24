import sys

from pipeline.multi_env_runner import fan_out
from pipeline.orchestrator import run_single_env_pipeline
from pipeline.pipeline_parameters import PipelineParametersHandler, resolve_env_names


def dispatch() -> int:
    env_names = resolve_env_names()
    if len(env_names) <= 1:
        run_single_env_pipeline()
        return 0

    handler = PipelineParametersHandler.from_env(allow_multi_env=True)
    env_names_value = handler.params.pop("ENV_NAMES", None)
    handler.write_dotenv()
    if env_names_value is not None:
        handler.params["ENV_NAMES"] = env_names_value

    return fan_out(env_names)


if __name__ == "__main__":
    raise SystemExit(dispatch())
