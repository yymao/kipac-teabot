__all__ = ['topic_model', 'collection_weight', 'similarity_threshold']
import re
import math
from collections import defaultdict
import cPickle as pickle

_stopwords = "a,about,above,after,again,against,all,am,an,and,any,are,aren't,as,at,be,because,been,before,being,below,between,both,but,by,can't,cannot,could,couldn't,did,didn't,do,does,doesn't,doing,don't,down,during,each,few,for,from,further,had,hadn't,has,hasn't,have,haven't,having,he,he'd,he'll,he's,her,here,here's,hers,herself,him,himself,his,how,how's,i,i'd,i'll,i'm,i've,if,in,into,is,isn't,it,it's,its,itself,let's,me,more,most,mustn't,my,myself,no,nor,not,of,off,on,once,only,or,other,ought,our,ours,ourselves,out,over,own,same,shan't,she,she'd,she'll,she's,should,shouldn't,so,some,such,than,that,that's,the,their,theirs,them,themselves,then,there,there's,these,they,they'd,they'll,they're,they've,this,those,through,to,too,under,until,up,very,was,wasn't,we,we'd,we'll,we're,we've,were,weren't,what,what's,when,when's,where,where's,which,while,who,who's,whom,why,why's,with,won't,would,wouldn't,you,you'd,you'll,you're,you've,your,yours,yourself,yourselves"
_stopwords = _stopwords.split(',')
_stopwords.extend(['pc', 'kpc', 'mpc', 'gpc', 'et', 'al', 'au'])

_re_word = re.compile(r"[a-z][a-z-']*[a-z]",re.I)
_re_punct = re.compile(r"[,.;:?!]")


similarity_threshold = 0.02

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

    def get_similarity(self, other):
        f = lambda x,y:x+y*y
        norm_self = reduce(f, self._tf.itervalues(), 0)
        norm_other = reduce(f, other._tf.itervalues(), 0)
        s = 0.0
        for k, v in self._tf.iteritems():
            s += other._tf[k]*v
        return s/math.sqrt(norm_self*norm_other)

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

