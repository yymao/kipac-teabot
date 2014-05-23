import sys
import sqlite3
import numpy as np

from database import people_db_path
from fetch_arxiv import fetch_arxiv
from topic_model import topic_model, similarity_threshold

people = []
db = sqlite3.connect(people_db_path)
cur = db.cursor()
cur.execute('select name, model, email, tester from people')
row = cur.fetchone()
while row is not None:
    people.append({'name':row[0], 'model':topic_model(str(row[1])), 'email':row[2], 'tester':row[3]})
    row = cur.fetchone()
db.close()

arxiv = fetch_arxiv(max_results=1, id_list=sys.argv[1])
entry = arxiv.getentries()[0]
model = topic_model()
model.add_document(entry['title'] + '.' + entry['summary'])
scores = np.array([model.get_similarity(person['model']) for person in people])

indices = scores.argsort()
for i in reversed(indices):
    print people[i]['name'], scores[i]

