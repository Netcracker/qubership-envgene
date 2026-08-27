import sys
import pytest
import os
import shutil
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


def _write_manifest(dest_dir: Path, filename: str) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(_MOCK_NEXUS_FIXTURES / "manifests" / filename, dest_dir / filename)


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


@pytest.fixture(scope="session", autouse=True)
def mock_nexus(tmp_path_factory):
    base_dir = tmp_path_factory.mktemp("mock_nexus")

    # "test-artifact:v1" - the default env template, used as-is by most scenarios and as the
    # BG Domain origin-side artifact in the BGD warmup scenarios.
    art_dir = base_dir / "release" / "org" / "test" / "test-artifact" / "v1"
    _write_manifest(art_dir, "test-artifact-v1.json")
    _build_env_template_zip(art_dir / "test-artifact-v1.zip", "default-env-template")

    # "test-artifact:v2" - the BG Domain peer-side artifact in the BGD warmup scenarios: a newer
    # version of the SAME template artifact (not a differently-named one), deliberately a
    # different template from v1 so the two can be told apart.
    art_v2_dir = base_dir / "release" / "org" / "test" / "test-artifact" / "v2"
    _write_manifest(art_v2_dir, "test-artifact-v2.json")
    _build_env_template_zip(art_v2_dir / "test-artifact-v2.zip", "bg-peer-env-template")

    # "project-env-template:v1.2.3" - used by the env-inventory-generation and template-version
    # scenarios, where the artifact's own semantic version is what's under test.
    pet_dir = base_dir / "release" / "org" / "test" / "project-env-template" / "v1.2.3"
    _write_manifest(pet_dir, "project-env-template-v1.2.3.json")
    _build_env_template_zip(pet_dir / "project-env-template-v1.2.3.zip", "env-inventory-template")

    test_app_dir = base_dir / "release" / "com" / "test" / "test_app_artifact" / "1.0.0"
    _write_manifest(test_app_dir, "test_app_artifact-1.0.0.json")

    test_app2_dir = base_dir / "release" / "com" / "test" / "test_app_2_artifact" / "2.0.0"
    _write_manifest(test_app2_dir, "test_app_2_artifact-2.0.0.json")

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
