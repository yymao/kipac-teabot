#!/usr/bin/env python
import cgi
score = 0.25

form = cgi.FieldStorage()
arxiv_id = form.getfirst('id', '')
name = form.getfirst('name', '')
key = form.getfirst('key','')
abstract = form.getfirst('abs','')
mendeley = form.getfirst('mendeley','')

if name and key:
    import md5
    from secrets import keypass
    if md5.md5(arxiv_id + name + keypass).hexdigest() == key:
        from Member import Member
        with Member(name).get_weights_db('w') as d:
            if arxiv_id not in d or float(d[arxiv_id]) < score:
                d[arxiv_id] = str(score)

if arxiv_id:
    if mendeley:
        url = 'https://www.mendeley.com/import/?url=http%3A%2F%2Farxiv.org%2Fabs%2F' + arxiv_id
    elif abstract:
        url = 'https://arxiv.org/abs/' + arxiv_id
    else:
        url = 'https://arxiv.org/pdf/{0}.pdf'.format(arxiv_id)
else:
    url = 'https://arxiv.org/list/astro-ph/recent'

print 'Location:', url
print

