#!/usr/bin/python
from os import getenv

def secrets(val):
    if "username" in val or "password" in val or "secret" in val:
        credential_id = (val.rsplit('.', 1)[:-1][0]).replace('collector.','').replace('.','-')
        value_suffix = val.split('.')[-1]
        cmdb_var = f"${{creds.get(\"{credential_id}\").{value_suffix}}}"
    else:
        credential_id = val.replace('.','-')
        cmdb_var = f"${{creds.get(\"{credential_id}\")}}"
    return cmdb_var

class FilterModule(object):
    filter_map = {
        'secrets': secrets
    }

    def filters(self):
        return self.filter_map
