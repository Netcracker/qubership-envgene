# integration — Legacy, Unused in This Branch

This directory contains only this file. On `main`, `python/integration/integration_loader/loader.py` provided `IntergrationConfigLoader`, loading `integration.yml` (Cloud Passport discovery, CMDB config) into a Python object.

In this branch that config is loaded by a local function instead — `get_integration_config()` defined directly in `scripts/cloud_passport/main.py`, used by `run_cloud_passport()`. Nothing in the repo imports `python/integration` anymore.

## integration.yml Structure

```yaml
cp_discovery:
  gitlab:
    project: string       # Full GitLab project path of discovery repo
    branch: master
    token: string         # Auth token (creds.get macro or $type: credRef)
```

`get_integration_config()` returns `{}` (with a warning logged) if the file is missing — callers must not assume the key exists. In this branch only `cp_discovery.gitlab.token` is read (`scripts/cloud_passport/main.py::run_cloud_passport`); the CI-committing token comes directly from the `GITLAB_TOKEN` env var, not from a `self_token` config key.
