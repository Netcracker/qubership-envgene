class IntergrationConfigLoader:
    def __init__(self, data: dict) -> None:
        self._load(data)

    def _load(self, data):
        if data:
            for key, val in data.items():
                if isinstance(data[key], dict):
                    if key == 'cp_discovery':
                        setattr(self, key, data[key])
                else:
                    setattr(self, key, val)

    def to_dict(self):
        output = {}
        for attribute in self.__dict__.keys():
            if attribute[:2] != '__' and attribute != 'data':
                value = getattr(self, attribute)
                if not callable(value):
                    output.update({attribute: value})
        return output
