#!/usr/bin/env python

import os
import sys
import time
from fetch_arxiv import is_holiday
from teabot_utils import *
from secrets import tealeaks_team, sent_from

if 'REQUEST_METHOD' in os.environ:
    print 'Content-Type: text/html'
    print
    import cgi
    import cgitb
    cgitb.enable()
    form = cgi.FieldStorage()
    if form.getfirst("send") == time.strftime("%Y%m%d"):
        from email_server import email_server
    else:
        from email_server import email_server_dummy as email_server
elif is_holiday():
    sys.exit(0)
else:
    from email_server import email_server

entries = get_arxiv_entries()
if not entries:
    raise RuntimeError('Found no arXiv entry. Abort!')

people = get_kipac_members()
if not people:
    raise RuntimeError('Found no member. Abort!')

scores, keywords= calc_scores(entries, people, 7)
active_idx = get_active_indices_and_clean_up(people)

footer =  u'<br><p>This message is automatically generated and sent by KIPAC TeaBot. <br>'
footer += u'<a href="https://github.com/yymao/kipac-teabot/issues?state=open">Create an issue</a> if you have any suggestions/questions.</p>'

email = email_server()

#find papers that members are interested
title = '{0} new papers on arXiv'.format(format_today())
msg = prepare_email_to_organizers(entries, people, scores, active_idx)
if msg:
    email.send(sent_from, tealeaks_team, '[TeaBot] ' + title, msg + footer)

#find interesting papers for individual members
footer += u'<p>To unsubscribe or to update your preferences, <a href="https://web.stanford.edu/group/kipac_teabot/cgi-bin/teabot/subscribe.html">click here</a>.</p>'
for to, title, msg in iter_prepare_email_to_individuals(entries, people, scores, keywords):
    email.send(sent_from, to, '[TeaBot] ' + title, msg + footer)

email.close()

if 'REQUEST_METHOD' in os.environ:
    print '<div>Done!</div>'

