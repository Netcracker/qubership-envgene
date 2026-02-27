from os import environ
from pathlib import Path

import pytest
import responses
from aioresponses import aioresponses
from env_template.process_env_template import process_env_template
from envgenehelper.test_helpers import TestHelpers

GROUP_ID = "org.qubership"
PROJECT_GROUP_ID = "org.qubership.project"

ARTIFACT_ID = "qubership_envgene_templates"
ARTIFACT_ZIP_ID = f"{ARTIFACT_ID}-zip"

VERSION = "master-SNAPSHOT"

SNAPSHOT_TIMESTAMP = "20251223.070533"
SNAPSHOT_BUILD = "16"
SNAPSHOT_VERSION = f"master-{SNAPSHOT_TIMESTAMP}-{SNAPSHOT_BUILD}"

ZIP_HASH = "103e65"
ZIP_BUILD_TIME = "20251219-035732"
ZIP_VERSION = f"{ZIP_HASH}_{ZIP_BUILD_TIME}"

GROUP_PATH = GROUP_ID.replace(".", "/")
PROJECT_GROUP_PATH = PROJECT_GROUP_ID.replace(".", "/")

SNAPSHOT_BASE = "https://artifactory.qubership.org/mvn.snapshot"
TMPL_SNAPSHOT_BASE = "https://artifactory.qubership.org/tmpl-mvn.snapshot"
STAGING_BASE = "https://artifactory.qubership.org/mvn.staging"

BASE_PATH = f"{GROUP_PATH}/{ARTIFACT_ID}/{VERSION}"
ARTIFACT_NAME = f"{ARTIFACT_ID}-{SNAPSHOT_VERSION}"

METADATA_URL = f"{SNAPSHOT_BASE}/{BASE_PATH}/maven-metadata.xml"
DD_URL = f"{SNAPSHOT_BASE}/{BASE_PATH}/{ARTIFACT_NAME}.json"
ZIP_URL = f"{SNAPSHOT_BASE}/{BASE_PATH}/{ARTIFACT_NAME}.zip"

STAGING_ZIP_URL = (
    f"{STAGING_BASE}/{PROJECT_GROUP_PATH}/"
    f"{ARTIFACT_ZIP_ID}/{ZIP_VERSION}/"
    f"{ARTIFACT_ZIP_ID}-{ZIP_VERSION}.zip"
)

TMPL_ZIP_URL = (
    f"{TMPL_SNAPSHOT_BASE}/{PROJECT_GROUP_PATH}/"
    f"{ARTIFACT_ZIP_ID}/{ZIP_VERSION}/"
    f"{ARTIFACT_ZIP_ID}-{ZIP_VERSION}.zip"
)


@pytest.fixture
def mock_aio_response():
    with aioresponses() as m:
        yield m


metadata_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<metadata modelVersion="1.1.0">
  <groupId>{GROUP_ID}</groupId>
  <artifactId>{ARTIFACT_ID}</artifactId>
  <version>{VERSION}</version>
  <versioning>
    <snapshot>
      <timestamp>{SNAPSHOT_TIMESTAMP}</timestamp>
      <buildNumber>{SNAPSHOT_BUILD}</buildNumber>
    </snapshot>
    <lastUpdated>20251228013827</lastUpdated>
    <snapshotVersions>
      <snapshotVersion>
        <extension>json</extension>
        <value>{SNAPSHOT_VERSION}</value>
        <updated>20251223070533</updated>
      </snapshotVersion>
      <snapshotVersion>
        <extension>zip</extension>
        <value>{SNAPSHOT_VERSION}</value>
        <updated>20251223070533</updated>
      </snapshotVersion>
    </snapshotVersions>
  </versioning>
</metadata>
"""

dd_json = {
    "configurations": [{
        "artifacts": [{
            "id": f"{PROJECT_GROUP_ID}:{ARTIFACT_ZIP_ID}:{ZIP_VERSION}",
            "type": "zip",
            "classifier": ""
        }],
        "maven_repository": STAGING_BASE
    }]
}


def set_env(name: str):
    environ["ENVIRONMENT_NAME"] = name


def mock_metadata(aio_mock, url=METADATA_URL, repeat=1):
    aio_mock.get(url, body=metadata_xml, content_type="application/xml", status=200, repeat=repeat)


def mock_dd_exists(aio_mock=None, exists=True):
    status = 200 if exists else 404

    if aio_mock:
        aio_mock.head(DD_URL, payload="", status=status)
    else:
        responses.add(responses.HEAD, DD_URL, status=status)


def mock_dd_response():
    responses.add(responses.GET, DD_URL, json=dd_json, status=200)


def mock_zip(url):
    responses.add(
        responses.GET,
        url,
        body=TestHelpers.create_fake_zip(),
        content_type="application/zip",
        status=200,
    )
    responses.add(
        responses.HEAD,
        url,
        status=200,
    )


class TestEnvTemplate:

    @pytest.fixture(scope="class", autouse=True)
    def init_env(self):
        base_dir = Path(__file__).resolve().parents[4]

        environ["CI_PROJECT_DIR"] = str((base_dir / "test_data/test_template/projects").resolve())
        environ["CLUSTER_NAME"] = "cluster-01"
        environ["GITHUB_TOKEN"] = "token"
        environ["GITHUB_USER_NAME"] = "user"

        yield

        environ.pop("CI_PROJECT_DIR", None)
        environ.pop("CLUSTER_NAME", None)
        environ.pop("ENVIRONMENT_NAME", None)

    @responses.activate
    def test_new_logic_with_dd(self, mock_aio_response):
        set_env("env-01")

        mock_metadata(mock_aio_response)
        mock_dd_exists(mock_aio_response, exists=True)
        mock_dd_response()
        mock_zip(STAGING_ZIP_URL)

        process_env_template()

        assert len(responses.calls) == 3
        assert responses.calls[0].request.url == DD_URL
        assert responses.calls[1].request.url == STAGING_ZIP_URL

    @responses.activate
    def test_new_logic_with_zip(self, mock_aio_response):
        set_env("env-01")

        mock_metadata(mock_aio_response, repeat=2)
        mock_dd_exists(mock_aio_response, exists=False)

        mock_aio_response.head(ZIP_URL, payload="", status=200)
        mock_zip(ZIP_URL)

        process_env_template()

        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == ZIP_URL

    @responses.activate
    def test_old_logic_with_dd(self):
        set_env("env-02")

        responses.add(responses.GET, METADATA_URL, body=metadata_xml, content_type="application/xml", status=200)
        mock_dd_exists(exists=True)
        responses.add(responses.GET, DD_URL, json=dd_json, status=200)
        mock_zip(TMPL_ZIP_URL)

        process_env_template()

        assert len(responses.calls) == 5
        assert responses.calls[2].request.url == DD_URL
        assert responses.calls[4].request.url == TMPL_ZIP_URL

    @responses.activate
    def test_old_logic_with_zip(self):
        set_env("env-02")

        tmpl_metadata_url = f"{TMPL_SNAPSHOT_BASE}/{BASE_PATH}/maven-metadata.xml"
        tmpl_zip_url = f"{TMPL_SNAPSHOT_BASE}/{BASE_PATH}/{ARTIFACT_NAME}.zip"

        responses.add(responses.GET, METADATA_URL, body=metadata_xml, content_type="application/xml", status=404)
        responses.add(responses.GET, tmpl_metadata_url, body=metadata_xml, content_type="application/xml", status=200)

        mock_zip(tmpl_zip_url)

        process_env_template()

        assert len(responses.calls) == 4
        assert responses.calls[3].request.url == tmpl_zip_url
