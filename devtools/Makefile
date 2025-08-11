compose := sudo docker compose -f docker-compose.yml

build-%:
	$(compose) build $*

up-%:
	$(compose) up -d $*
	@if [ -f $*/up.sh ]; then $(compose) exec $* sh /workspace/devtools/$*/up.sh; fi

bash-%:
	$(compose) exec $* bash

down:
	$(compose) down

stop-%:
	$(compose) stop $*

rm-%:
	$(compose) rm $*

run-%:
	@if [ -f $*/run.sh ]; then $(compose) exec $* sh /workspace/devtools/$*/run.sh; \
	else echo "No run script for $*"; fi

edit:
	vim $(abspath $(lastword $(MAKEFILE_LIST)))
