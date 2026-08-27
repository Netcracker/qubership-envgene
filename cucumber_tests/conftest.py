import sys
import pytest
import os
import subprocess
import time
import zipfile
import urllib.request
from pathlib import Path
from cucumber_tests.framework.workspace import EnvGeneWorkspace
from cucumber_tests.shared_steps.common_steps import *

# Fixture data for the mock_nexus server: one JSON manifest per artifact, plus the Jinja
# templates that get zipped up for the env-template artifacts. Kept as real files under
# test_data/mock_nexus/ (instead of inline strings) so their content is readable and diffable.
_MOCK_NEXUS_FIXTURES = Path(__file__).parent / "test_data" / "mock_nexus"


# The two manifest shapes every mock_nexus artifact needs: a plain Maven env-template artifact
# (configurations/maven_repository/artifacts[].id) or an application deployment descriptor
# (applications/deployGraph). Every manifest in this suite is one of these two shapes with only
# the coordinate/name/version/deployPostfix differing, so each is kept as a single template file
# with placeholders instead of one near-identical file per artifact.
_MAVEN_ARTIFACT_MANIFEST_PATH = _MOCK_NEXUS_FIXTURES / "manifests" / "maven-artifact.json"
_APP_DEPLOYMENT_DESCRIPTOR_PATH = _MOCK_NEXUS_FIXTURES / "manifests" / "app-deployment-descriptor.json"


def _write_maven_manifest(dest_dir: Path, filename: str, artifact_id: str, version: str) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    content = _MAVEN_ARTIFACT_MANIFEST_PATH.read_text(encoding="utf-8") \
        .replace("__ARTIFACT_ID__", artifact_id).replace("__VERSION__", version)
    (dest_dir / filename).write_text(content, encoding="utf-8")


def _write_app_manifest(dest_dir: Path, filename: str, app_name: str, version: str, deploy_postfix: str) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    content = _APP_DEPLOYMENT_DESCRIPTOR_PATH.read_text(encoding="utf-8") \
        .replace("__APP_NAME__", app_name).replace("__VERSION__", version) \
        .replace("__DEPLOY_POSTFIX__", deploy_postfix)
    (dest_dir / filename).write_text(content, encoding="utf-8")


def _add_dir_to_zip(zf: zipfile.ZipFile, source_dir: Path, arc_prefix: str) -> None:
    for path in sorted(source_dir.rglob("*")):
        if path.is_file():
            zf.write(path, arcname=f"{arc_prefix}/{path.relative_to(source_dir).as_posix()}")


def _build_env_template_zip(dest_path: Path, bundle_name: str) -> None:
    """Zip templates/ from the shared "common" fixtures plus the bundle's own overrides,
    mirroring the "{{ templates_dirs.common }}" split the templates themselves reference."""
    with zipfile.ZipFile(dest_path, "w") as z:
        _add_dir_to_zip(z, _MOCK_NEXUS_FIXTURES / "common", "templates")
        _add_dir_to_zip(z, _MOCK_NEXUS_FIXTURES / bundle_name, "templates")


# Template Descriptor shared by the envTemplate.bgNsArtifacts.origin/peer mock artifacts. Both
# roles are byte-identical except for which BG Domain role they name - that difference is not
# optional duplication: render_config_env.py's _find_ns_config_by_name() looks up the
# role-specific namespace by matching this exact name against the common template's namespace
# name, so the origin artifact's namespace MUST be named "bss-origin" and the peer artifact's
# "bss-peer" for either to be picked up at all. Kept as one file (like the rest of mock_nexus/)
# with a __ROLE__ placeholder instead of two hand-copied fixture files.
_BG_ROLE_TEMPLATE_PATH = _MOCK_NEXUS_FIXTURES / "bg-role-template" / "env_templates" / "test.yml"


def _build_bg_role_zip(dest_path: Path, role: str) -> None:
    """Zip a single env_templates/test.yml, substituting the given BG Domain role ("origin" or
    "peer") into _BG_ROLE_TEMPLATE_PATH's __ROLE__ placeholder. No "common" merge is needed:
    this file's own "{{ templates_dirs.common }}" paths resolve against the
    separately-downloaded common artifact, not against this zip's own contents."""
    content = _BG_ROLE_TEMPLATE_PATH.read_text(encoding="utf-8").replace("__ROLE__", role)
    with zipfile.ZipFile(dest_path, "w") as z:
        z.writestr("templates/env_templates/test.yml", content)


