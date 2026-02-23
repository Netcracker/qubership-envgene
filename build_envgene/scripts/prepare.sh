#!/bin/bash
set -e

#### input variables
# envgen_debug
# envgen_args
# module_ansible_dir
# module_ansible_cfg
# module_inventory
# CI_SERVER_URL
# GITLAB_TOKEN

playbook_name=$1
ansible_dir=${module_ansible_dir}

if ${envgen_debug} ; then set -o xtrace; fi

chmod 700 "$ansible_dir"
cd "$ansible_dir"

export ANSIBLE_CONFIG=${module_ansible_cfg}

#### Run ansible
echo "ansible-playbook playbooks/$playbook_name -i ${module_inventory} ${envgen_args}"
if ansible-playbook "playbooks/$playbook_name" -i "${module_inventory}" ${envgen_args}; then
    status=0
else
    status=$?
fi

mkdir -p "$CI_PROJECT_DIR/build_env/tmp"
if [ -d "/build_env/tmp" ]; then
    cp -r /build_env/tmp/* "$CI_PROJECT_DIR/build_env/tmp/" || true
fi

exit $status

