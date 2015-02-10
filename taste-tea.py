#!/usr/bin/env python
import cgi
score = 0.25

form = cgi.FieldStorage()
arxiv_id = str(form.getvalue('id'))
name = form.getvalue('name')
key = form.getvalue('key')
abstract = form.getvalue('abs')

if name and key:
    import md5
    from secrets import keypass
    if md5.md5(arxiv_id + name + keypass).hexdigest() == key:
        from Member import Member
        with Member(name).get_weights_db('w') as d:
            if arxiv_id not in d or float(d[arxiv_id]) < score:
                d[arxiv_id] = str(score)

if arxiv_id:
    if abstract:
        url = 'http://arxiv.org/abs/' + arxiv_id
    else:
        url = 'http://arxiv.org/pdf/%s.pdf'%(arxiv_id)
else:
    url = 'http://arxiv.org/list/astro-ph/recent'

print 'Location:', url
print

