#!/usr/bin/env python

import os
if 'REQUEST_METHOD' in os.environ :
    import cgi, cgitb
    cgitb.enable()
    print 'Content-Type: text/html'
    print
    class email_server:
        def __init__(self):
            pass
        def close(self):
            pass
        def send(self, From, To, subject, message):
            print '<h2>', cgi.escape(To), '</h2>'
            print message.encode('ascii', 'xmlcharrefreplace')
            print '<br/><hr/>'
else:
    from email_server import email_server

import sys
import time
import md5
import json
import anydbm
import numpy as np

from database import keypass, kipac_members_db, model_dir, collection_weight_path
from fetch_arxiv import fetch_arxiv
from topic_model import topic_model, collection_weight, similarity_threshold

#get new arxiv entries
now = time.time()
sec_per_day = 24*60*60
to_time = time.gmtime(now-sec_per_day)
from_time = time.gmtime(now-sec_per_day*(2 if time.gmtime(now).tm_wday else 4))
from_time = time.strftime('%Y%m%d2000', from_time)
to_time = time.strftime('%Y%m%d2000', to_time)

arxiv = fetch_arxiv(max_results=200, \
        search_query='cat:astro-ph*+AND+submittedDate:[%s+TO+%s]'%(\
        from_time, to_time))
entries = arxiv.getentries()
del arxiv
if len(entries) == 0:
    sys.exit(0)

#load kipac members
people = []
member_db = anydbm.open(kipac_members_db, 'r')
for arxivname, js in member_db.iteritems():
    d = json.loads(js)
    with open('%s/%s.model'%(model_dir, arxivname), 'rb') as f:
        d['model'] = topic_model(f.read())
    people.append(d)
member_db.close()
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
for person in people:
    del person['model']

#helper function
def get_largest_indices(scores, limit, threshold=similarity_threshold):
    s = scores.argsort()
    for c, i in enumerate(reversed(s)):
        if scores[i] < threshold or c >= limit:
            break
        yield i

#start an email server
email = email_server()
from_me = 'KIPAC Tea Bot <teabot@kipac.stanford.edu>'
footer =  u'<p>This message is automatically generated and sent by KIPAC TeaBot.<br/>'
footer += u'<a href="https://github.com/yymao/kipac-teabot/issues?state=open">Create an issue</a> if you have any suggestions/questions.</p>'

#find papers that members are interested
n_papers = 10
n_people = 4
msg = u'<h2>KIPAC people might find the following new papers on arXiv today interesting:</h2>'
msg += u'<ul>'
median_scores = np.median(scores, axis=1)
any_paper = False
for i in get_largest_indices(median_scores, n_papers, 0):
    names= [people[j]['name'] for j in get_largest_indices(scores[i], n_people)]
    if len(names):
        any_paper = True
        entry = entries[i]
        msg += u'<li><p>'
        msg += u'<a href="%s">%s</a> by %s et al.<br/>'%(\
                entry['id'], entry['title'], entry['first_author'])
        msg += u'Try asking: %s'%(', '.join(names))
        msg += u'</p></li>'
msg += u'</ul>'
if any_paper:
    email.send(from_me, 'KIPAC tealeaks <tealeaks@kipac.stanford.edu>', 
            '[TeaBot] New arXiv papers ' + time.strftime('%m/%d', time.localtime()),
            msg + footer)

#find interesting papers for individual members
n_papers = 3
for j, person in enumerate(people):
    if person['tester'] != '1':
        continue
    msg = u'Hi %s,<br/><br/>'%(person['nickname'])
    msg += u'TeaBot thinks you\'ll find the following paper(s) on arXiv today interesting:<br/>'
    msg += u'<ul>'
    any_paper = False
    for i in get_largest_indices(scores[:, j], n_papers):
        entry = entries[i]
        if not any_paper:
            best_title = entry['title']
            any_paper = True
        arxiv_id = entry['key']
        key = md5.md5(arxiv_id + person['arxivname'] + keypass).hexdigest()
        url = 'http://stanford.edu/~yymao/cgi-bin/kipac-teabot/taste-tea.py?id=%s&name=%s&key=%s'%(\
                arxiv_id, person['arxivname'], key)
        msg += u'<li><b><a href="%s">%s</a></b> by %s et al.<br/><br/>%s [<a href="%s">Read more</a>]<br/><br/><br/></li>'%(\
                url, entry['title'], entry['first_author'], entry['summary'], url)
    if not any_paper:
        continue
    msg += u'</ul>'
    email.send(from_me, '%s <%s>'%(person['name'], person['email']),
            '[TeaBot] Best match on arXiv today: ' + best_title, 
            msg + footer)

#close the email server
email.close()

