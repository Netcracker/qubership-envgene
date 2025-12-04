import os
from shutil import rmtree

is_init = "{{ cookiecutter._is_init }}" == "true"
is_gitlab = "{{ cookiecutter.is_gitlab }}" == "true"

INIT_PATHS = [
    ".gitignore",
    "README.md",
    "environments",
    "configuration",
]

CI_PLATFORM_PATHS_TO_REMOVE = {
    False: [".gitlab-ci.yml", "gitlab-ci"],
    True: [".github"]
}

for path in CI_PLATFORM_PATHS_TO_REMOVE[is_gitlab]:
    if not os.path.exists(path):
        continue
    if os.path.isfile(path):
        os.remove(path)
    else:
        rmtree(path)

if not is_init:
    for p in INIT_PATHS:
        if not os.path.exists(p):
            continue
        os.remove(p) if os.path.isfile(p) else rmtree(p)

