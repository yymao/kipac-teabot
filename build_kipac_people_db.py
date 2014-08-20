kipac_people_url = """\
http://kipac.stanford.edu/kipac/views/ajax?field_person_display_name_value=&type=2836&field_person_membership2_nid=2813&location=All&view_name=people_list&view_display_id=page_1&view_args=&view_path=people&view_base_path=people&view_dom_id=2&pager_element=0
http://kipac.stanford.edu/kipac/views/ajax?js=1&page=1&type=2836&field_person_membership2_nid=2813&location=All&view_name=people_list&view_display_id=page_1&view_path=people&view_base_path=people&view_dom_id=2&pager_element=0&view_args=
http://kipac.stanford.edu/kipac/views/ajax?field_person_display_name_value=&type=2834&field_person_membership2_nid=All&location=All&view_name=people_list&view_display_id=page_1&view_args=&view_path=people&view_base_path=people&view_dom_id=2&pager_element=0
http://kipac.stanford.edu/kipac/views/ajax?js=1&page=1&type=2834&field_person_membership2_nid=All&location=All&view_name=people_list&view_display_id=page_1&view_path=people&view_base_path=people&view_dom_id=2&pager_element=0&view_args=
http://kipac.stanford.edu/kipac/views/ajax?field_person_display_name_value=&type=3032&field_person_membership2_nid=All&location=All&view_name=people_list&view_display_id=page_1&view_args=&view_path=people&view_base_path=people&view_dom_id=2&pager_element=0
http://kipac.stanford.edu/kipac/views/ajax?field_person_display_name_value=&type=2837&field_person_membership2_nid=All&location=All&view_name=people_list&view_display_id=page_1&view_args=&view_path=people&view_base_path=people&view_dom_id=2&pager_element=0
http://kipac.stanford.edu/kipac/views/ajax?js=1&page=1&type=2837&field_person_membership2_nid=All&location=All&view_name=people_list&view_display_id=page_1&view_path=people&view_base_path=people&view_dom_id=2&pager_element=0&view_args=
http://kipac.stanford.edu/kipac/views/ajax?js=1&page=2&type=2837&field_person_membership2_nid=All&location=All&view_name=people_list&view_display_id=page_1&view_path=people&view_base_path=people&view_dom_id=2&pager_element=0&view_args=
http://kipac.stanford.edu/kipac/views/ajax?field_person_display_name_value=&type=2841&field_person_membership2_nid=All&location=All&view_name=people_list&view_display_id=page_1&view_args=&view_path=people&view_base_path=people&view_dom_id=2&pager_element=0
http://kipac.stanford.edu/kipac/views/ajax?js=1&page=1&type=2841&field_person_membership2_nid=All&location=All&view_name=people_list&view_display_id=page_1&view_path=people&view_base_path=people&view_dom_id=2&pager_element=0&view_args=
""".splitlines()

import re
from urllib import urlopen
import sqlite3

from database import people_db_path, collection_weight_path
from fetch_arxiv import fetch_arxiv
from topic_model import topic_model, collection_weight

re_name = re.compile(r'/kipac/people/\w+\\\"\\x3e([\w\s-]+)\\x3c')

arxiv_name_exceptions = {\
        'Chris Davis':'Davis_C_P',
        'Yashar Hezavehe':'Hezaveh_Y',
        'Kimmy Wu':'Wu_W_L_K',
        'Fatima Rubio da Costa':'da_Costa_F_R',
        'Yu Lu':'Lu_Yu',
        'Johnny Ng':'Ng_John_N',
        'Steve Allen':'Allen_S_W',
        'Yajie Yuan':'Yuan_Yajie',
        'Bob Wagoner':'Wagoner_R_V',
        'Rob Cameron':'Cameron_R_A',
        'David Burke':'Burke_D_L',
        'Blas Cabrera':'Cabrera_B',
        'Sarah Church':'Church_S',
        'Pat Burchat':'Burchat_P_R'
}

data = urlopen('http://names.mongabay.com/data/1000.html').read()
common_lastnames = [m.groups()[0].lower() for m in re.finditer(r"<tr><td>([A-Z]+)</td><td>\d+", data)]

def get_arxiv_name(name):
    if name in arxiv_name_exceptions:
        return arxiv_name_exceptions[name]
    first, space, last = name.rpartition(' ')
    first = re.split('\W+', first)
    if last.lower() in common_lastnames:
        first = '_'.join(first)
    else:
        first = '_'.join(map(lambda s:s[0], first))
    last = re.sub('\W+', '_', last)
    return last + '_' + first

db = sqlite3.connect(people_db_path)
cw = collection_weight()
for url in kipac_people_url:
    for m in re_name.finditer(urlopen(url).read()):
        name = m.groups()[0]
        arxivname = get_arxiv_name(name)
        arxiv = fetch_arxiv(search_query='cat:astro-ph*+AND+au:'+arxivname,\
                max_results=50, sortBy='submittedDate', sortOrder='descending')
        model = topic_model()
        count = 0
        for entry in arxiv.iterentries():
            count += 1
            model.add_document(entry['title'] + '.' + entry['summary'])
        if count:
            cw.add(model)
            db.execute('insert or replace into people (name, arxivname, model) values (?,?,?)', (name, arxivname, sqlite3.Binary(model.dumps())))
        print '%02d'%count, name, arxivname

db.commit()
db.close()

with open(collection_weight_path, 'w') as f:
    f.write(cw.dumps())

