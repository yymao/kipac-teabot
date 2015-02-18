#!/usr/bin/env python

import os
import sys
import time
import json
import cgi
from fetch_arxiv import fetch_arxiv, get_time_range
from email_server import email_server
from secrets import member_list_path, discovery_team, discovery_archive
from Member import Member

papers = {}

with open(member_list_path, 'r') as f:
    header = f.next().strip().split(',')
    for line in f:
        row = dict(zip(header, line.strip().split(',')))
        print row['arxivname']
        t = get_time_range(time.time(), 2) + (row['arxivname'],)
        q = 'cat:astro-ph*+AND+submittedDate:[%s+TO+%s]+AND+au:%s'%t
        try:
            arxiv = fetch_arxiv(search_query=q, max_results=10)
        except IOError:
            sys.stderr.write(row['arxivname'] \
                    + 'was not updated due to connection error.\n')
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
    #save to archive
    fname = '%s/%s.json'%(discovery_archive, time.strftime('%Y%m%d'))
    with open(fname, 'w') as f:
        json.dump(papers, f)

    #prepare email
    email = email_server()
    for k, v in papers.iteritems():
        msg = u'<p>This new paper that appears on arXiv today is (allegedly) authored by KIPAC member(s):</p>'
        msg += u'<p style="margin-left: 4em;"><b>[%s] <a href="http://arxiv.org/abs/%s">%s</a></b><br/><br/>'%(k, k, cgi.escape(v[0]))
        msg += u',<br/>'.join(map(cgi.escape, v[1:]))
        msg += u'</p><br/>'
        msg += u'<p>If this report is accurate, you might send the member(s) above a congratulatory email!</p><br/>'
        msg += u'<p>This message is automatically generated and sent by KIPAC TeaBot.<br/>'
        msg += u'<a href="https://github.com/yymao/kipac-teabot/issues?state=open">Create an issue</a> if you have any suggestions/questions.</p>'
        email.send('KIPAC TeaBot <teabot@kipac.stanford.edu>', discovery_team, \
                '[TeaBot][Discovery] %s'%cgi.escape(v[0]),  msg)
    email.close()

