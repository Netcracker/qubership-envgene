# Guide for running things locally

## Prerequisites

1. You have installed `WSL` and have `docker` in it.

## Setup

1. Check `docker-compose.yml` file to find the service for general unit tests,
   or job that you need to test and run
1. Run `make build-%` and `make up-%` where `%` is name of the service to get
   container running for service that you want. And run `make run-%` to actually
   run the code.

## Usage

Format:

```sh
make <command>-<service>
```

Where `service` matches the service name from docker-compose.yml.

| Command | What it does                              | Example              |
| ------- | ----------------------------------------- | -------------------- |
| `build` | Build service image                       | `make build-tests` |
| `up`    | Start service (runs `up.sh` if present)   | `make up-tests`    |
| `bash`  | Open shell in running service             | `make bash-tests`  |
| `down`  | Stop all services                         | `make down`          |
| `stop`  | Stop one service                          | `make stop-tests`  |
| `rm`    | Remove service container                  | `make rm-tests`    |
| `run`   | Run service’s `run.sh` script (if exists) | `make run-tests`   |
| `edit`  | Edit Makefile in Vim                      | `make edit`          |

**Notes:**

* `up.sh` / `run.sh` are optional, per-service scripts.
* If service is configured correctly and has the code mounted
  into it from repos, changes made in code in repos, should reflect immediately
  in container, so after code changes you would need to just run `make run-%`.
  If there are changes in docker-compose - run `make up-%` again and if there
  are changes in `Dockerfile` itself used for service - run `make build-%`
