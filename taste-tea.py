#!/usr/bin/env python
import cgi
score = 0.25

form = cgi.FieldStorage()
arxiv_id = str(form.getvalue('id'))
name = form.getvalue('name')
key = form.getvalue('key')

if name and key:
    import md5
    from secrets import keypass
    if md5.md5(arxiv_id + name + keypass).hexdigest() == key:
        from Member import Member
        with Member(name).get_weights_db('w') as d:
            if arxiv_id not in d or float(d[arxiv_id]) < score:
                d[arxiv_id] = str(score)

url = ('http://arxiv.org/pdf/%s.pdf'%(arxiv_id)) if arxiv_id else 'http://arxiv.org'

print 'Location:', url
print

