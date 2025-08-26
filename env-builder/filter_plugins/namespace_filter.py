from ansible.errors import AnsibleFilterError


def filter_namespaces(namespaces: list[dict], filter: str, bgd_object: dict) -> list[dict]:
    for ns in namespaces:
        ns["_rendered_name"] = (
            ns["template_path"].split("/")[-1]
            .replace(".yml.j2", "")
            .replace(".yaml.j2", "")
        )
    if not filter:
        return namespaces
    is_exclusion = filter.startswith("!")
    if is_exclusion: filter = filter[1:]
    selectors = [s.strip() for s in filter.split(",") if s.strip()]
    resolved_filter = []

    for sel in selectors:
        if not sel.startswith("@"):
            resolved_filter.append(sel)
            continue
        alias = sel[1:]
        if alias not in bgd_object:
            raise AnsibleFilterError(f"Unknown alias in NS_BUILD_FILTER: {sel}")
        name = bgd_object[alias]["name"]

        resolved_filter.append(name)
    if is_exclusion:
        filtered_namespaces = [ns for ns in namespaces if ns["_rendered_name"] not in resolved_filter]
    else:
        filtered_namespaces = [ns for ns in namespaces if ns["_rendered_name"] in resolved_filter]
    return filtered_namespaces

class FilterModule:
    def filters(self):
        return {"filter_namespaces": filter_namespaces}
