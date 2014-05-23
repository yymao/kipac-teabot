from database import people_db_path, tester_list
import sqlite3

db = sqlite3.connect(people_db_path)

for name, email in tester_list.iteritems():
    print name,
    cur = db.cursor()
    cur.execute('select 1 from people where name==? limit 1', (name,))
    if cur.fetchone() is None:
        print 'is not in the database!'
        continue
    print 'ok'
    db.execute('update people set email=?, tester=? where name==?', \
            (email, 1, name))
    db.commit()

db.execute('update people set tester=? where name==?', (2, 'Yao-Yuan Mao'))
db.commit()

db.close()

