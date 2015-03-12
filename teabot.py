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

import sys
import time
import md5
import numpy as np

from fetch_arxiv import fetch_arxiv, get_time_range
from topic_model import topic_model, collection_weight, similarity_threshold
from secrets import keypass, member_list_path, collection_weight_path
from Member import Member

#get new arxiv entries
arxiv = fetch_arxiv(max_results=200, \
        search_query='cat:astro-ph*+AND+submittedDate:[%s+TO+%s]'%\
        get_time_range(time.time()))
entries = arxiv.getentries()
if len(entries) == 0:
    sys.exit(0)
del arxiv

#load kipac members
people = []
with open(member_list_path, 'r') as f:
    header = f.next().strip().split(',')
    for line in f:
        row = dict(zip(header, line.strip().split(',')))
        row['model'] = Member(row['arxivname']).get_model()
        if row['model'] is not None:
            people.append(row)
if len(people) == 0:
    sys.exit(0)

#apply collection weight to arxiv entries
with open(collection_weight_path, 'rb') as f:
    cw = collection_weight(f.read())

scores = []
for entry in entries:
    model = topic_model()
    model.add_document(entry['title'] + '.' + entry['summary'])
    model.apply_weight(cw)
    for person in people:
        scores.append(model.get_similarity(person['model']))
scores = np.array(scores).reshape(len(entries), len(people))

#clean up
del model
del cw
active_idx = []
tester_idx = []
for i, person in enumerate(people):
    if int(person['active'] or 0):
        active_idx.append(i)
    if int(person['tester'] or 0):
        tester_idx.append(i)
    del person['model']
    del person['active']
    del person['tester']

#helper function
def get_largest_indices(scores, limit, threshold=similarity_threshold):
    s = scores.argsort()
    for c, i in enumerate(reversed(s)):
        if scores[i] < threshold or c >= limit:
            break
        yield i

#start an email server
email = email_server()
from_me = 'KIPAC TeaBot <teabot@kipac.stanford.edu>'
footer =  u'<br><p>This message is automatically generated and sent by KIPAC TeaBot. <br>'
footer += u'<a href="https://github.com/yymao/kipac-teabot/issues?state=open">Create an issue</a> if you have any suggestions/questions.</p>'

#find papers that members are interested
n_papers = 8
n_people = 4
msg = u'<h2>KIPAC people might find the following new papers on arXiv today interesting:</h2>'
msg += u'<ul>'
median_scores = np.median(scores[:,active_idx], axis=1)
any_paper = False
for i in get_largest_indices(median_scores, n_papers, 0):
    names = [people[active_idx[j]]['name'] \
            for j in get_largest_indices(scores[i,active_idx], n_people)]
    if names:
        any_paper = True
        entry = entries[i]
        msg += u'<li>[%s] <a href="%s">%s</a> by %s et al. <br>'%(\
                entry['key'], entry['id'], cgi.escape(entry['title']), \
                cgi.escape(entry['first_author']))
        msg += u'Try asking: %s</li>'%(', '.join(names))
msg += u'</ul>'
msg += u'<p>Also check <a href="http://stanford.edu/~yymao/cgi-bin/kipac-teabot/arxiv-discovery">this page</a> for new arXiv papers authored by KIPAC members.</p>'
if any_paper:
    email.send(from_me, 'KIPAC tealeaks <tealeaks@kipac.stanford.edu>', \
            '[TeaBot] %s new papers on arXiv'%(time.strftime('%m/%d',time.localtime())), \
            msg + footer)

#find interesting papers for individual members
n_papers = 3
for j in tester_idx:
    person = people[j]
    msg = u'Hi %s, <br><br>'%(person['nickname'])
    msg += u'TeaBot thinks you\'ll find the following paper(s) on arXiv today interesting: <br>'
    msg += u'<ul>'
    any_paper = False
    for i in get_largest_indices(scores[:, j], n_papers):
        entry = entries[i]
        if not any_paper:
            best_title = entry['title']
            any_paper = True
        arxiv_id = entry['key']
        key = md5.md5(arxiv_id + person['arxivname'] + keypass).hexdigest()
        url = 'https://web.stanford.edu/~yymao/cgi-bin/kipac-teabot/taste-tea.py?id=%s&name=%s&key=%s'%(arxiv_id, person['arxivname'], key)
        msg += u'<li>[<a href="%s&abs=on">%s</a>] <b><a href="%s">%s</a></b> <br>by %s et al. <br><br>%s [<a href="%s">Read more</a>]<br><br><br></li>'%(\
                url, arxiv_id, url, cgi.escape(entry['title']), cgi.escape(entry['first_author']), cgi.escape(entry['summary']), url)
    if not any_paper:
        continue
    msg += u'</ul>'
    email.send(from_me, '%s <%s>'%(person['name'], person['email']),
            '[TeaBot] ' + best_title, msg + footer)

#close the email server
email.close()

