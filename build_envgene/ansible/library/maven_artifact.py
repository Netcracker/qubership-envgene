import logging
import os
import posixpath
import io
import traceback
import re
import json

from ansible.module_utils.ansible_release import __version__ as ansible_version

LXML_ETREE_IMP_ERR = None
try:
    from lxml import etree

    HAS_LXML_ETREE = True
except ImportError:
    LXML_ETREE_IMP_ERR = traceback.format_exc()
    HAS_LXML_ETREE = False

BOTO_IMP_ERR = None
try:
    import boto3

    HAS_BOTO = True
except ImportError:
    BOTO_IMP_ERR = traceback.format_exc()
    HAS_BOTO = False

SEMANTIC_VERSION_IMP_ERR = None
try:
    from semantic_version import Version, Spec

    HAS_SEMANTIC_VERSION = True
except ImportError:
    SEMANTIC_VERSION_IMP_ERR = traceback.format_exc()
    HAS_SEMANTIC_VERSION = False

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.six.moves.urllib.parse import urlparse
from ansible.module_utils.urls import fetch_url
from ansible.module_utils.common.text.converters import to_bytes, to_native, to_text


def split_pre_existing_dir(dirname):
    '''
    Return the first pre-existing directory and a list of the new directories that will be created.
    '''
    head, tail = os.path.split(dirname)
    b_head = to_bytes(head, errors='surrogate_or_strict')
    if not os.path.exists(b_head):
        if head == dirname:
            return None, [head]
        else:
            (pre_existing_dir, new_directory_list) = split_pre_existing_dir(head)
    else:
        return head, [tail]
    new_directory_list.append(tail)
    return pre_existing_dir, new_directory_list


def adjust_recursive_directory_permissions(pre_existing_dir, new_directory_list, module, directory_args, changed):
    '''
    Walk the new directories list and make sure that permissions are as we would expect
    '''
    if new_directory_list:
        first_sub_dir = new_directory_list.pop(0)
        if not pre_existing_dir:
            working_dir = first_sub_dir
        else:
            working_dir = os.path.join(pre_existing_dir, first_sub_dir)
        directory_args['path'] = working_dir
        changed = module.set_fs_attributes_if_different(directory_args, changed)
        changed = adjust_recursive_directory_permissions(working_dir, new_directory_list, module, directory_args, changed)
    return changed


class Artifact(object):
    def __init__(self, group_id, artifact_id, version, version_by_spec, classifier='', extension='jar'):
        if not group_id:
            raise ValueError("group_id must be set")
        if not artifact_id:
            raise ValueError("artifact_id must be set")

        self.group_id = group_id
        self.artifact_id = artifact_id
        self.version = version
        self.version_by_spec = version_by_spec
        self.classifier = classifier

        if not extension:
            self.extension = "jar"
        else:
            self.extension = extension

    def is_snapshot(self):
        return self.version and self.version.endswith("SNAPSHOT")

    def path(self, with_version=True):
        base = posixpath.join(self.group_id.replace(".", "/"), self.artifact_id)
        if with_version and self.version:
            timestamp_version_match = re.match("^(.*-)?([0-9]{8}\\.[0-9]{6}-[0-9]+)$", self.version)
            if timestamp_version_match:
                base = posixpath.join(base, timestamp_version_match.group(1) + "SNAPSHOT")
            else:
                base = posixpath.join(base, self.version)
        return base

    def _generate_filename(self):
        filename = self.artifact_id + "-" + self.classifier + "." + self.extension
        if not self.classifier:
            filename = self.artifact_id + "." + self.extension
        return filename

    def get_filename(self, filename=None):
        if not filename:
            filename = self._generate_filename()
        elif os.path.isdir(filename):
            filename = os.path.join(filename, self._generate_filename())
        return filename

    def __str__(self):
        result = "%s:%s:%s" % (self.group_id, self.artifact_id, self.version)
        if self.classifier:
            result = "%s:%s:%s:%s:%s" % (self.group_id, self.artifact_id, self.extension, self.classifier, self.version)
        elif self.extension != "jar":
            result = "%s:%s:%s:%s" % (self.group_id, self.artifact_id, self.extension, self.version)
        return result

    @staticmethod
    def parse(input):
        parts = input.split(":")
        if len(parts) >= 3:
            g = parts[0]
            a = parts[1]
            v = parts[-1]
            t = None
            c = None
            if len(parts) == 4:
                t = parts[2]
            if len(parts) == 5:
                t = parts[2]
                c = parts[3]
            return Artifact(g, a, v, c, t)
        else:
            return None


