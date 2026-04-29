compose := docker compose -f devtools/docker-compose.yml

build-%:
	$(compose) build $*

up-%:
	$(compose) up -d $*
	@if [ -f devtools/$*/up.sh ]; then $(compose) exec $* bash /workspace/devtools/$*/up.sh; fi

bash-%:
	$(compose) exec $* bash

# Non-interactive command in the tests container (same image and mount as make bash-tests).
# Example: make tests-run CMD='pytest scripts/build_env/tests/env-build/test_render_envs.py -v'
.PHONY: tests-run
tests-run:
	@test -n "$(CMD)" || (echo "Usage: make tests-run CMD='command run under /workspace'" >&2 && false)
	$(compose) exec -T tests bash -lc 'cd /workspace && $(CMD)'

down:
	$(compose) down

stop-%:
	$(compose) stop $*

rm-%:
	$(compose) rm $*

run-%:
	@if [ -f devtools/$*/run.sh ]; then $(compose) exec $* bash /workspace/devtools/$*/run.sh; \
	else echo "No run script for $*"; fi

edit:
	vim $(abspath $(lastword $(MAKEFILE_LIST)))
