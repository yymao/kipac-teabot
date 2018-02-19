#!/usr/bin/env python

import os
from secrets import member_list_path, collection_weight_path
from Member import Member
from topic_model import collection_weight

cw = collection_weight()
force_update = False #or True

with open(member_list_path, 'r') as f:
    header = f.next().strip().split(',')
    for line in f:
        row = dict(zip(header, line.strip().split(',')))
        m = Member(row['arxivname'])
        if row['email'] and (m.has_prefs() or int(row['is_kipac'] or 0)):
            print row['arxivname']
            model = m.update_model(force_update)
            if model is not None:
                cw.add(model)

with open(collection_weight_path, 'wb') as fo:
    fo.write(cw.dumps())