class MavenDownloader:
    def __init__(self, module, base, local=False, headers=None):
        self.module = module
        if base.endswith("/"):
            base = base.rstrip("/")
        self.base = base
        self.local = local
        self.headers = headers
        self.user_agent = "Ansible {0} maven_artifact".format(ansible_version)
        self.latest_version_found = None
        self.metadata_file_name = "maven-metadata-local.xml" if local else "maven-metadata.xml"

    def find_latest_version_available(self, artifact):
        if self.latest_version_found:
            return self.latest_version_found
        path = "/%s/%s" % (artifact.path(False), self.metadata_file_name)
        content = self._getContent(self.base + path, "Failed to retrieve the maven metadata file: " + path)
        xml = etree.fromstring(content)
        v = xml.xpath("/metadata/versioning/versions/version[last()]/text()")
        if v:
            self.latest_version_found = v[0]
            return v[0]

    def find_uri_for_artifact(self, artifact, suppress_errors=True):
        if artifact.is_snapshot():
            if self.local:
                return self._uri_for_artifact(artifact, artifact.version)
            path = "/%s/%s" % (artifact.path(), self.metadata_file_name)
            content = self._getContent(self.base + path, "Failed to retrieve the maven metadata file: " + path)
            xml = etree.fromstring(content)
            for snapshotArtifact in xml.xpath("/metadata/versioning/snapshotVersions/snapshotVersion"):
                classifier = snapshotArtifact.xpath("classifier/text()")
                artifact_classifier = classifier[0] if classifier else ''
                extension = snapshotArtifact.xpath("extension/text()")
                artifact_extension = extension[0] if extension else ''
                if artifact_classifier == artifact.classifier and artifact_extension == artifact.extension:
                    return self._uri_for_artifact(artifact, snapshotArtifact.xpath("value/text()")[0])

        try:
            self._getContent(self.base + '/' + artifact.path(),
                             "Failed to retrieve the maven metadata")
            return self._uri_for_artifact(artifact, artifact.version)
        except ValueError as e:
            if suppress_errors:
                return None
            raise e

    def _uri_for_artifact(self, artifact, version=None):
        if artifact.is_snapshot() and not version:
            raise ValueError("Expected uniqueversion for snapshot artifact " + str(artifact))
        elif not artifact.is_snapshot():
            version = artifact.version
        if artifact.classifier:
            return posixpath.join(version)

        return posixpath.join(version)

    # for small files, directly get the full content
    def _getContent(self, url, failmsg, force=True):
        if self.local:
            parsed_url = urlparse(url)
            if os.path.isfile(parsed_url.path):
                with io.open(parsed_url.path, 'rb') as f:
                    return f.read()
            if force:
                raise ValueError(failmsg + " because can not find file: " + url)
            return None
        response = self._request(url, failmsg, force)
        if response:
            return response.read()
        return None

    # only for HTTP request
    def _request(self, url, failmsg, force=True):
        url_to_use = url
        parsed_url = urlparse(url)

        if parsed_url.scheme == 's3':
            parsed_url = urlparse(url)
            bucket_name = parsed_url.netloc
            key_name = parsed_url.path[1:]
            client = boto3.client('s3', aws_access_key_id=self.module.params.get('username', ''), aws_secret_access_key=self.module.params.get('password', ''))
            url_to_use = client.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': key_name}, ExpiresIn=10)

        req_timeout = self.module.params.get('timeout')

        # trick to add parameters in the way that fetch_url expects
        self.module.params['url_username'] = self.module.params.get('username', '')
        self.module.params['url_password'] = self.module.params.get('password', '')
        self.module.params['http_agent'] = self.user_agent

        kwargs = {}
        if self.module.params['unredirected_headers']:
            kwargs['unredirected_headers'] = self.module.params['unredirected_headers']

        response, info = fetch_url(
            self.module,
            url_to_use,
            timeout=req_timeout,
            headers=self.headers,
            **kwargs
        )

        if info['status'] == 200:
            return response
        if force:
            raise ValueError(
                "Error: " + failmsg
                + "\nTried to use URL(repositoryDomainName + TargetRelease/Snapshot/Staging artifact_version): " + url_to_use
                + "\nReceived Response: " + info["msg"]
            )
        return None

