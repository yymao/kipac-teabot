#!/usr/bin/env python

import os
if 'REQUEST_METHOD' in os.environ :
    import cgi, cgitb
    cgitb.enable()
    print 'Content-Type: text/html'
    print
    TESTING = True
else:
    TESTING = False #or True

import sys
import time
import re
import md5
import sqlite3
import numpy as np

from database import keypass, people_db_path, collection_weight_path, response_db_path
from email_server import email_server
from fetch_arxiv import fetch_arxiv
from topic_model import topic_model, collection_weight, similarity_threshold

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
arxiv = None
if len(entries) == 0:
    sys.exit(0)

people = []
db = sqlite3.connect(people_db_path)
cur = db.cursor()
cur.execute('select name, model, email, tester from people')
row = cur.fetchone()
while row is not None:
    people.append({'name':row[0], 'model':topic_model(str(row[1])), 'email':row[2], 'tester':row[3]})
    row = cur.fetchone()
db.close()
if len(people) == 0:
    sys.exit(0)

with open(collection_weight_path, 'r') as f:
    cw = collection_weight(f.read())

scores = []
for entry in entries:
    model = topic_model()
    model.add_document(entry['title'] + '.' + entry['summary'])
    model.apply_weight(cw)
    for person in people:
        scores.append(model.get_similarity(person['model']))
scores = np.array(scores).reshape(len(entries), len(people))
model = None

email = email_server()
from_me = 'Yao-Yuan Mao <yymao@stanford.edu>'
footer =  u'<br/><p>This message is automatically generated and sent by KIPAC TeaBot.<br/>'
footer += u'<a href="https://github.com/yymao/kipac-teabot/issues?state=open">Create an issue</a> if you have any suggestions/questions.</p>'

def get_largest_indices(scores, limit, threshold=similarity_threshold):
    s = scores.argsort()
    for c, i in enumerate(reversed(s)):
        if scores[i] < threshold or c >= limit:
            break
        yield i

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
    if TESTING:
        print msg.encode('ascii', 'xmlcharrefreplace') + footer
        print '<br/><hr/>'
    else:
        email.send(from_me, 'KIPAC tealeaks <tealeaks@kipac.stanford.edu>', \
            '[TeaBot] New arXiv papers ' \
            + time.strftime('%m/%d', time.localtime()),\
            msg + footer)

db = sqlite3.connect(response_db_path)
n_papers = 3
for j, person in enumerate(people):
    if person['tester'] is None:
        continue
    msg = u'Hi %s,<br/><br/>'%(person['name'].split()[0])
    msg += u'You may find the following new paper(s) on arXiv today interesting:<br/>'
    msg += u'<ul>'
    any_paper = False
    for i in get_largest_indices(scores[:, j], n_papers):
        entry = entries[i]
        if not any_paper:
            best_title = entry['title']
            any_paper = True
        arxiv_id = re.search(r'\d{4}\.\d{4}', entry['id']).group()
        key = md5.md5(arxiv_id + person['name'] + keypass).hexdigest()
        db.execute('insert or replace into response (key, arxiv_id, person) values (?,?,?)',\
                (key, arxiv_id, person['name']))
        url = 'http://www.stanford.edu/~yymao/cgi-bin/taste-tea/arxiv.php?id=%s&key=%s'%(\
                arxiv_id, key)
        dislike_key = md5.md5(key + 'dislike' + keypass).hexdigest()
        url_dislike = 'http://www.stanford.edu/~yymao/cgi-bin/taste-tea/get-res.php?id=%s&key=%s&res=dislike&reskey=%s'%(\
                arxiv_id, key, dislike_key)
        msg += u'<li><p><a href="%s">%s</a> by %s et al.<br/><br/>%s<br/><br/><a href="%s">Read more</a> | <a href="%s">Not interesting</a><br/><br/></p></li>'%(\
                url, entry['title'], entry['first_author'], entry['summary'], url, url_dislike)
    if not any_paper:
        continue
    msg += u'</ul>'
    db.commit()
    if TESTING:
        print '<h2>', person['name'], '</h2>'
        print msg.encode('ascii', 'xmlcharrefreplace') + footer
        print '<br/><hr/>'
    else:
        email.send(from_me, '%s <%s>'%(person['name'], person['email']), \
                '[TeaBot] Best match on arXiv today: '+best_title, msg + footer)

db.close()
email.close()

