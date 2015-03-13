#!/usr/bin/env python

import cgi
form = cgi.FieldStorage()
arxiv_id = form.getvalue('id')
print 'Content-Type: text/html'
print

from fetch_arxiv import fetch_arxiv
from topic_model import topic_model, collection_weight, similarity_threshold
from secrets import member_list_path, collection_weight_path
from Member import Member

try:
    if not arxiv_id:
        raise ValueError('no arXiv ID provided.')

    try:
        entry = fetch_arxiv(id_list=arxiv_id).getentries()[0]
    except IndexError:
        raise ValueError('arXiv ID {0} not found.'.format(arxiv_id))

    model = topic_model()
    model.add_document('{0[title]}. {0[summary]}'.format(entry))

    #load kipac members
    people = []
    with open(member_list_path, 'r') as f:
        header = f.next().strip().split(',')
        for line in f:
            person = dict(zip(header, line.strip().split(',')))
            if int(person['active'] or 0):
                person['model'] = Member(person['arxivname']).get_model()
                if person['model'] is not None:
                    people.append(person)
    if not people:
        raise ValueError('something wrong with the member database!')

    #apply collection weight to arxiv entries
    with open(collection_weight_path, 'rb') as f:
        model.apply_weight(collection_weight(f.read()))

    scores = [model.get_similarity(person['model']) for person in people]
    idx = sorted(xrange(len(scores)), key=scores.__getitem__, reverse=True)[:15]

    print '<h4>[<a href="http://arxiv.org/abs/{0}">{0}</a>] {1}</h4>'.format(arxiv_id, cgi.escape(entry['title']))
    for i in idx:
        print '<p title="score = {1:.4f}">{0[name]} &lt;{0[email]}&gt;, </p>'.format(people[i], scores[i]*100.0)

except Exception as e:
    print '<p class="error">Error: {0}</p>'.format(e)

