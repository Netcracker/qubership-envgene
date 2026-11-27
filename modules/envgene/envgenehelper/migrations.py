from collections.abc import Mapping, MutableMapping

from ruyaml import CommentedSeq

from envgene_shared.utils.logger import logger

PARAMETER_SET_TAGS = ("deployParameterSets", "e2eParameterSets", "technicalConfigurationParameterSets")


def migrate_empty_parameter_sets(obj, path) -> None:
    if not isinstance(obj, MutableMapping):
        return
    for tag in PARAMETER_SET_TAGS:
        value = obj.get(tag)
        if isinstance(value, Mapping) and not value:
            logger.warning(f"{path}: {tag} is an empty mapping, migrated to an empty list. Write '{tag}: []'.")
            obj[tag] = CommentedSeq()
