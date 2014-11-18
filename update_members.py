#!/usr/bin/env python

from urllib import urlopen
import json
import anydbm
from whichdb import whichdb
from database import kipac_members_url, kipac_members_db, model_dir
from fetch_arxiv import fetch_arxiv

member_db = anydbm.open(kipac_members_db, 'c')
f = urlopen(kipac_members_url)
header = f.next().split(',')
for line in f:
    row = dict(zip(header, line.split(',')))
    if not int(row['active']):
        continue
    arxivname = row['arxivname']
    arxiv = fetch_arxiv(search_query='cat:astro-ph*+AND+au:'+arxivname,\
            max_results=50, sortBy='submittedDate', sortOrder='descending')
    print row['name'],
    if not whichdb('%s/%s'%(model_dir, arxivname)):
        print "<new database>",
    d = anydbm.open('%s/%s'%(model_dir, arxivname), 'c')
    for entry in arxiv.iterentries():
        d[entry['key']] = '1'
    d.sync()
    for k in d:
        break
    else:
        d.close()
        print "<no entry>"
        continue
    member_db[arxivname] = json.dumps(row)
    d.close()
    print

member_db.close()

