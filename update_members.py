from urllib import urlopen
import anydbm
from database import kipac_members_url, kipac_members_reduced_csv, model_dir
from fetch_arxiv import fetch_arxiv

f = urlopen(kipac_members_url)
f.next()
with open(kipac_members_reduced_csv, 'w') as fo:
    for line in f:
        items = line.split(',')
        if int(items[5]) == 0:
            continue
        arxivname = items[2]
        arxiv = fetch_arxiv(search_query='cat:astro-ph*+AND+au:'+arxivname,\
                max_results=50, sortBy='submittedDate', sortOrder='descending')
        count = 0
        d = anydbm.open('%s/%s'%(model_dir, arxivname), 'c')
        for entry in arxiv.iterentries():
            d[entry['key']] = '1'
            count += 1
        d.close()
        if count:
            fo.write(line)
        print items[0], count

