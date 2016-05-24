__all__ = ['topic_model', 'collection_weight', 'similarity_threshold']
import re
import math
from collections import defaultdict
from operator import itemgetter
import cPickle as pickle
from mysql_stopwords import mysql_stopwords

_stopwords = mysql_stopwords
map(_stopwords.add, ('pc', 'kpc', 'mpc', 'gpc', 'et', 'al', 'au', 'odot', 'rm', 'pm'))

_re_word = re.compile(r"[a-z][a-z-']*[a-z]",re.I)
_re_punct = re.compile(r"[,.;:?!]")

similarity_threshold = 0.016

class topic_model:
    def __init__(self, string=None):
        if string is None:
            self._tf = defaultdict(float) #term frequency
        else:
            self.loads(string)

    def add_document(self, text, weight=1.0):
        ugf = defaultdict(int) #unigram frequency
        bgf = defaultdict(int) #bigram frequency
        tgf = defaultdict(int) #trigram frequency
        for sentence in _re_punct.split(text):
            history = []
            for m in _re_word.finditer(sentence):
                w = m.group().lower()
                if w not in _stopwords:
                    ugf[w] += 1
                    history.append(w)
                    if len(history) >= 2:
                        bgf[' '.join(history[-2:])] += 1
                        if len(history) >= 3:
                            tgf[' '.join(history[-3:])] += 1
                            del history[0]
        for ngf in (ugf, bgf, tgf):
            try:
                normalization = max(ngf.itervalues())
            except ValueError:
                pass
            else:
                normalization = float(normalization)/weight
                for k, v in ngf.iteritems():
                    self._tf[k] += v/normalization

    def get_similarity(self, other, return_keywords=0):
        f = lambda x,y:x+y*y
        norm_self = reduce(f, self._tf.itervalues(), 0)
        norm_other = reduce(f, other._tf.itervalues(), 0)
        norm_total = math.sqrt(norm_self*norm_other)
        return_keywords = int(return_keywords)
        if return_keywords:
            keywords = []
            total_score = 0.0
            for k, v in self._tf.iteritems():
                s = other._tf[k]*v
                total_score += s
                if len(keywords) >= return_keywords:
                    m = min(keywords, key=itemgetter(1))
                    if s < m[1]:
                        continue
                    keywords.remove(m)
                keywords.append((k, s))
            return total_score/norm_total, map(itemgetter(0), sorted(keywords, key=itemgetter(1), reverse=True))
        else:
            return sum(other._tf[k]*v for k, v in self._tf.iteritems())/norm_total

    def dumps(self):
        return pickle.dumps(self._tf, 2)

    def loads(self, string):
        self._tf = pickle.loads(string)

    def apply_weight(self, collection_weight):
        total = float(collection_weight._total_count)
        for k in self._tf:
            self._tf[k] *= math.log(total/(collection_weight._w[k]+1))

class collection_weight:
    def __init__(self, string=None):
        if string is None:
            self._total_count = 0
            self._w = defaultdict(int)
        else:
            self.loads(string)

    def add(self, topic_model):
        self._total_count += 1
        for k in topic_model._tf:
            self._w[k] += 1

    def dumps(self):
        return pickle.dumps({'total_count':self._total_count, 'w':self._w}, 2)

    def loads(self, string):
        d = pickle.loads(string)
        self._total_count = d['total_count']
        self._w = d['w']

