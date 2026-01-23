#!/usr/bin/env python

import cgi
import cgitb
cgitb.enable()

form = cgi.FieldStorage()

print_id_only = form.getfirst('fmt', '').lower() == 'txt' or form.getfirst('idOnly')
print_body_only = bool(form.getfirst('bodyOnly'))
use_plain_style = bool(form.getfirst('plainStyle'))

print 'Content-Type:', 'text/plain' if print_id_only else 'text/html'
print 'Access-Control-Allow-Origin: *'
print

import os
import json
from datetime import date, timedelta
from secrets import discovery_archive

try:
    date_header_level = int(form.getfirst('headerLevel'))
except (ValueError, TypeError):
    date_header_level = 2

if date_header_level < 1 or date_header_level > 4:
    date_header_level = 2

try:
    days = int(form.getfirst('days'))
except (ValueError, TypeError):
    days = 30

try:
    items = int(form.getfirst('items'))
except (ValueError, TypeError):
    items = None
else:
    days = 30


if not (print_id_only or print_body_only):
    print '''<!DOCTYPE html>
<html>
<head>
  <title>New arXiv papers by KIPAC members</title>
  <meta http-equiv="content-type" content="text/html; charset=utf-8">
  <meta name="robots" content="noindex, nofollow">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  '''
    if use_plain_style:
        print '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/normalize/8.0.1/normalize.min.css" integrity="sha512-NhSC1YmyruXifcj/KFRWoC561YpHpc5Jtzgvbuzx5VozKpWvQ+4nXhPdFgmx8xqexRcpAglTj9sIBWINXa8x5w==" crossorigin="anonymous" referrerpolicy="no-referrer" />'
        print '''<style>
  .layout {
     margin-left: auto;
     margin-right: auto;
     max-width: 900px;
     padding: 0.5em 1em 6em 1em;
   }
  .footer{
     text-align: center;
     font-size: small;
     padding-top: 3em;
  }
  li {
    padding-bottom: 0.67em;
    line-height: 1.39em;
  }
  </style>'''
    else:
        print '<link rel="stylesheet" href="static/kipac.css" />'

    print '''</head>
<body>
  <div class="layout">
    <h1>New arXiv papers by KIPAC members</h1>
    <p style="font-size: small;"><a href="https://docs.google.com/forms/d/1gC1HpHCjcTQ2wGIsEzzAkUXm7aG9AJCyN6cjVxD8sR8/viewform">Report missing or misattributed papers</a></p>
'''

def _fn2date(fn):
    return int(fn[:-5])

files = sorted((f for f in os.listdir(discovery_archive) if f.endswith('.json')), key=_fn2date, reverse=True)
try:
    min_backto = files[5]
except IndexError:
    min_backto = files[-1]
min_backto = _fn2date(min_backto)
min_backto = min(int((date.today()-timedelta(days=days)).strftime('%Y%m%d')), min_backto)
files = [f for f in files if _fn2date(f) >= min_backto]

printed_items = 0
if items:
    print '<ul>'

for f in files:
    with open('{0}/{1}'.format(discovery_archive, f)) as fp:
        papers = json.load(fp)
    keys = papers.keys()
    keys.sort(reverse=True)

    if print_id_only:
        print '\n'.join(keys)
        continue

    if not items:
        print '<h{3}><a name="{0}{1}{2}">{0}/{1}/{2}</a></h{3}>'.format(f[4:6], f[6:8], f[:4], date_header_level)
        print '<ul>'

    for k in keys:
        v = papers[k]
        print u'<li><b>[<a name="{0}" href="http://arxiv.org/abs/{0}">{0}</a>]</b> <a href="http://arxiv.org/pdf/{0}.pdf">{1}</a><br> <i>Authors include {2}</i></li>'.format( \
                k, cgi.escape(v.pop(0)), \
                u', '.join(map(lambda s: s.partition(' <')[0], v)) \
                ).encode('utf-8')
        printed_items += 1
        if items is not None and printed_items >= items:
            break

    if not items:
        print '</ul>'

if items:
    print '</ul>'

if not (print_id_only or print_body_only):
    print """
  <p class="footer">By <a href="https://yymao.github.io">Yao-Yuan Mao</a> (2015-2022). Part of the <a href="https://github.com/yymao/kipac-teabot">KIPAC TeaBot</a> project.</p>
  </div>
</body>
</html>
"""

