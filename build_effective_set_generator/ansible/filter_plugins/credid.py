import re

def credid(val):
    match = re.search(r".*\('([^']+)'\).(\w+)", val)
    if match:
        cred_name = match.group(1)
        cred_property = match.group(2)
    return [cred_name, cred_property]


class FilterModule(object):
    filter_map = {
        'credid': credid
    }

    def filters(self):
        return self.filter_map
