#!/usr/bin/env python

import cgi
import cgitb
cgitb.enable()
print 'Content-Type: text/html'
print

import os
import time
import json
from secrets import discovery_archive


print '''
<!DOCTYPE html>
<html>
<head>
  <title>New arXiv papers by KIPAC members</title>
  <meta http-equiv="content-type" content="text/html; charset=utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="stylesheet" href="//cdn.jsdelivr.net/pure/0.5.0/pure-min.css">
  <style>
  .l-box {padding: 1em;}
  </style>
</head>
<body>
  <div class="l-box">
    <h1>New arXiv papers by KIPAC members</h1>
'''

backto = int(time.strftime('%Y%m%d', time.localtime(time.time()-90*24*60*60)))
files = os.listdir(discovery_archive)
files = filter(lambda s: s.endswith('.json'), files)
files = filter(lambda i: i>backto, map(lambda s: int(s[:-5]), files))
files.sort(reverse=True)
files = map(str, files)

for f in files:
    with open('%s/%s.json'%(discovery_archive, f)) as fp:
        papers = json.load(fp)
    print '<h2>%s</h2>'%('/'.join([f[4:6], f[6:8], f[:4]]))
    print '<ul>'
    keys = papers.keys()
    keys.sort(reverse=True)
    for k in keys:
        v = papers[k]
        print u'<li><p><b>[%s]</b> <a href="http://arxiv.org/abs/%s">%s</a><br>'%(k, k, cgi.escape(v[0]))
        print u'by', u', '.join(map(lambda s: cgi.escape(s.partition(' <')[0]), v[1:]))
        print '</p></li>'
    print '</ul><br>'

print """
  </div>
</body>
</html>
"""

