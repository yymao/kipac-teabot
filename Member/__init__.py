__all__ = ['Member']

import os
import anydbm
import cPickle as pickle
from itertools import izip

from secrets import db_path
from fetch_arxiv import fetch_arxiv
from topic_model import topic_model

class _MyDB:
    def __init__(self, path, flag='r'):
        self._path = path
        self._flag = flag

    def __enter__(self):
        self._d = anydbm.open(self._path, self._flag)
        return self._d

    def __exit__(self, type, value, tb):
        self._d.close()

class Member:
    def __init__(self, arxiv_name):
        self.arxiv_name = arxiv_name
        self._weights_path = self._get_path('weights')
        self._model_path = self._get_path('model')
        self._prefs_path = self._get_path('prefs')
    
    def _get_path(self, t):
        return os.path.join(db_path, t, self.arxiv_name)

    def rename(self, new_arxiv_name):
        self.arxiv_name = new_arxiv_name
        if os.path.isfile(self._get_path('weights')):
            raise ValueError('Weights database for ' + self.arxiv_name + ' already exists')
        if os.path.isfile(self._weights_path):
            os.rename(self._weights_path, self._get_path('weights'))
        self._weights_path = self._get_path('weights')
        if os.path.isfile(self._model_path):
            os.rename(self._model_path, self._get_path('model'))
        self._model_path = self._get_path('model')
        if os.path.isfile(self._prefs_path):
            os.rename(self._prefs_path, self._get_path('prefs'))
        self._prefs_path = self._get_path('prefs')

        arxiv = fetch_arxiv( \
                search_query='cat:astro-ph*+AND+au:'+self.arxiv_name, \
                max_results=50, sortBy='submittedDate', sortOrder='descending')
        with self.get_weights_db('w') as d:
            for entry in arxiv.iterentries():
                k = entry['key']
                if k not in d or float(d[k]) < 1:
                    d[k] = '1'

    def has_weights_db(self):
        return os.path.isfile(self._weights_path)

    def has_weights(self):
        with self.get_weights_db() as d:
            for k in d:
                return True
        return False

    def get_weights_db(self, flag='r'):
        return _MyDB(self._weights_path, flag)

    def create_weights_db(self):
        if os.path.isfile(self._weights_path):
            raise ValueError('Weights database for ' + self.arxiv_name + ' already exists')
        arxiv = fetch_arxiv( \
                search_query='cat:astro-ph*+AND+au:'+self.arxiv_name, \
                max_results=50, sortBy='submittedDate', sortOrder='descending')
        with self.get_weights_db('n') as d:
            for entry in arxiv.iterentries():
                d[entry['key']] = '1'

    def get_model(self):
        if os.path.isfile(self._model_path):
            with open(self._model_path, 'rb') as f:
                model = topic_model(f.read())
        else:
            model = None
        return model

    def update_model(self, force_update=False):
        if not os.path.isfile(self._model_path) \
                or os.path.getmtime(self._weights_path) > os.path.getmtime(self._model_path) \
                or force_update:
            with self.get_weights_db() as d:
                ids = list(d.iterkeys())
                if not len(ids):
                    return None
                model = topic_model()
                for i in range(0, len(ids), 150):
                    arxiv = fetch_arxiv(id_list=','.join(ids[i:i+150]), max_results=150)
                    for key, entry in izip(ids, arxiv.iterentries()):
                        model.add_document(entry['title']+'.'+entry['summary'], \
                                weight=float(d[key]))
            with open(self._model_path, 'wb') as f:
                f.write(model.dumps())
        else:
            model = self.get_model()
        return model

    def has_prefs(self):
        return os.path.isfile(self._prefs_path)

    def get_prefs(self):
        if not self.has_prefs():
            return None
        with open(self._prefs_path) as f:
            d = pickle.load(f)
        return d

    def update_prefs(self, new_prefs):
        with open(self._prefs_path, 'w') as f:
            pickle.dump(new_prefs, f, pickle.HIGHEST_PROTOCOL)
        return new_prefs

    def remove_prefs(self):
        os.remove(self._prefs_path)
