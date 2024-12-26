new_dict = {}
def flatten_dict(d, env_name, new_dict, sep='-'):
    for k, v in d.items():
        if isinstance(v, dict):
            for key, value in d.items():
                if isinstance(value, dict):
                    new_key = f"{env_name}{sep}{key}"
                    flatten_dict(value, new_key, new_dict, sep=sep)
                else:
                    if env_name in new_dict.keys() and isinstance(new_dict[env_name], dict) :
                        new_dict[env_name].update({key:value})
                    else:
                        new_dict[env_name] = {key:value}
        else:
            if env_name in new_dict.keys() and isinstance(new_dict[env_name], dict) :
                new_dict[env_name].update({k:v})
            else:
                new_dict[env_name] = {k:v}
    return new_dict

class FilterModule(object):

    def filters(self):
        return {'flatten_dict': flatten_dict}