@pytest.fixture(scope="session", autouse=True)
def mock_nexus(tmp_path_factory):
    base_dir = tmp_path_factory.mktemp("mock_nexus")

    # "test-artifact:v1" - the default env template, used as-is by most scenarios and as the
    # BG Domain origin-side artifact in the BGD warmup scenarios.
    art_dir = base_dir / "release" / "org" / "test" / "test-artifact" / "v1"
    _write_maven_manifest(art_dir, "test-artifact-v1.json", "test-artifact", "v1")
    _build_env_template_zip(art_dir / "test-artifact-v1.zip", "default-env-template")

    # "test-artifact:v2" - the BG Domain peer-side artifact pin used in the BGD warmup scenario,
    # deliberately a different version string from "test-artifact:v1" so the before/after sync
    # assertion is meaningful. Manifest only, no zip: warmup (bg_manage.py's
    # sync_bg_ns_artifacts) only ever compares/overwrites this string in env_definition.yml and
    # copies the *already-rendered* namespace directory on disk - it never downloads the
    # artifact. Confirmed by a full-suite run: zero HTTP requests for this path.
    art_v2_dir = base_dir / "release" / "org" / "test" / "test-artifact" / "v2"
    _write_maven_manifest(art_v2_dir, "test-artifact-v2.json", "test-artifact", "v2")

    # "origin-template:v1" / "peer-template:v1" - genuinely distinct Environment Template
    # artifacts (not just another version of test-artifact) referenced from
    # envTemplate.bgNsArtifacts.origin/peer. Proves the origin/peer sides of a BG Domain can
    # render structurally different namespace content, not just a different template version.
    for _role in ("origin", "peer"):
        _role_dir = base_dir / "release" / "org" / "test" / f"{_role}-template" / "v1"
        _write_maven_manifest(_role_dir, f"{_role}-template-v1.json", f"{_role}-template", "v1")
        _build_bg_role_zip(_role_dir / f"{_role}-template-v1.zip", _role)

    # "project-env-template:v1.2.3" - used by the env-inventory-generation and template-version
    # scenarios, where the artifact's own semantic version string is what's under test. Manifest
    # only, no zip: none of those scenarios render templates, so nothing ever downloads this
    # artifact either (confirmed the same way as test-artifact:v2 above).
    pet_dir = base_dir / "release" / "org" / "test" / "project-env-template" / "v1.2.3"
    _write_maven_manifest(pet_dir, "project-env-template-v1.2.3.json", "project-env-template", "v1.2.3")

    test_app_dir = base_dir / "release" / "com" / "test" / "test_app_artifact" / "1.0.0"
    _write_app_manifest(test_app_dir, "test_app_artifact-1.0.0.json", "test_app", "1.0.0", "dp1")

    test_app2_dir = base_dir / "release" / "com" / "test" / "test_app_2_artifact" / "2.0.0"
    _write_app_manifest(test_app2_dir, "test_app_2_artifact-2.0.0.json", "test_app_2", "2.0.0", "dp2")

    proc = subprocess.Popen([sys.executable, "cucumber_tests/mock_server.py", "8000", str(base_dir)])
    
    # Wait for the mock server to start
    for i in range(10):
        try:
            urllib.request.urlopen("http://localhost:8000/")
            break
        except Exception:
            time.sleep(0.5)
    else:
        print("MOCK SERVER FAILED TO START ON PORT 8000")

    yield
    proc.terminate()
    proc.wait()

@pytest.fixture
def workspace(tmp_path):
    return EnvGeneWorkspace(tmp_path)


_XFAIL_REASONS = {
    "xfail": "Known framework gap: ENVGENE_PROJECT is not validated by the orchestrator.",
    "xfail_cli_npe": "Known bug: Calculator CLI throws a NullPointerException on "
                      "NamespaceDTO.isCleaned() when matching BG Domain deployPostfix.",
    "xfail_cli_no_hierarchy_rule": "Known gap: the hierarchy validation rule (Tenant level "
                                    "parameters cannot reference Cloud/Namespace level parameters) "
                                    "is not enforced by the Calculator CLI.",
    "xfail_cli_no_context_rule": "Known gap: the cross-context validation rule (e2eParameters/"
                                  "technicalConfigurationParameters/deployParameters cannot "
                                  "reference each other) is not enforced by the Calculator CLI.",
    "xfail_cli_macro_ns_timeout": "Known bug: a macro reference resolved across hierarchy levels "
                                   "is dropped from the effective set deployment parameters.",
}


def pytest_bdd_apply_tag(tag, function):
    """Handle custom Gherkin tags as pytest marks."""
    if tag in _XFAIL_REASONS:
        marker = pytest.mark.xfail(reason=_XFAIL_REASONS[tag], strict=True)
        marker(function)
        return True
    return None
