import os
import json


FOLDER = '/kb/KB'
META = 'meta.json'


class MetaKb(type):
    """ToDo"""
    def __getattr__(self, item):
        if not os.path.exists(os.path.join(FOLDER, item, META)):
            raise ValueError
        meta = json.loads(open(os.path.join(FOLDER, item, META), encoding='utf-8').read())
        return meta['title']


class Kb(object, metaclass=MetaKb):
    """Vulnerability title dispatcher."""
