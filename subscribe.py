#!/usr/bin/env python
import os
import sys

if 'REQUEST_METHOD' not in os.environ:
    sys.exit(0)

import cgi
#import cgitb
#cgitb.enable()
import re
import cPickle as pickle

from secrets import member_list_path, update_prefs_path
from fetch_arxiv import arxiv_id_pattern
from Member import Member

_arxiv_re = re.compile(arxiv_id_pattern)

form = cgi.FieldStorage()

#confirmation
key = form.getfirst('k')
arxivname = form.getfirst('n')
if key and arxivname:
    print 'Content-Type: text/html'
    print
    print '''<!DOCTYPE html>
<html>
<head>
  <title>KIPAC TeaBot</title>
  <meta http-equiv="content-type" content="text/html; charset=utf-8">
</head>
<body>
<h1>KIPAC TeaBot</h1><h3>
'''
    prefs_path = os.path.join(update_prefs_path, arxivname)
    try:
        with open(prefs_path) as f:
            d = pickle.load(f)
    except IOError:
        print 'Hmmm... something went wrong...'
    else:
        if d.get('cancel') == key:
            os.remove(prefs_path)
            print 'Your request to {0} has been canceled.'.format(d.get('action'))

        elif d.get('key') == key:
            os.remove(prefs_path)
            m = Member(arxivname)
            if d.get('unsubscribe'):
                m.remove_prefs()
                print 'You have successfully unsubscribed from KIPAC TeaBot :('
            else:
                m.update_prefs(d['prefs'])
                if d.get('add_arxiv'):
                    with m.get_weights_db('w') as db:
                        for match in _arxiv_re.finditer(d['add_arxiv']):
                            k = match.group()
                            if k not in db or float(db[k]) < 0.8:
                                db[k] = '0.8'
                print 'Your request to {0} has been successfully processed! :)'.format(d.get('action'))

    print '</h3></body></html>'
    sys.exit(0)


# create request
# basic verification
import json
import time

print 'Content-Type: application/json'
print

def exit_and_output(msg='', success=False):
    print json.dumps(locals())
    sys.exit(0)

email = form.getfirst('email', '')
if '@' not in email:
    exit_and_output("Please enter a valid email address.")

with open(member_list_path, 'r') as f:
    header = f.next().strip().split(',')
    for line in f:
        person = dict(zip(header, line.strip().split(',')))
        if email == person['email']:
            break
    else:
        exit_and_output("The email address is not in the database. If you think this is a mistake, please contant Yao-Yuan Mao.")

prefs_path = os.path.join(update_prefs_path, person['arxivname'])
if os.path.isfile(prefs_path) and time.time() - os.path.getmtime(prefs_path) < 86400.0:
    exit_and_output("You have a previous request that have not yet been confirmed or canceled. If you think this is a mistake, please contant Yao-Yuan Mao.")


# start to process request
import uuid
from email_server import email_server

def check_select(i, options):
    try:
        i = int(i)
    except (ValueError, TypeError):
        return None
    if i not in options:
        return None
    return i


d = dict(key=uuid.uuid4().hex, cancel=uuid.uuid4().hex, ip=os.environ["REMOTE_ADDR"], time=time.time())
has_prefs = Member(person['arxivname']).has_prefs()

if form.getfirst('unsubscribe'):
    if not has_prefs:
        exit_and_output('You are not subscribed to TeaBot.')
    d['unsubscribe'] = True
    d['action'] = 'unsubscribe from TeaBot'
else:
    d['prefs'] = dict(nr = check_select(form.getfirst('nr'), (1,2,3,4,5)),
                      nl = check_select(form.getfirst('nl'), (0,10,25,50,75)),
                      pa = bool(form.getfirst('pa')),
                      export = bool(form.getfirst('export')))
    if any(v is None for v in d['prefs'].itervalues()):
        exit_and_output("Hmmm... this is weird.")
    d['add_arxiv'] = form.getfirst('arxiv', '')
    d['action'] = 'update your TeaBot preferences' if has_prefs else 'subscribe to TeaBot'

try:
    with open(prefs_path, 'w') as f:
        pickle.dump(d, f, pickle.HIGHEST_PROTOCOL)
except IOError:
    exit_and_output('Something went wrong. Please fill out your request again.')

url_base = 'https://web.stanford.edu/~yymao/cgi-bin/kipac-teabot/subscribe.py'

msg = """Hi {0[nickname]},<br><br>
Please confirm your request to {1[action]} by <a href="{2}?k={1[key]}&n={0[arxivname]}">clicking here</a>, or visit the following URL: <br><br>{2}?k={1[key]}&n={0[arxivname]}<br><br><br><br>
If you did not request to {1[action]}, you can ignore this email. If you would like to cancel this request, please <a href="{2}?k={1[cancel]}&n={0[arxivname]}">click here</a>, or visit
the following URL: <br><br>{2}?k={1[cancel]}&n={0[arxivname]}<br><br><br>
""".format(person, d, url_base)

msg += '<p>This message is automatically generated and sent by KIPAC TeaBot. <br>'
msg += '<a href="https://github.com/yymao/kipac-teabot/issues?state=open">Create an issue</a> if you have any suggestions/questions.</p>'

email = email_server()
email.send('KIPAC TeaBot <teabot@kipac.stanford.edu>', 
           '{0[name]} <{0[email]}>'.format(person),
           '[TeaBot] {0}'.format(d['action']), 
           msg)
email.close()
exit_and_output('A confirmation email has been sent to {0[email]}, please click the link in that email to complete the request.'.format(person), True)

