# scripts — Shared Pipeline Utilities

Shared shell scripts and Python utilities included by multiple Docker images via Docker COPY or script inclusion.

## utils/

| File | Responsibility |
|------|---------------|
| `run_effective_set_cli.sh` | Invokes the Java Calculator CLI. Called by `effective_set_entrypoint.py` with assembled arguments. Wraps classpath setup and JVM invocation |
| `handle_certs.sh` | Installs/updates CA certificates from `configuration/certs/` into the system trust store |
| `update_ca_cert.sh` | Low-level cert update helper |
| `log_pipe_params.py` | Logs pipeline parameters for debugging/audit |
| `pipeline_parameters.py` | Parses and validates pipeline parameter combinations |
| `sparse_checkout.sh` | Configures git sparse checkout for large instance repositories |

## Key: `run_effective_set_cli.sh`

This is the bridge between the Python orchestration layer and the Java Calculator. Its arguments are assembled by `build_effective_set_generator/scripts/effective_set_entrypoint.py::_build_cli_cmd()`. Notable flags:

- `--env-id` — `FULL_ENV_NAME` (`<cluster>/<env>`)
- `--envs-path` — `$CI_PROJECT_DIR/environments`
- `--output` — path to write the ES
- `--sd-path` — path to `sd.yaml` or `delta_sd.yaml`
- `--registries` — path to `configuration/registry.yml`
- `--sboms-path` — path to `sboms/` directory
- `--effective-set-version` — from `EFFECTIVE_SET_CONFIG`
- `--custom-params` — from `CUSTOM_PARAMS` pipeline variable
