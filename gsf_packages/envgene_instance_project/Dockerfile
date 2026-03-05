FROM scratch

LABEL gsf.package="true"

COPY gsf_packages/envgene_instance_project/git-system-follower-package /git-system-follower-package

WORKDIR /git-system-follower-package

COPY schemas/config.schema.json "scripts/templates/default/{{ cookiecutter.gsf_repository_name }}/git_hooks/"