def main():
    module = AnsibleModule(
        argument_spec=dict(
            discovery_repository=dict(default=None),
            artifact_definition=dict(default=None),
            group_id=dict(required=False),
            artifact_id=dict(required=False),
            version=dict(default=None),
            version_by_spec=dict(default=None),
            classifier=dict(default=''),
            extension=dict(default='jar'),
            repository_url=dict(default='https://repo1.maven.org/maven2'),
            username=dict(default=None, aliases=['aws_secret_key']),
            password=dict(default=None, no_log=True, aliases=['aws_secret_access_key']),
            headers=dict(type='dict'),
            state=dict(default="present", choices=["present", "absent"]),  # TODO - Implement a "latest" state
            timeout=dict(default=10, type='int'),
            dest=dict(type="path", required=False),
            unredirected_headers=dict(type='list', elements='str', required=False),
        ),
        add_file_common_args=True,
        mutually_exclusive=([('version', 'version_by_spec')])
    )

    if module.params["discovery_repository"] is not None:
        discovery_repository(module)
    else:
        download_artifact(module)

def convert_nexus_repo_url_to_index_view(url: str) -> str:
    has_trailing_slash = url.endswith("/")
    segments = url.rstrip("/").split("/")

    *head, last = segments
    if last != 'repository':
        return url
    new_segments = head + ['service', 'rest'] + [last, 'browse']
    new_url = "/".join(new_segments)

    if has_trailing_slash:
        new_url += "/"
    return new_url

def discovery_repository(module):
    artifact_definition = module.params["artifact_definition"]
    artifact_definition = artifact_definition.replace("'", '"')
    artifact_definition = json.loads(artifact_definition)

    repository_domain = artifact_definition["registry"]["mavenConfig"]["repositoryDomainName"]
    if not repository_domain.endswith('/'):
        repository_domain += '/'
    nexus_browse_repo_domain = convert_nexus_repo_url_to_index_view(repository_domain)
    maven_config = artifact_definition["registry"]["mavenConfig"]

    target_names = []
    target_names.append(maven_config["targetRelease"])
    target_names.append(maven_config["targetStaging"])
    target_names.append(maven_config["targetSnapshot"])

    repository_urls = []
    for domain_name in (repository_domain, nexus_browse_repo_domain):
        for target_name in target_names:
            # repo_url to try, target_name
            repository_urls.append((domain_name + target_name, target_name))

    errors = []
    for repository_url in repository_urls:
        version_dd = try_to_download_artifact(repository_url[0], artifact_definition, module)
        if isinstance(version_dd, str):
            discovered_repo_url = repository_domain + repository_url[1]
            module.exit_json(repository_url=discovered_repo_url, version_dd=version_dd, changed=True)
            return
        errors.append(str(version_dd))

    module.fail_json(msg="artifact not found", errors=errors)

def try_to_download_artifact(repository_url, artifact_definition, module):
    group_id = artifact_definition["groupId"]
    artifact_id = artifact_definition["artifactId"]

    version = module.params["version"]
    headers = module.params['headers']
    version_by_spec = module.params["version_by_spec"]
    classifier = module.params["classifier"]
    extension = module.params["extension"]
    local = False

    if not version_by_spec and not version:
        version = "latest"

    downloader = MavenDownloader(module, repository_url, local, headers)
    try:
        artifact = Artifact(group_id, artifact_id, version, version_by_spec, classifier, extension)
        return downloader.find_uri_for_artifact(artifact, suppress_errors=False)
    except ValueError as e:
        return e

def download_artifact(module):
    repository_url = module.params["repository_url"]
    if not repository_url:
        repository_url = "https://repo1.maven.org/maven2"
    try:
        parsed_url = urlparse(repository_url)
    except AttributeError as e:
        module.fail_json(msg='url parsing went wrong %s' % e)
    local = parsed_url.scheme == "file"
    if parsed_url.scheme == 's3' and not HAS_BOTO:
        module.fail_json(msg=missing_required_lib('boto3', reason='when using s3:// repository URLs'),
                         exception=BOTO_IMP_ERR)
    version_by_spec = module.params["version_by_spec"]
    classifier = module.params["classifier"]
    extension = module.params["extension"]
    headers = module.params['headers']
    state = module.params["state"]
    dest = module.params["dest"]
    group_id = module.params["group_id"]
    artifact_id = module.params["artifact_id"]
    version = module.params["version"]
    downloader = MavenDownloader(module, repository_url, local, headers)
    if not version_by_spec and not version:
        version = "latest"
    try:
        artifact = Artifact(group_id, artifact_id, version, version_by_spec, classifier, extension)
    except ValueError as e:
        module.fail_json(msg=e.args[0])
    changed = False
    version_dd = downloader.find_uri_for_artifact(artifact)
    if changed:
        module.exit_json(state=state, dest=dest, group_id=group_id, artifact_id=artifact_id, version=version, classifier=classifier,
                         extension=extension, repository_url=repository_url, changed=changed)
    else:
        module.exit_json(state=state, dest=dest, version_dd=version_dd, changed=changed)


if __name__ == '__main__':
    main()
