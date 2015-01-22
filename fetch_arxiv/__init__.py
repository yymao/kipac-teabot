__all__ = ['fetch_arxiv']
import re
from urllib import urlopen
import xml.etree.ElementTree as ET

_url_base = 'http://export.arxiv.org/api/query?'
_prefix = '{http://www.w3.org/2005/Atom}'
_arxiv_re = re.compile(r'\d{4}\.\d{4,5}|[a-z-]+(?:\.[A-Za-z-]+)?\/\d{7}')

class arxiv_entry:
    def __init__(self, entry):
        self.entry = entry

    def __getitem__(self, key):
        if key == 'authors':
            return [author.findtext(_prefix+'name') \
                    for author in self.entry.iterfind(_prefix+'author')]
        elif key == 'first_author':
            return self.entry.find(_prefix+'author').findtext(_prefix+'name')
        elif key == 'key':
            return _arxiv_re.search(self.entry.findtext(_prefix+'id')).group()
        else:
            return self.entry.findtext(_prefix+key)

class fetch_arxiv:
    def __init__(self, **keywords):
        """
        search_query=cat:astro-ph*+AND+au:%s
        max_results=50
        sortBy=submittedDate
        sortOrder=descending
        id_list=[comma-delimited ids]
        """
        url = _url_base + '&'.join([k+'='+str(v) \
                for k, v in keywords.iteritems()])
        for i in range(5):
            try:
                f = urlopen(url)
            except IOError:
                continue
            else:
                break
        else:
            raise IOError('cannot connect to arXiv')
        self.root = ET.parse(f).getroot()
        first_entry = self.root.find(_prefix+'entry')
        if first_entry is not None and \
                first_entry.findtext(_prefix+'title') == 'Error':
            self.root.remove(first_entry)

    def getentries(self):
        return map(arxiv_entry, self.root.iterfind(_prefix+'entry'))

    def iterentries(self):
        for entry in self.root.iterfind(_prefix+'entry'):
            yield arxiv_entry(entry)


