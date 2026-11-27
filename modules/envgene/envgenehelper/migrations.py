from collections.abc import Mapping, MutableMapping

from ruyaml import CommentedSeq

from envgene_shared.utils.logger import logger

PARAMETER_SET_TAGS = ("deployParameterSets", "e2eParameterSets", "technicalConfigurationParameterSets")


# Our own samples wrote an empty mapping for these tags until v3.28, so projects that copied them keep
# `deployParameterSets: {}` in templates of their own. A GSF upgrade never rewrites those templates, so the
# mapping arrives again on every run. An empty mapping carries no parameter set name, so the store turns it
# into an empty list before the schema check and the build goes on. A mapping with keys is not migrated: the
# schema rejects it and only the author knows which list of names was meant.
def migrate_empty_parameter_sets(obj, path) -> None:
    if not isinstance(obj, MutableMapping):
        return
    for tag in PARAMETER_SET_TAGS:
        value = obj.get(tag)
        if isinstance(value, Mapping) and not value:
            logger.warning(f"{path}: {tag} is an empty mapping, migrated to an empty list. Write '{tag}: []'.")
            obj[tag] = CommentedSeq()
