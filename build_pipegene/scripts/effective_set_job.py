import json
from os import getenv, environ
from pathlib import Path

from gcip import WhenStatement, Need

from envgenehelper import logger
from envgenehelper import cleanup_targets
from pipeline_helper import job_instance


def prepare_generate_effective_set_job(pipeline, full_env_name, env_name, cluster_name, app_reg_defs_job,
                                       artifact_app_defs_path, artifact_reg_defs_path, sd_version, sd_data,
                                       deployment_id, effective_set_config, tags):
    logger.info(f'Prepare generate-effective-set job for {full_env_name}')
    logger.info(f'Cleanup_targets: {cleanup_targets}')
            
    is_local_app_def = artifact_app_defs_path and artifact_reg_defs_path and app_reg_defs_job

    base_dir = getenv('CI_PROJECT_DIR')
    base_env_path = f"{base_dir}/environments/{full_env_name}"
    app_defs_path = f"{base_env_path}/AppDefs"
    reg_defs_path = f"{base_env_path}/RegDefs"

    sboms_path = f"{base_dir}/sboms"
    effective_set_config_dict = json.loads(effective_set_config)

    sd_path = Path(f'{base_dir}/environments/{full_env_name}/Inventory/solution-descriptor/sd.yaml')
    # TODO it is necessary to remove unnecessary calls, leave only script calls in such jobs! bad for gsf delivery
    script = [
        '/module/scripts/handle_certs.sh',
        # cert handling for java
        'mkdir -p ${CI_PROJECT_DIR}/configuration/certs/ && cp /default_cert.pem "${CI_PROJECT_DIR}/configuration/certs/default_cert.pem"',
        'for cert in "${CI_PROJECT_DIR}/configuration/certs/*" ; do [ -f "$cert" ] && keytool -import -trustcacerts -alias "$(basename "$cert")" -file "$cert" -keystore /etc/ssl/certs/keystore.jks -storepass changeit -noprompt; done',
        'python3 /module/scripts/main.py decrypt_cred_files',
        f'[ -n "$APP_REG_DEFS_JOB" ] && [ -n "$APP_DEFS_PATH" ] && mkdir -p {app_defs_path} && cp -rf {artifact_app_defs_path}/* {app_defs_path}',
        f'[ -n "$APP_REG_DEFS_JOB" ] && [ -n "$REG_DEFS_PATH" ] && mkdir -p {reg_defs_path} && cp -fr {artifact_reg_defs_path}/* {reg_defs_path}',
    ]

    cmdb_cli_cmd_call = [
        f"/deployments/run-java.sh --env-id={full_env_name}",
        "--envs-path=$CI_PROJECT_DIR/environments",
        f"--output=$CI_PROJECT_DIR/environments/{full_env_name}/effective-set"
    ]

    effective_set_version = effective_set_config_dict.get("version") or "v2.0"
    full_sd_exists = sd_path.parent.is_dir() and sd_path.is_file()
    sd_data = bool(sd_data) or bool(sd_version)
    if full_sd_exists or sd_data:
        cmdb_cli_cmd_call.extend([
            "--registries=$CI_PROJECT_DIR/configuration/registry.yml",
            f"--sboms-path={sboms_path}",
            f"--sd-path={sd_path}",
        ])

    if not (full_sd_exists and sd_data) and effective_set_version.lower() == "v1.0":
        raise ValueError("Feature generation effective set for pipeline and topology context is not supported for v1.0")

    effective_set_expiry = None
    logger.info(f'Prepare generate_effective_set job for {full_env_name}.')
    if effective_set_config:
        logger.info(f"EFFECTIVE_SET_CONFIG : {effective_set_config}")
        script.extend([
            f"python3 /module/scripts/handle_effective_set_config.py --effective-set-config '{effective_set_config}'",
            'extra_args=$(jq -r \'.extra_args // [] | join(" ")\' /tmp/effective_set_output.json)',
            'effective_set_expiry=$(jq -r \'.effective_set_expiry\' /tmp/effective_set_output.json)',
            'echo "extra_args before calling cmdb cli: $extra_args"',
        ])
        cmdb_cli_cmd_call.extend(["$extra_args"])
        effective_set_expiry = effective_set_config_dict.get("effective_set_expiry") or "1 hour"
    if deployment_id:
        cmdb_cli_cmd_call.extend([f"--extra_params=DEPLOYMENT_SESSION_ID={deployment_id}", ])

    script.append(" ".join(cmdb_cli_cmd_call))
    script.append('python3 /module/scripts/main.py encrypt_cred_files')
    generate_effective_set_params = {
        "name": f'generate_effective_set.{full_env_name}',
        "image": '${effective_set_generator_image}',
        "stage": 'generate_effective_set',
        "script": script
    }

    generate_effective_set_vars = {
        "CLUSTER_NAME": cluster_name,
        "ENVIRONMENT_NAME": env_name,
        "ENV_NAME": env_name,
        "INSTANCES_DIR": "${CI_PROJECT_DIR}/environments",
        "effective_set_generator_image": "$effective_set_generator_image",
        "envgen_args": " -vv",
        "envgen_debug": "true",
        "module_ansible_dir": "/module/ansible",
        "module_inventory": "${CI_PROJECT_DIR}/configuration/inventory.yaml",
        "module_ansible_cfg": "/module/ansible/ansible.cfg",
        "module_config_default": "/module/templates/defaults.yaml",
        "GITLAB_RUNNER_TAG_NAME": tags,
        "EXCLUDE_CLEANUP_TARGETS": " ".join(cleanup_targets)
    }
    needs = []
    if is_local_app_def:
        # gcip library doesn't allow to create a Need object that has the same pipeline as one it runs within.
        # We need to specify pipeline because generated job will be ran in child pipeline
        # To work around this we temporarily change value in environment and return it after creating the Need object
        real_ci_pipe_id = getenv('CI_PIPELINE_ID', '')  # currect pipeline, parent of future child pipeline
        environ['CI_PIPELINE_ID'] = '0000000'
        needs.append(Need(job=app_reg_defs_job, pipeline=real_ci_pipe_id, artifacts=True))
        environ['CI_PIPELINE_ID'] = real_ci_pipe_id
    generate_effective_set_job = job_instance(params=generate_effective_set_params, needs=needs,
                                                              vars=generate_effective_set_vars)
    generate_effective_set_job.artifacts.add_paths("${CI_PROJECT_DIR}/environments/" + f"{full_env_name}")
    generate_effective_set_job.artifacts.add_paths('${CI_PROJECT_DIR}/sboms')
    generate_effective_set_job.artifacts.add_paths('${CI_PROJECT_DIR}/configuration/registry.y*ml')

    if effective_set_expiry:
        logger.info(f"effective set expiry value '{effective_set_expiry}'")
        generate_effective_set_job.artifacts.expire_in = effective_set_expiry
    
    generate_effective_set_job.artifacts.when = WhenStatement.ALWAYS
    pipeline.add_children(generate_effective_set_job)
    
    return generate_effective_set_job
