# integration — External Integration Config Loader

Thin helper that loads the `integration.yml` config dict into a Python object. Used by modules that integrate with external systems (Cloud Passport discovery, CMDB).

## Files

| File | Responsibility |
|------|---------------|
| `integration_loader/loader.py` | `IntergrationConfigLoader` — flattens a dict onto `self` attributes; special-cases the `cp_discovery` sub-dict by expanding it as a nested object |

## integration.yml Structure

```yaml
cp_discovery:
  gitlab:
    project: string       # Full GitLab project path of discovery repo
    branch: master
    token: string         # Auth token (creds.get macro or $type: credRef)
self_token: string        # Token for EnvGene to commit back to instance repo
```

`self_token` falls back to the `GITHUB_TOKEN` / `GITLAB_TOKEN` CI/CD variable if not set in the file.
