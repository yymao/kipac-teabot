__all__ = ['fetch_arxiv']
from urllib import urlopen
import xml.etree.ElementTree as ET

_url_base = 'http://export.arxiv.org/api/query?'
_prefix = '{http://www.w3.org/2005/Atom}'

class arxiv_entry:
    def __init__(self, entry):
        self.entry = entry

    def __getitem__(self, key):
        if key == 'authors':
            return [author.findtext(_prefix+'name') \
                    for author in self.entry.iterfind(_prefix+'author')]
        elif key == 'first_author':
            return self.entry.find(_prefix+'author').findtext(_prefix+'name')
        else:
            return self.entry.findtext(_prefix+key)

class fetch_arxiv:
    def __init__(self, **keywords):
        """
        search_query=cat:astro-ph*+AND+au:%s
        max_results=50
        sortBy=submittedDate
        sortOrder=descending
        """
        url = _url_base + '&'.join([k+'='+str(v) \
                for k, v in keywords.iteritems()])
        self.root = ET.parse(urlopen(url)).getroot()
        first_entry = self.root.find(_prefix+'entry')
        if first_entry is not None and \
                first_entry.findtext(_prefix+'title') == 'Error':
            self.root.remove(first_entry)

    def getentries(self):
        return map(arxiv_entry, self.root.iterfind(_prefix+'entry'))

    def iterentries(self):
        for entry in self.root.iterfind(_prefix+'entry'):
            yield arxiv_entry(entry)


