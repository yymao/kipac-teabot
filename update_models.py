#!/usr/bin/env python

import os
import anydbm
from database import kipac_members_db, model_dir, collection_weight_path
from fetch_arxiv import fetch_arxiv
from topic_model import topic_model, collection_weight

cw = collection_weight()

with open(kipac_members_db, 'r') as f:
    header = f.next().strip().split(',')
    for line in f:
        row = dict(zip(header, line.strip().split(',')))
        db_name = '%s/%s'%(model_dir, row['arxivname'])
        model_name = db_name + '.model'
        print row['arxivname'],
        if not os.path.isfile(model_name) or \
                os.path.getmtime(db_name) > os.path.getmtime(model_name):
            d = anydbm.open(db_name, 'r')
            ids = list(d.iterkeys())
            arxiv = fetch_arxiv(id_list=','.join(ids), max_results=len(ids))
            model = topic_model()
            for entry in arxiv.iterentries():
                model.add_document(entry['title'] + '.' + entry['summary'], \
                        weight=float(d[str(entry['key'])]))
            d.close()
            with open(model_name, 'wb') as f:
                f.write(model.dumps())
            print '<UPDATED>'
        else:
            with open(model_name, 'rb') as f:
                model = topic_model(f.read())
            print
        cw.add(model)

with open(collection_weight_path, 'wb') as fo:
    fo.write(cw.dumps())

