# SBOM-Generator

## Table of Contents


1. [Performance environment variables](#Performance environment variables)
2. [FAQ](#faq)
   - [Configuring Log Level](#configuring-log-level)
---

## Performance environment variables

| name    | default | description                                                                                          |
|---------|---------|------------------------------------------------------------------------------------------------------|
| `TCP_CONNECTION_LIMIT` | `100`   | Numver of TCP connections which can be opened simultaneously for downloading artifacts from registry |

## FAQ
### Configuring Log Level
Specify environment variable **LOGURU_LEVEL**