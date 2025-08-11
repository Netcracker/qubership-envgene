from typing import Any
from typing import NamedTuple

import ruyaml.representer


class YamlIndent(NamedTuple):
    mapping: int
    sequence: int
    offset: int


def create_yaml_processor(*, indent: YamlIndent) -> ruyaml.main.YAML:
    def _null_representer(self: ruyaml.representer.BaseRepresenter, data: None) -> Any:
        return self.represent_scalar('tag:yaml.org,2002:null', 'null')

    yaml = ruyaml.main.YAML()
    yaml.indent(**indent._asdict())
    yaml.preserve_quotes = True  # type: ignore[assignment]
    yaml.width = 4096  # type: ignore[assignment]
    yaml.Representer.add_representer(type(None), _null_representer)
    return yaml
