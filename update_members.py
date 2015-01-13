#!/usr/bin/env python

import os
import cgi

if 'REQUEST_METHOD' in os.environ:
    import cgitb
    cgitb.enable()
    print 'Content-Type: text/html'
    print
    from email_server import email_server_dummy as email_server
else:
    from email_server import email_server

import time
from urllib import urlopen
import anydbm
from fetch_arxiv import fetch_arxiv
from database import kipac_members_url, kipac_members_db, model_dir, new_paper_discovery

any_new = False
msg = u'<h2>Here\'s a list of new arXiv papers authored by KIPAC members:</h2>'
msg += u'<ul>'

with open(kipac_members_db, 'w') as fo:
    f = urlopen(kipac_members_url)
    line = f.next()
    fo.write(line)
    header = line.strip().split(',')
    for line in f:
        row = dict(zip(header, line.strip().split(',')))
        if int(row['active'] or 0) + int(row['tester'] or 0) == 0:
            continue
        arxiv = fetch_arxiv( \
                search_query='cat:astro-ph*+AND+au:'+row['arxivname'], \
                max_results=20, sortBy='submittedDate', sortOrder='descending')
        db_name = '%s/%s'%(model_dir, row['arxivname'])
        d = anydbm.open(db_name, 'w')
        for entry in arxiv.iterentries():
            k = entry['key']
            if k not in d: #or float(d[k]) < 1:
                d[k] = '1'
                any_new = True
                msg += u'<li>%s: [%s] <a href="%s">%s</a></li>'%(row['name'], 
                        entry['key'], entry['id'], cgi.escape(entry['title']))
        d.sync()
        if d:
            fo.write(line)
        d.close()

if any_new:
    msg += u'</ul>'
    msg += u'<p>This message is automatically generated and sent by KIPAC TeaBot.<br/>'
    msg += u'<a href="https://github.com/yymao/kipac-teabot/issues?state=open">Create an issue</a> if you have any suggestions/questions.</p>'
    email = email_server()
    email.send('KIPAC Tea Bot <teabot@kipac.stanford.edu>', \
               new_paper_discovery, \
               '[TeaBot] New arXiv papers by KIPAC members' \
                       + time.strftime('%m/%d',time.localtime()), \
               msg)
    email.close()

