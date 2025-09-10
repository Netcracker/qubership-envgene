from gcip import Job, Need
from typing import Optional, List, Dict, Union, Any
from envgenehelper import (
    logger,
    check_file_exists,
    openYaml,
    getAppDefinitionPath,
    get_envgene_config_yaml,
    get_or_create_nested_yaml_attribute,
)
from os import getenv

class JobExtended(Job):
    def __init__(
        self,
        name: str,
        stage: str,
        image: Optional[str],
        script: List[str],
        variables: Optional[Dict[str, str]] = None,
        needs: Optional[List[Union['Need', 'Job', List[str]]]] = None,
        tags: Optional[List[str]] = None,
        timeout: Optional[int] = None
    ) -> None:
        super().__init__(name=name, stage=stage, image=image, script=script, variables=variables, needs=needs, tags=tags)
        self.script = script
        self.timeout = timeout

    def render(self) -> Dict[str, Any]:
        job_data = super().render()
        job_data['script'] = self.script
        job_data['timeout'] = self.timeout
        return job_data

def job_instance(params, vars, needs=None, rules=None):
    timeout = params.get('timeout', '10m')
    gitlab_runner_tag = vars.get('GITLAB_RUNNER_TAG_NAME')
    job = JobExtended(
        name=params['name'],
        image=params['image'],
        stage=params['stage'],
        script=params['script'],
        variables=vars,
        timeout=timeout
    )
    if 'before_script' in params.keys():
        job.prepend_scripts(params['before_script'])
    if 'after_script' in params.keys():
        job.append_scripts(params['after_script'])
    if needs is None:
        needs = []
    job.set_needs(needs)
    job.add_tags(gitlab_runner_tag)
    if rules:
        job.rules.extend(rules)
    return job


def get_gav_coordinates_from_build():
    result = {
        "group_id": "",
        "artifact_id": "",
        "version": ""
    }
    file_path_gav = f"{getenv('CI_PROJECT_DIR')}/GAV_coordinates.yaml"
    if check_file_exists(file_path_gav):
        content = openYaml(file_path_gav, safe_load=True)
        if content and "artifact" in content:
            result["group_id"] = content["artifact"]["group_id"]
            result["artifact_id"] = content["artifact"]["artifact_id"]
            result["version"] = content["artifact"]["version"]
            logger.info(f'group_id: {result["group_id"]}')
            logger.info(f'artifact_id: {result["artifact_id"]}')
            logger.info(f'version: {result["version"]}')
        else:
            logger.error(f"File '{file_path_gav}' is empty. No build information available.")
            raise ReferenceError("Execution is aborted build artifact is not valid. See logs above.")
    else:
        logger.error(f"No build results found. File '{file_path_gav}' not found.")
        raise ReferenceError("Execution is aborted build artifact is not valid. See logs above.")
    return result

def find_predecessor_job(job_name, jobs_map, jobs_sequence):
    seqIdx = jobs_sequence.index(job_name)
    predecessors = reversed(jobs_sequence[:seqIdx])
    for previousJob in predecessors:
        if previousJob in jobs_map:
            return [jobs_map[previousJob]]
    return []

def check_discovery_job_needed(env_definition: dict, env_template_vers: str) -> bool:
    is_app_ver_format = False
    if env_template_vers and ":" in env_template_vers:
        is_app_ver_format = True
    elif env_definition:
        env_template_vers = get_or_create_nested_yaml_attribute(env_definition, 'envTemplate.artifact', None)
        is_app_ver_format = env_template_vers

    if not is_app_ver_format:
        return False

    config = get_envgene_config_yaml()
    mode = str(config.get('artifact_definitions_discovery_mode', 'auto')).lower()
    if mode == 'true':
        return True

    template_name = env_template_vers.split(':')[0]
    app_def_path = getAppDefinitionPath(getenv('CI_PROJECT_DIR'), template_name)
    if check_file_exists(app_def_path):
        return False

    if mode == 'false':
        raise Exception(f"\nartifact definition for artifact with name: {template_name} is not found in the path: /configuration/artifact_definitions\n\n"
                        +'artifact definition discovery is disable in /configuration/config.yml: \n'
                        +'artifact_definitions_discovery_mode: false\n\n'
                        +'set artifact definition manually or enable artifact definition discovery \n')
    return True
