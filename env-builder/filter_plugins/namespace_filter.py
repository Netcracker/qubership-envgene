from ansible.errors import AnsibleFilterError


def filter_namespaces(namespaces, bgd_object, filter):
    for ns in namespaces:
        ns["_rendered_name"] = (
            ns["template_path"].split("/")[-1]
            .replace(".yml.j2", "")
            .replace(".yaml.j2", "")
        )
    if not filter:
        # what to return?
        return
    is_exclusion = filter.startswith("!")
    selectors = [s.strip() for s in filter.split(",") if s.strip()]
    resolved_filter = []

    for sel in selectors:
        if sel.startswith("@"):
            alias = sel[1:]
            if alias not in bgd_object:
                raise AnsibleFilterError(f"Unknown alias in NS_BUILD_FILTER: {sel}")
            name = bgd_object[alias]["name"]
        else:
            name = sel

        resolved_filter.append(name)
    return ??


class FilterModule:
    def filters(self):
        return {"filter_namespaces": filter_namespaces}
