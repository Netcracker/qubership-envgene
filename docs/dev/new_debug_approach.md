# New approach for testing changes in instance repo

## Intro

Usual dev process in envgene looks like this:

Make changes -> commit -> wait for images to build(10-15 minutes) -> test changes in instance repo (1-2 minutes)
Iteration time: 11-17 minutes 😭

New approach:

Make changes -> commit -> test changes in instance repo(1-2 minutes)
Iteration time: 1-2 minutes 😄

## General idea

Use pipegene extension mechanism for replacing the source code from images(python, yaml files, etc) with files from instance repo for
debugging.

## Setup

1. Create `devtest/wdebug_plugin` folder in instance repo.
1. Create `devtest/wdebug_plugin/main.py` file with this content

    ```Python
    from plugin_engine import PluginCore
    from envgenehelper import logger

    class EffectiveSetJobPlugin(PluginCore):
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)

        def invoke(self, *args, params, pipeline_helper, pipeline, **kwargs) -> None:
            env = params['full_env']
            logger.info(f'Extending pipeline with debug logic')
            call_debug_sh = 'bash ${CI_PROJECT_DIR}/devtest/debug.sh || true'
            jobs_map = params['jobs_map']
            for job in jobs_map.values():
                job.script.insert(0, call_debug_sh)
    ```

1. Update .gitlab-ci.yml to add code for copying previously created extension to path for plugins

    ```yaml

    generate_pipeline:
      extends:
        - .generate_pipeline
    # necessary changes below
      before_script:
        - cp -r ${CI_PROJECT_DIR}/devtest/wdebug_plugin /module/scripts/pipegene_plugins/per_env
        # optional for testing changes in plugins
        - cp "$CI_PROJECT_DIR/devtest/effective_set_job.py" /module/scripts/pipegene_plugins/per_env/effective_set_job/effective_set_job.py
    # necessary changes above
      stage: generate

    ```

1. Create copies of files from envgene repo in instance repo using hard links `ln -f <path_to_file_in_envene> <path_to_instance>/devtest/`
By using hardlinks changes you make will be reflected in both envgene and instance repo files.
1. Create debug.sh file with code that you need(use example below as base)

    ```bash
    echo 'debug plugin is active'
    # check job name("$CI_JOB_NAME") or job image("$CI_JOB_IMAGE") to ensure replacements happen in right places
    if [[ "$CI_JOB_NAME" = "generate-effective"* ]]; then 
      echo "CI_JOB_NAME is '$CI_JOB_NAME'"
      # Examples
      # Sometimes you can get paths in container from error logs, if not look at the related Dockerfile to tell where file ends up in container
      cp "$CI_PROJECT_DIR/devtest/appver_resolver.py" /module/venv/lib/python3.10/site-packages/appver_resolver/appversion_resolver.py
      cp "$CI_PROJECT_DIR/devtest/get_sboms.py" /module/scripts/get_sboms.py
      echo "File copied."
    fi
    if [[ "$CI_JOB_NAME" = "env-builder"* ]]; then
      echo "CI_JOB_NAME is '$CI_JOB_NAME'"
      # Examples
      cp "$CI_PROJECT_DIR/devtest/01_prepare_vars.yaml" /module/ansible/roles/set_template_version/tasks/01_prepare_vars.yaml
      echo "File copied."
    fi
    ```

## Workflow

1. Make changes in envgene repo
1. Commit changes in instance repo
1. Run pipeline and test changes
1. Once necessary changes are made and pipeline works as expected:
    1. Commit in envgene repo and wait for images
    1. Remove lines that add debug plugin in generate_pipeline job in .gitlab-ci.yml
    1. Re-run tests to ensure that everything works as expected

## Issues

1. Add pipeline plugins sorting into main branch in qubership-envgene(is in RC branch at the moment)
Some kind of sorting or setting load order for plugins is necessary, because some plugins(1 plugin at the moment) completely overwrite the
script of a job and in that case changes made by debug plugin are lost. It doesn't have to be alphabetical sorting, it is used just as
simplest solution at the moment(downside: have to name plugin `wdebug` to have it at last place in load order)
1. Hard links get broken by `git pull`(make some kind git hook for recovering hard links?)
1. Pick better names for devtest folder and plugin
