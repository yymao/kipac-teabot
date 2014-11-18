#!/usr/bin/env python

import anydbm
from database import kipac_members_reduced_csv, model_dir, collection_weight_path
from fetch_arxiv import fetch_arxiv
from topic_model import topic_model, collection_weight

cw = collection_weight()

with open(kipac_members_reduced_csv, 'r') as f:
    for line in f:
        arxivname = line.split(',')[2]
        d = anydbm.open('%s/%s'%(model_dir, arxivname), 'r')
        ids = list(d.iterkeys())
        arxiv = fetch_arxiv(id_list=','.join(ids), max_results=len(ids))
        model = topic_model()
        for entry in arxiv.iterentries():
            model.add_document(entry['title'] + '.' + entry['summary'], \
                    weight=float(d[str(entry['key'])]))
        d.close()
        with open('%s/%s.model'%(model_dir, arxivname), 'wb') as fo:
            fo.write(model.dumps())
        cw.add(model)
        print arxivname

with open(collection_weight_path, 'wb') as fo:
    fo.write(cw.dumps())

