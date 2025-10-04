from envgenehelper import *

MERGE_IMPOSSIBLE = "SD merge error:\nDelta SD contains a new applications, but doesn't contain this application in the deployGraph.\nSD Merge is impossible."
NEW_CHUNK_ERROR = "SD merge error:\nDelta SD contains a new chunk\nSD Merge is impossible."
NO_DEPLOY_GRAPH_ERROR = "SD merge error:\nDelta SD contains deployGraph, but Full SD doesn't contain deployGraph.\nSD Merge is impossible."


def get_app_name(name: str):
    return name[0:name.find(":")]


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


def error(str):
    logger.error(str)
    raise ValueError(str)


def check_deploy_graph(app_name: str, data: dict) -> bool:
    deploy_graph = data.get("deployGraph")
    if not deploy_graph:
        return False

    for entry in deploy_graph:
        for app in entry.get("apps", []):
            if app_name.lower() in app.lower():
                return True
    return False


# Returns False if target contains a criteria and its value is not matched with delta's value. Otherwise returns True
def check_criteria(target, delta, criteria):
    result = True
    for c in criteria:
        if c in target:
            result = result and (target[c] == delta[c])
    #   if not result:
    #       error(MERGE_IMPOSSIBLE)
    return result


def add_app(entry, apps: list) -> int:
    entry_name = get_app_name(entry["version"])

    for i, app in enumerate(apps):
        app_name = get_app_name(app["version"])

        if isinstance(entry, ruyaml.CommentedMap):
            if app_name == entry_name and check_criteria(entry, app, ["deployPostfix", "alias"]):
                logger.info(f"Replaced value: {entry}")
                apps[i] = entry
                return 1

        elif app_name == entry_name:
            logger.info(f"Replaced value: {entry}")
            apps[i] = entry
            return 1

    logger.info(f"Appended value: {entry}")
    apps.append(entry)
    return 1

def merge(full_sd, delta_sd):
    """
    Merge Delta SD into Full SD using `basic-merge` rules on sd_data:
      1. Matching App => update version from Delta
      2. Duplicating App => leave as-is
      3. New App => append to Full SD
      4. Output contains only `applications` key
    """
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

    # Stage 3: Return result with only `applications`
    return {"applications": result_apps}


def extended_merge(full_sd, delta_sd):
    # Merges delta SD into full SD by updating or adding matching apps, ensuring deployGraph consistency
    logger.info("Inside extended_merge")
    logger.info(f"Full SD: {full_sd}")
    logger.info(f"Delta SD: {delta_sd}")
    if "deployGraph" not in delta_sd.keys():
        error(NO_DEPLOY_GRAPH_ERROR)
    counter_ = 0
    apps_list = full_sd["applications"].copy()
    length = len(delta_sd["applications"])

    # find applications with suitable deployGraph
    for j in delta_sd["applications"]:
        if check_deploy_graph(get_app_name(j["version"]), delta_sd):
            counter_ += add_app(j, apps_list)

    # merge rest of applications
    for i in range(len(apps_list)):
        for j in range(len(delta_sd["applications"])):
            apps_item = apps_list[i]
            delta_item = delta_sd["applications"][j]
            same_app_name = get_app_name(apps_item["version"]) == get_app_name(delta_item["version"])

            if isinstance(apps_item, ruyaml.CommentedMap):
                if same_app_name and check_criteria(apps_item, delta_item, ["deployPostfix", "alias"]):
                    apps_list[i] = delta_item
                    counter_ += 1
            else:
                if same_app_name:
                    apps_list[i] = delta_item
                    counter_ += 1

    logger.info(f"counter_: {counter_}")
    if counter_ < length:
        error(MERGE_IMPOSSIBLE)
    full_sd["applications"] = apps_list

    # merge DeployGraph
    counter = 0
    length = len(delta_sd["deployGraph"])
    for i in full_sd["deployGraph"]:
        for j in delta_sd["deployGraph"]:
            if i["chunkName"] == j["chunkName"]:
                in_first = set(i["apps"])
                in_second = set(j["apps"])
                in_second_but_not_in_first = in_second - in_first
                i["apps"] = i["apps"] + list(in_second_but_not_in_first)
                counter += 1
    if counter < length:
        error(NEW_CHUNK_ERROR)

    return full_sd


def basic_merge(full_sd, delta_sd):
    """
    Merge Delta SD into Full SD using `basic-merge` rules:
      1. Matching App => update version from Delta
      2. Duplicating App => leave as-is
      3. New App => append to Full SD
      4. Output contains only `applications` key
    """
    logger.info(f"Inside basic_merge")
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

    full_sd["applications"] = result_apps
    # Stage 3: Return result
    return full_sd


def basic_exclusion_merge(full_sd, delta_sd):
    """
    Merge Delta SD into Full SD using `basic-exclusion-merge` rules:
      1. Matching App => update version from Delta
      2. Duplicating App => remove from Full SD
      3. New App => log warning
      4. Output contains only `applications` key
    """
    logger.info(f"Inside basic_exclusion_merge")
    logger.info(f"Full SD: {full_sd}")
    logger.info(f"Delta SD: {delta_sd}")
    full_apps = full_sd.get("applications", [])
    delta_apps = delta_sd.get("applications", [])
    result_apps = []

    # Track matched delta apps
    matched_delta_indices = set()

    # Stage 1: Process full SD
    for f_app in full_apps:
        keep = True
        for i, d_app in enumerate(delta_apps):
            if is_duplicating(f_app, d_app):
                # Rule 3: Remove duplicating
                keep = False
                matched_delta_indices.add(i)
                break
            elif is_matching(f_app, d_app):
                # Rule 1: Replace matching
                result_apps.append(d_app)
                keep = False
                matched_delta_indices.add(i)
                break
        if keep:
            result_apps.append(f_app)

    # Stage 2: Warn about new apps
    for i, d_app in enumerate(delta_apps):
        if i not in matched_delta_indices:
            # Rule 2: New Application, rejects
            logger.info(f"Warning: New application '{get_app_name_sd(d_app)}' ignored (not present in Full SD)")

    full_sd["applications"] = result_apps
    # Stage 3: Return result
    return full_sd
