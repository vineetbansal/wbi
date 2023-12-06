import yaml


# https://stackoverflow.com/questions/38034377/object-like-attribute-access-for-nested-dictionary
class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

    @classmethod
    def from_nested_dicts(cls, data):
        """Construct nested AttrDicts from nested dictionaries."""
        if not isinstance(data, dict):
            return data
        else:
            return cls({key: cls.from_nested_dicts(data[key]) for key in data})


class Config(object):
    def __init__(self, name, filepath):
        self.name = name
        self.namespace = None
        self.file_paths = [filepath]
        self.init_from_file(filepath)

    def __getattr__(self, item):
        return getattr(self.namespace, item)

    def init_from_file(self, filepath):
        with open(filepath) as f:
            attr_dict = yaml.load(f, Loader=yaml.FullLoader)
        self.namespace = AttrDict.from_nested_dicts(attr_dict)
