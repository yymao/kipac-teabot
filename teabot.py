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
    #from email_server import email_server_dummy as email_server

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
        search_query='cat:astro-ph*+AND+submittedDate:[{0[0]}+TO+{0[1]}]'.format(\
        get_time_range(time.time())))
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
        m = Member(row['arxivname'])
        row['model'] = m.get_model()
        row['prefs'] = m.get_prefs()
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
for i, person in enumerate(people):
    if int(person['active'] or 0):
        active_idx.append(i)
    del person['model']
    del person['active']


#helper functions
def get_largest_indices(scores, limit, threshold=similarity_threshold, store_argsort=None):
    s = scores.argsort()
    if store_argsort is not None:
        store_argsort[:] = s[::-1]
    for c, i in enumerate(reversed(s)):
        if scores[i] < threshold or c >= limit:
            break
        yield i

def format_authors(authors, max_authors=6):
    a = u', '.join(authors[:max_authors])
    if len(authors) > max_authors:
        a += u' et al.'
    return cgi.escape(a)

def format_entry(entry, arxivname, print_abstract=True, score=None):
    arxiv_id = entry['key']
    key = md5.md5(arxiv_id + arxivname + keypass).hexdigest()
    url = 'https://web.stanford.edu/~yymao/cgi-bin/kipac-teabot/taste-tea.py?id={0}&name={1}&key={2}'.format(arxiv_id, arxivname, key)
    abstract = u'{0} [<a href="{1}">Read more</a>] <br><br><br>'.format(cgi.escape(entry['summary']), url) if print_abstract else u''
    score = u' (score = {:.3g})'.format(score) if score is not None else u''
    return u'<li>[<a href="{0}&abs=on">{1}</a>] <b><a href="{0}">{2}</a></b>{5} <br>by {3} <br><br>{4}</li>'.format(\
                url, arxiv_id, cgi.escape(entry['title']), format_authors(entry['authors']), abstract, score)

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
        msg += u'<li>[{0[key]}] <a href="{0[id]}">{1}</a> <br>by {2} <br>Try asking: {3} <br><br></li>'.format(\
                entry, cgi.escape(entry['title']), format_authors(entry['authors']), ', '.join(names))
msg += u'</ul>'
msg += u'<p>Also check <a href="http://stanford.edu/~yymao/cgi-bin/kipac-teabot/arxiv-discovery">this page</a> for new arXiv papers authored by KIPAC members.</p>'
if any_paper:
    email.send(from_me, 'KIPAC tealeaks <tealeaks@kipac.stanford.edu>', \
            '[TeaBot] {0} new papers on arXiv'.format(time.strftime('%m/%d',time.localtime())), \
            msg + footer)


#find interesting papers for individual members
footer += u'<p>To unsubscribe or to update your preferences, <a href="https://web.stanford.edu/~yymao/cgi-bin/kipac-teabot/subscribe.html">click here</a>.</p>'
for j, person in enumerate(people):
    if not person['prefs']:
        continue
    greetings = u'Hi {0}, <br><br>'.format(person['nickname'])
    msg = u'TeaBot thinks you\'ll find the following paper(s) on arXiv today interesting: <br>'
    msg += u'<ul>'
    any_paper = 0
    ss = np.empty(len(scores), int) if person['prefs']['nl'] > person['prefs']['nr'] else None
    for i in get_largest_indices(scores[:, j], person['prefs']['nr'], store_argsort=ss):
        if not any_paper:
            best_title = entries[i]['title']
        msg += format_entry(entries[i], person['arxivname'], person['prefs']['pa'])
        any_paper += 1
    msg += u'</ul>'
    if person['prefs']['nl'] > person['prefs']['nr']:
        if not any_paper:
            any_paper += 1
            best_title = '{0} new papers on arXiv'.format(time.strftime('%m/%d',time.localtime()))
            msg = u''
        msg += u'The following papers are sorted by relevance:'
        msg += u'<ul>'
        for i in ss[any_paper:person['prefs']['nl']]:
            msg += format_entry(entries[i], person['arxivname'], False)
        msg += u'</ul>'
    if any_paper:
        email.send(from_me, '{0[name]} <{0[email]}>'.format(person), \
                '[TeaBot] ' + best_title, u''.join((greetings, msg, footer)))


#close the email server
email.close()

