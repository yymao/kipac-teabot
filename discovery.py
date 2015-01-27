#!/usr/bin/env python

import os
import cgi
import time
from fetch_arxiv import fetch_arxiv
from email_server import email_server
from secrets import member_list_path, discovery_team
from Member import Member

papers = {}

with open(member_list_path, 'r') as f:
    header = f.next().strip().split(',')
    for line in f:
        row = dict(zip(header, line.strip().split(',')))
        print row['arxivname']
        try:
            arxiv = fetch_arxiv( \
                    search_query='cat:astro-ph*+AND+au:'+row['arxivname'], \
                    max_results=10, sortBy='submittedDate', \
                    sortOrder='descending')
        except IOError:
            print row['arxivname'], 'was not updated due to connection error.'
            continue
        m = Member(row['arxivname'])
        with m.get_weights_db('w') as d:
            for entry in arxiv.iterentries():
                k = entry['key']
                if k not in d or float(d[k]) < 1:
                    d[k] = '1'
                    if k not in papers:
                        papers[k] = [entry['title']]
                    papers[k].append('%s <%s>'%(row['name'], row['email']))

if papers:
    msg = u'<h2>Here\'s a list of new arXiv papers authored by KIPAC members:</h2>'
    msg += u'<ul>'
    for k, v in papers.iteritems():
        msg += u'<li><p><b>[%s] <a href="http://arxiv.org/abs/%s">%s</a></b></p><p>'%(k, k, cgi.escape(v[0]))
        msg += u',<br/>'.join(map(cgi.escape, v[1:]))
        msg += u'<br/></p></li>'
    msg += u'</ul><br/>'
    msg += u'<p>If this report is accurate, you might send the members above a congratulatory email!</p><br/>'
    msg += u'<p>This message is automatically generated and sent by KIPAC TeaBot.<br/>'
    msg += u'<a href="https://github.com/yymao/kipac-teabot/issues?state=open">Create an issue</a> if you have any suggestions/questions.</p>'
    email = email_server()
    email.send('KIPAC TeaBot <teabot@kipac.stanford.edu>', \
               discovery_team, \
               '[TeaBot] %s new arXiv papers by KIPAC members'%(time.strftime('%m/%d',time.localtime())), \
               msg)
    email.close()

