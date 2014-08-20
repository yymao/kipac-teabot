import sqlite3
from database import people_db_path, response_db_path
from fetch_arxiv import fetch_arxiv
from topic_model import topic_model

weight = 0.25

people = []
db = sqlite3.connect(people_db_path)
cur = db.cursor()
cur.execute('select name, model from people where tester >= 1')
row = cur.fetchone()
while row is not None:
    people.append({'name':row[0], 'model':topic_model(str(row[1]))})
    row = cur.fetchone()
db.close()

db = sqlite3.connect(response_db_path)
cur = db.cursor()
for person in people:
    print person['name']
    cur.execute('select arxiv_id from response where person==? and (res==? or res==?)', (person['name'], 'like', 'read'))
    arxiv_ids = map(lambda t: t[0], cur.fetchall())
    if arxiv_ids:
        arxiv = fetch_arxiv(id_list=','.join(arxiv_ids), \
                max_results=len(arxiv_ids))
        for entry in arxiv.iterentries():
            person['model'].add_document(entry['title']+'.'+entry['summary'], \
                    weight)
        person['changed'] = True
db.close()

db = sqlite3.connect(people_db_path)
for person in people:
    if 'changed' in person:
        db.execute('update people set model=? where name==?', \
                (sqlite3.Binary(person['model'].dumps()), person['name']))
db.commit()
db.close()

