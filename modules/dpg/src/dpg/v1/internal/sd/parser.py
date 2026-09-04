import yaml
from pathlib import Path
from packaging.version import Version

from dpg.v1.internal.sd.models import SolutionDescriptor, SolutionDescriptor_2_0, SolutionDescriptor_2_1, \
    SolutionDescriptor_2_2


class SolutionDescriptorParser:
    @staticmethod
    def parse(filepath: Path = None, content: dict = None):
        if filepath is not None and content is None:
            if not filepath.exists():
                raise Exception(f"File {filepath} doesn't exists..")
            content = yaml.load(filepath.read_text(), Loader=yaml.SafeLoader)

        version = Version(str(content.get('version')))
        if version is None:
            raise Exception("Incorrect version of Solution Descriptor..")

        match version:
            case Version("2.0"):
                return SolutionDescriptor_2_0(**content)
            case Version("2.1"):
                return SolutionDescriptor_2_1(**content)
            case Version("2.2"):
                return SolutionDescriptor_2_2(**content)
            case _:
                raise Exception(f"Version {version} doesn't support.")
