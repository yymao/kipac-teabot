#!/usr/bin/env python

from __future__ import print_function
import io
import os
import re
import json
import cgi
from fetch_arxiv import fetch_arxiv_rss
from email_server import email_server
from secrets import member_list_path, discovery_team, discovery_archive
from Member import Member

if 'REQUEST_METHOD' in os.environ:
    print('Content-Type: text/html')
    print()
    import cgitb
    cgitb.enable()

def get_kipac_members():
    people = []
    with io.open(member_list_path, 'r', encoding='utf-8') as f:
        header = f.next().strip().split(',')
        for line in f:
            row = dict(zip(header, line.strip().split(',')))
            if int(row['is_kipac'] or 0):
                people.append(row)
    return people

def convert_arxiv_name_to_re(arxiv_name):
    names = arxiv_name.split('_')
    j = r"[\w'.]*[\s\-]+"
    return re.compile(j.join((j.join(names[1:]), names[0])), re.I + re.U)


arxiv = fetch_arxiv_rss()
entries = arxiv.entries
if not entries:
    raise RuntimeError('Found no arXiv entry. Abort!')

people = get_kipac_members()
if not people:
    raise RuntimeError('Found no member. Abort!')

has_new_paper = False
archive_fname = "{}/{}.json".format(discovery_archive, arxiv.date)
if os.path.isfile(archive_fname):
    with open(archive_fname, 'r') as f:
        papers = json.load(f)
else:
    papers = dict()

for person in people:
    name_re = convert_arxiv_name_to_re(person["arxivname"])
    entries_matched = [entry for entry in entries if name_re.search(entry.authors_text)]
    if not entries_matched:
        continue
    m = Member(person['arxivname'])
    with m.get_weights_db('w') as d:
        for entry in entries_matched:
            k = entry['key']
            if k not in d or float(d[k]) < 1:
                d[k] = '1'
            if k not in papers:
                has_new_paper = True
                papers[k] = [entry['title']]
            person_str = '%s <%s>'%(person['name'].decode('utf-8'), person['email'])
            if person_str not in papers[k]:
                papers[k].append(person_str)

if papers:
    # save to archive
    with open(archive_fname, 'w') as f:
        json.dump(papers, f)

if has_new_paper:
    # prepare email
    email = email_server()
    for k, v in papers.iteritems():
        msg = u'<p>This new paper that appears on arXiv today is (allegedly) authored by KIPAC member(s):</p>'
        msg += u'<ul><li>[%s] <a href="http://arxiv.org/abs/%s">%s</a></b> <br><br>'%(k, k, cgi.escape(v[0]))
        msg += u', <br>'.join(map(cgi.escape, v[1:]))
        msg += u'</li></ul>'
        msg += u'<p>If this report is accurate, you might send the member(s) above a congratulatory email!</p>'
        msg += u'<br><p>This message is automatically generated and sent by KIPAC TeaBot. <br>'
        msg += u'<a href="https://github.com/yymao/kipac-teabot/issues?state=open">Create an issue</a> if you have any suggestions/questions.</p>'
        email.send('KIPAC TeaBot <teabot@kipac.stanford.edu>', discovery_team, \
                '[TeaBot][Discovery] %s'%cgi.escape(v[0]), msg)
    email.close()
