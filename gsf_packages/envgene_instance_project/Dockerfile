# syntax=docker/dockerfile:1.19
FROM scratch

LABEL gsf.package="true"

COPY gsf_packages/envgene_instance_project/git-system-follower-package /git-system-follower-package

ARG GIT_HOOKS_DIR="/git-system-follower-package/scripts/templates/default/{{ cookiecutter.gsf_repository_name }}/git_hooks"
COPY --exclude=tests modules/envgene-shared/envgene_shared ${GIT_HOOKS_DIR}/envgene_shared
