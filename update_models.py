#!/usr/bin/env python

import os
import anydbm
from database import kipac_members_db, model_dir, collection_weight_path
from fetch_arxiv import fetch_arxiv
from topic_model import topic_model, collection_weight

cw = collection_weight()

member_db = anydbm.open(kipac_members_db, 'r')
for arxivname in member_db:
    fn = '%s/%s'%(model_dir, arxivname)
    print arxivname,
    if not os.path.isfile(fn+'.model') or \
            os.path.getmtime(fn) > os.path.getmtime(fn+'.model'):
        d = anydbm.open(fn, 'r')
        ids = list(d.iterkeys())
        arxiv = fetch_arxiv(id_list=','.join(ids), max_results=len(ids))
        model = topic_model()
        for entry in arxiv.iterentries():
            model.add_document(entry['title'] + '.' + entry['summary'], \
                    weight=float(d[str(entry['key'])]))
        d.close()
        with open(fn+'.model', 'wb') as f:
            f.write(model.dumps())
        print '<updated>'
    else:
        with open(fn+'.model', 'rb') as f:
            model = topic_model(f.read())
        print
    cw.add(model)
member_db.close()

with open(collection_weight_path, 'wb') as fo:
    fo.write(cw.dumps())

