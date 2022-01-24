"""KB - Knowledge base.. ToDo"""
import os
import json


FOLDER = '/kb/KB'
META = 'meta.json'


class MetaKb(type):
    """ToDo"""
    def __getattr__(cls, item):
        if not os.path.exists(os.path.join(FOLDER, item, META)):
            raise ValueError
        with open(os.path.join(FOLDER, item, META), encoding='utf-8') as f:
            meta = json.loads(f.read())
        return meta['title']


class Kb(object, metaclass=MetaKb):
    """Vulnerability title dispatcher."""
