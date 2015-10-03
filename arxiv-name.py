#!/usr/bin/env python
import re
import cgi
#import cgitb
#cgitb.enable()
from fetch_arxiv import fetch_arxiv

print "Content-Type: text/html"
print 

form = cgi.FieldStorage()
last = form.getvalue('last')
first= form.getvalue('first')
fi = bool(form.getvalue('fi'))

first = re.split('\W+', first)
first = '_'.join(map(lambda s:s[:1], first)) if fi else '_'.join(first)
last = re.sub('\W+', '_', last)
arxivname = last.strip('_') + '_' + first.strip('_')

print "<h3>arXiv name: %s</h3>"%arxivname

arxiv = fetch_arxiv(search_query='cat:astro-ph*+AND+au:'+arxivname,\
        max_results=20, sortBy='submittedDate', sortOrder='descending')
entries = arxiv.getentries()

if entries:
    print '<ul>'
    for entry in entries:
        item = u'<li><a href="%s">%s</a> <b>%s</b><br/><i>%s</i></li>'%(\
                entry['id'], entry['id'][21:-2], entry['title'], \
                u', '.join(entry['authors']))
        print item.encode('ascii', 'xmlcharrefreplace')
    print '</ul>'
else:
    print '<h3>No paper found.</h3>'
