from envgenehelper import *

SD_FILE_NAME = "sd.yaml"
DELTA_SD_FILE_NAME = "delta_sd.yaml"


def get_app_name_sd(app):
    return app.get("version", "").split(':')[0]


def get_version(app):
    return app.get("version", "").split(":", 1)[1]


def is_matching(app1, app2):
    return (
            get_app_name_sd(app1) == get_app_name_sd(app2) and
            app1.get("deployPostfix") == app2.get("deployPostfix")
    )


def is_duplicating(app1, app2):
    return (
            is_matching(app1, app2) and
            get_version(app1) == get_version(app2)
    )


def basic_merge_multiple(sd_list: list):
    result_sd = sd_list[0]
    for next_sd in sd_list[1:]:
        result_sd = basic_merge(result_sd, next_sd)
    return result_sd


def basic_merge(full_sd, delta_sd):
    """
    Merge Delta SD into Full SD using `basic-merge` rules:
      1. Matching App => update version from Delta
      2. Duplicating App => leave as-is
      3. New App => append to Full SD
      4. Output contains only `applications` key
    """
    logger.info("Inside basic_merge")
    logger.info(f"Full SD: {full_sd}")
    logger.info(f"Delta SD: {delta_sd}")

    full_apps = full_sd.get("applications", [])
    delta_apps = delta_sd.get("applications", [])
    result_apps = []

    # Stage 1: Replace Matching apps with Delta versions
    for f_app in full_apps:
        replaced = False
        for d_app in delta_apps:
            if is_duplicating(f_app, d_app):
                # Rule 2: Duplicating, keep Full SD version
                result_apps.append(f_app)
                replaced = True
                break
            elif is_matching(f_app, d_app):
                # Rule 1: Matching, replace with Delta version
                result_apps.append(d_app)
                replaced = True
                break
        if not replaced:
            # No match found: keep Full SD version
            result_apps.append(f_app)

    # Stage 2: Add New applications from Delta SD
    for d_app in delta_apps:
        if not any(is_matching(f_app, d_app) for f_app in full_apps):
            # Rule 3: New Application, append
            result_apps.append(d_app)

    return {"applications": result_apps}


def basic_exclusion_merge(full_sd, delta_sd):
    """
    Merge Delta SD into Full SD using `basic-exclusion-merge` rules:
      1. Matching App, New App => WARN
      2. Duplicating App => remove from Full SD
      3. Output contains only `applications` key
    """
    logger.info("Inside basic_exclusion_merge")
    logger.info(f"Full SD: {full_sd}")
    logger.info(f"Delta SD: {delta_sd}")
    full_apps = full_sd.get("applications", [])
    delta_apps = delta_sd.get("applications", [])
    result_apps = []

    matched_delta_indices = set()

    # Stage 1: Process full SD
    for f_app in full_apps:
        keep = True
        for i, d_app in enumerate(delta_apps):
            if is_duplicating(f_app, d_app):
                # Rule 2: Remove duplicating
                keep = False
                matched_delta_indices.add(i)
                break
            elif is_matching(f_app, d_app):
                # Rule 1: Warn about matching apps
                logger.warning(f"Warning: Update application '{get_app_name_sd(d_app)}' ignored (matching in Full SD)")
                matched_delta_indices.add(i)
                break
        if keep:
            result_apps.append(f_app)

    # Rule 1: Warn about new apps
    for i, d_app in enumerate(delta_apps):
        if i not in matched_delta_indices:
            # Rule 2: New Application, rejects
            logger.warning(f"Warning: New application '{get_app_name_sd(d_app)}' ignored (not present in Full SD)")

    return {"applications": result_apps}


class MergeType(Enum):
    REPLACE = "replace"
    BASIC = "basic-merge"
    BASIC_EXCLUSION = "basic-exclusion-merge"

    @classmethod
    def from_value(cls, value: str):
        if not isinstance(value, str):
            raise ValueError(f"SD_REPO_MERGE_MODE value: '{value}' cannot be non-string")
        value_lower = value.strip().lower()
        for member in cls:
            if member.value == value_lower:
                return member
        valid_values = [member.value for member in cls]
        raise ValueError(
            f"Invalid SD_REPO_MERGE_MODE: '{value}'. Valid values are: {valid_values}"
        )


def calculate_merge_mode(sd_merge_mode, sd_delta) -> MergeType:
    if sd_merge_mode is not None:
        effective_merge_mode = MergeType.from_value(sd_merge_mode)
    # sd_delta var is deprecated
    elif sd_delta == "false":
        effective_merge_mode = MergeType.REPLACE
        logger.info(
            f"SD_REPO_MERGE_MODE not passed. Calculated based on SD_DELTA={sd_delta}: {effective_merge_mode.value}")
    else:
        effective_merge_mode = MergeType.BASIC
        logger.info(f"SD_REPO_MERGE_MODE not passed. Default value: {effective_merge_mode.value}")
    return effective_merge_mode


def get_sd_dir() -> Path:
    return Path(f'{get_current_env_dir_from_env_vars()}/{INVENTORY_DIR_NAME}/solution-descriptor/')


def get_sd_dir_by_env_cluster_name(cluster_name, environment_name) -> Path:
    instance_dir = get_env_dir_by_env_cluster_name(cluster_name, environment_name)
    return Path(f'{instance_dir}/{INVENTORY_DIR_NAME}/solution-descriptor/')
