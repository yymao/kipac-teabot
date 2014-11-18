#!/usr/bin/env python

from urllib import urlopen
from whichdb import whichdb
import anydbm
from fetch_arxiv import fetch_arxiv
from database import kipac_members_url, kipac_members_db, model_dir

with open(kipac_members_db, 'w') as fo:
    f = urlopen(kipac_members_url)
    line = f.next()
    fo.write(line)
    header = line.strip().split(',')
    for line in f:
        row = dict(zip(header, line.strip().split(',')))
        if int(row['active'] or 0) + int(row['tester'] or 0) == 0:
            continue
        print row['arxivname'],
        arxiv = fetch_arxiv( \
                search_query='cat:astro-ph*+AND+au:'+row['arxivname'], \
                max_results=50, sortBy='submittedDate', sortOrder='descending')
        db_name = '%s/%s'%(model_dir, row['arxivname'])
        if not whichdb(db_name):
            print "<NEW DB>",
        d = anydbm.open(db_name, 'c')
        for entry in arxiv.iterentries():
            k = entry['key']
            if k not in d or float(d[k]) < 1:
                d[k] = '1'
        d.sync()
        for k in d:
            break
        else:
            d.close()
            print "<NO ENTRY>"
            continue
        fo.write(line)
        d.close()
        print

