#!/usr/bin/env python

import os
import cgi
import time
from fetch_arxiv import fetch_arxiv
from email_server import email_server
from secrets import member_list_path, discovery_team
from Member import Member

any_new = False
msg = u'<h2>Here\'s a list of new arXiv papers authored by KIPAC members:</h2>'
msg += u'<ul>'

with open(member_list_path, 'r') as f:
    header = f.next().strip().split(',')
    for line in f:
        row = dict(zip(header, line.strip().split(',')))
        arxiv = fetch_arxiv( \
                search_query='cat:astro-ph*+AND+au:'+row['arxivname'], \
                max_results=10, sortBy='submittedDate', sortOrder='descending')
        m = Member(row['arxivname'])
        with m.get_weights_db('w') as d:
            for entry in arxiv.iterentries():
                k = entry['key']
                if k not in d: #or float(d[k]) < 1:
                    d[k] = '1'
                    any_new = True
                    msg += u'<li>%s: [%s] <a href="%s">%s</a></li>'%(\
                            row['name'], entry['key'], entry['id'], \
                            cgi.escape(entry['title']))

if any_new:
    msg += u'</ul><br/>'
    msg += u'<p>This message is automatically generated and sent by KIPAC TeaBot.<br/>'
    msg += u'<a href="https://github.com/yymao/kipac-teabot/issues?state=open">Create an issue</a> if you have any suggestions/questions.</p>'
    email = email_server()
    email.send('KIPAC TeaBot <teabot@kipac.stanford.edu>', \
               new_paper_discovery, \
               '[TeaBot] %s new arXiv papers by KIPAC members'%(time.strftime('%m/%d',time.localtime())), \
               msg)
    email.close()

