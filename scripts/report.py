#! /usr/bin/python

import requests

import re
import yaml
from termcolor import colored
from os import getenv
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

with open('archive.yaml', 'r') as file_save:
    archive=yaml.load(file_save, Loader=yaml.SafeLoader)


regex_snapshot = r"[a-zA-Z0-9_\/\-:\.]*[0-9].json"
regex_release = r"[a-zA-Z0-9_\/\-:\.]*RELEASE.json"
ref_name = getenv('CI_COMMIT_REF_NAME')
is_not_release = False
for url in archive.split(" "):
    if re.match(regex_snapshot, url):
        json_path = url
        is_not_release = True
        ci_commit_ref_name = ref_name.replace('/', '-')
        pattern = r'{}-\w+-\d+'.format(re.escape(ci_commit_ref_name))
        version_match = re.search(r'{}-\d{{1,}}.\d{{1,}}-\d{{1,}}'.format(re.escape(ci_commit_ref_name)), url, re.IGNORECASE)
        env_template_version = version_match.group(0)
        break
    elif re.match(regex_release, url):
        json_path = url
        break

response = requests.get(json_path, verify=False)
if response.status_code == 200:
    json_data = response.json()
    maven_repository = json_data['configurations'][0]['maven_repository']
    artifacts_name = json_data['configurations'][0]['artifacts'][0]['name']
    artifacts_id = json_data['configurations'][0]['artifacts'][0]['id']
    array_maven = maven_repository.split('/')
    array_name = json_path.split('/')
    array_id = artifacts_id.split(':')

group_id = '.'.join(array_name[4:-3])
artifact_id = array_name[-3]
snapshot_version = array_name[-2]

def print_green(text):
    print(colored(text, 'green'))

def print_with_bars(text, header=None):
    if header:
        print_green(header)
    print_green("======================================================================")
    print_green(text)
    print_green("======================================================================\n \n")

def print_artifact_info(info, header=None):
    if isinstance(info, str):
        wrapped_info = {'envTemplate': {'artifact': info}}
    else:
        wrapped_info = {'envTemplate': {'templateArtifact': {'artifact': info}}}
    text = yaml.dump(wrapped_info, default_flow_style=False)
    print_with_bars(text, header)

print_green("To use the built artifact in GAV notation, set the following in the Environment Inventory:\n \n")
art_gav = {'group_id': group_id, 'artifact_id': artifact_id, 'version': snapshot_version}
print_artifact_info(art_gav, 'SNAPSHOT version')
if is_not_release:
    art_gav['version'] = env_template_version
    print_artifact_info(art_gav, 'Concrete version')

print_green("To use the built artifact in application:version notation, set the following in the Environment Inventory:\n \n")
art_appver = "{}:{}".format(artifact_id, snapshot_version)
print_artifact_info(art_appver, 'SNAPSHOT')
if is_not_release:
    art_appver = "{}:{}".format(artifact_id, env_template_version)
    print_artifact_info(art_appver, 'Concrete version')

print_green("NOTE: The applicationDefinition with the name <env-template-atifact-id> must be created in the cloud CMDB (cloud-deployer) for using app:ver notation\n \n")

artifact_url = "{}/{}/{}/{}/{}".format(
    maven_repository,
    '/'.join(array_id[0].split('.')),
    array_id[1],
    array_id[2],
    artifacts_name
)

print_with_bars(artifact_url, "Link to download zip part of the artifact")
open("build.env", "a").write(f"artifact_url={artifact_url}\n")
