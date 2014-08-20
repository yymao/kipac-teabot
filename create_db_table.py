import os
import sqlite3
from database import people_db_path

if os.path.isfile(people_db_path):
    os.unlink(people_db_path)

db = sqlite3.connect(people_db_path)
db.execute('CREATE TABLE people (name text unique, arxivname text, email text, model blob, tester int);')
db.commit()
db.close()

