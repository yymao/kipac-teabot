#!/usr/bin/env python

import cgi
#import cgitb
#cgitb.enable()
form = cgi.FieldStorage()

plain_text = (form.getvalue('fmt') == 'txt')
try:
    days = int(form.getvalue('days'))
except (ValueError, TypeError):
    days = 30

print 'Content-Type:', 'text/plain' if plain_text else 'text/html' 
print

import os
import json
from datetime import date, timedelta
from secrets import discovery_archive

if not plain_text:
    print '''<!DOCTYPE html>
<html>
<head>
  <title>New arXiv papers by KIPAC members</title>
  <meta http-equiv="content-type" content="text/html; charset=utf-8">
  <meta name="robots" content="noindex, nofollow">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="stylesheet" href="//cdn.jsdelivr.net/pure/0.5.0/pure-min.css">
  <style>
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
  }
  </style>
</head>
<body>
  <div class="layout">
    <h1>New arXiv papers by KIPAC members</h1>
'''

backto = int((date.today()-timedelta(days=days)).strftime('%Y%m%d'))
files = os.listdir(discovery_archive)
files = filter(lambda s: s.endswith('.json') and int(s[:-5]) >= backto, files)
files.sort(reverse=True)

for f in files:
    with open('{0}/{1}'.format(discovery_archive, f)) as fp:
        papers = json.load(fp)
    keys = papers.keys()
    keys.sort(reverse=True)

    if plain_text:
        print '\n'.join(keys)
        continue

    print '<h2><a name="{0}{1}{2}">{0}/{1}/{2}</a></h2>'.format(f[4:6], f[6:8], f[:4])
    print '<ul>'
    for k in keys:
        v = papers[k]
        print u'<li><b>[<a name="{0}" href="http://arxiv.org/abs/{0}">{0}</a>]</b> <a href="http://arxiv.org/pdf/{0}.pdf">{1}</a><br> <i>by {2}</i></li>'.format( \
                k, cgi.escape(v.pop(0)), \
                u', '.join(map(lambda s: s.partition(' <')[0], v)) \
                ).encode('utf-8')
    print '</ul>'

if not plain_text:
    print """
  <p class="footer">By <a href="http://web.stanford.edu/~yymao/">Yao-Yuan Mao</a> (2015). Part of the <a href="https://github.com/yymao/kipac-teabot">KIPAC TeaBot</a> project.</p>
  </div>
</body>
</html>
"""

