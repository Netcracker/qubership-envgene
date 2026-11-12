import io
import json
import tarfile
from pathlib import Path

from deepdiff import DeepDiff
from envgenehelper.deploy_plan_adapter import DeployPlanEntity
from sbom_generator.utils.models import Extensions

TESTS_DIR = Path(__file__).resolve().parent


def deepdiff_default(a, b, **kwargs):
    return DeepDiff(a, b, ignore_order=True, **kwargs)


def load_json(path: Path):
    with open(TESTS_DIR.joinpath(f'{path}.{Extensions.JSON.value}'), 'r', encoding='utf-8') as file:
        return json.load(file)


def make_chart_tgz(files: dict[str, str]) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w:gz') as tar:
        for name, content in files.items():
            data = content.encode('utf-8')
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


def make_app(version: str) -> DeployPlanEntity:
    return DeployPlanEntity(version=version, deploy_postfix='any')
