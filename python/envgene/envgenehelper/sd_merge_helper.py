from envgenehelper import *

MERGE_IMPOSSIBLE="SD merge error:\nDelta SD contains a new applications, but doesn't contain this application in the deployGraph.\nSD Merge is impossible."
SD_HEADER_ERROR="SD merge error:\nFull and Delta SDs must have identical values for version, type, and deployMode\nMerge is impossible"
NEW_CHUNK_ERROR="SD merge error:\nDelta SD contains a new chunk\nSD Merge is impossible."
NO_DEPLOY_GRAPH_ERROR="SD merge error:\nDelta SD contains deployGraph, but Full SD doesn't contain deployGraph.\nSD Merge is impossible."

def pre_validate(data1, data2):
    header_attrs = ["version", "type", "deployMode"]
    for attr in header_attrs:
        if attr in data1.keys() and attr in data2.keys():
            if data1[attr] != data2[attr]:
                error(SD_HEADER_ERROR)
        else:
            error(SD_HEADER_ERROR)
    if "deployGraph" in data2.keys() and "deployGraph" not in data1.keys():
        error(NO_DEPLOY_GRAPH_ERROR)

def get_app_name(str):
    return str[0:str.find(":")]

def error(str):
    logger.error(str)
    raise ValueError(str)

def checkDeployGraph(str, data):
    result = False
    if "deployGraph" not in data.keys():
        return False
    for entry in data["deployGraph"]:
        for c in entry["apps"]:
            if str.lower() in c.lower():
                return True
    return result

# Returns False if target contains a criteria and its value is not matched with delta's value. Otherwise returns True
def check_criteria(target, delta, criteria):
    result = True
    for c in criteria:
        if c in target:
            result = result and (target[c] == delta[c])
 #   if not result:
 #       error(MERGE_IMPOSSIBLE)
    return result

def add_app(entry, list) -> int:
    touched = False
    for i in range(len(list)):
        if (isinstance(entry, ruyaml.CommentedMap) and get_app_name(list[i]["version"]) == get_app_name(entry["version"]) and check_criteria(entry, list[i], ["deployPostfix","alias"])) or (not isinstance(entry, ruyaml.CommentedMap) and get_app_name(list[i]) == get_app_name(entry)):
            logger.info(f"Replaced value: {entry}")
            list[i] = entry
            touched = True
    if not touched:
        logger.info(f"Appended value: {entry}")
        list.append(entry)
    return 1

def merge(data1, data2, target_path):
    logger.info(f"Full SD: {data1}")
    logger.info(f"Delta SD: {data2}")

    pre_validate(data1, data2)
    counter_ = 0
    apps_list = data1["applications"].copy()
    length = len(data2["applications"])

    # stage 1: Stage delta_sd applications with suitable deployGraph
    for j in data2["applications"]:
        if (isinstance(j, ruyaml.CommentedMap) and checkDeployGraph(get_app_name(j["version"]), data2)) or (not isinstance(j, ruyaml.CommentedMap) and checkDeployGraph(get_app_name(j), data2)):
            counter_ += add_app(j, apps_list)

    # stage 2: Merge rest of applications
    for i in range(len(apps_list)):
        for j in range(len(data2["applications"])):
            if "deployGraph" not in data2.keys() and ((isinstance(apps_list[i], ruyaml.CommentedMap) and get_app_name(apps_list[i]["version"]) == get_app_name(data2["applications"][j]["version"]) and check_criteria(apps_list[i], data2["applications"][j], ["deployPostfix","alias"])) or (not isinstance(apps_list[i], ruyaml.CommentedMap) and get_app_name(apps_list[i]) == get_app_name(data2["applications"][j]))):
                apps_list[i] = data2["applications"][j]
                counter_ += 1

    logger.info(f"counter_: {counter_}")
    logger.info(f"length: {length}")
    if counter_ < length:
        error(MERGE_IMPOSSIBLE)
    data1["applications"] = apps_list

    if "deployGraph" in data2.keys():
        # merge DeployGraph
        counter = 0
        length = len(data2["deployGraph"])
        for i in data1["deployGraph"]:
            for j in data2["deployGraph"]:
                if i["chunkName"] == j["chunkName"]:
                    in_first = set(i["apps"])
                    in_second = set(j["apps"])
                    in_second_but_not_in_first = in_second - in_first
                    i["apps"] = i["apps"] + list(in_second_but_not_in_first)
                    counter += 1
        if counter < length:
            error(NEW_CHUNK_ERROR)

    writeYamlToFile(target_path, data1)
