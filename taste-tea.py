import cgi, cgitb
cgitb.enable()
print 'Content-Type: text/html'
print

score = 0.25

form = cgi.FieldStorage()
arxiv_id = form.getvalue('id')
name = form.getvalue('name')
key = form.getvalue('key')

if name and key:
    import md5
    import sys
    sys.path.append('../kipac-teabot')
    from database import keypass, model_dir
    if md5.md5(arxiv_id + name + keypass).hexdigest() == key:
        d = anydbm.open('%s/%s'%(model_dir, name), 'w')
        if arxiv_id not in d or float(d[arxiv_id]) < score:
            d[arxiv_id] = score
        d.close()

url = 'http://arxiv.org/pdf/%s.pdf'%(arxiv_id) if arxiv_id else 'http://arxiv.org'
print '<html><head><script>location.href="%s"</script><meta http-equiv="Refresh" content="0; URL=%s"></head></html>'%(url, url)

