from __future__ import print_function
import re
import time
import xml.etree.ElementTree as ET

try:
    from urllib import urlopen
except ImportError:
    from urllib.request import urlopen

from .utils import arxiv_id_pattern

__all__ = ["fetch_arxiv"]

_url_base = "http://export.arxiv.org/api/query?"
_ns = {"atom": "http://www.w3.org/2005/Atom"}
_arxiv_re = re.compile(arxiv_id_pattern)


class arxiv_entry:
    def __init__(self, entry):
        self.entry = entry

    def __getitem__(self, key):
        if key == "authors":
            return [
                author.findtext("atom:name", "", _ns)
                for author in self.entry.iterfind("atom:author", _ns)
            ]
        if key == "first_author":
            return self.entry.find("atom:author", _ns).findtext("atom:name", "", _ns)
        if key in ("key", "id"):
            return _arxiv_re.search(self.entry.findtext("atom:id", "", _ns)).group()
        return self.entry.findtext("atom:{}".format(key), "", _ns)


class fetch_arxiv:
    def __init__(self, url=None, **kwargs):
        """
        search_query=cat:astro-ph*+AND+au:%s
        max_results=50
        sortBy=submittedDate
        sortOrder=descending
        id_list=[comma-delimited ids]
        """
        if url is None:
            self.url = _url_base + "&".join([k + "=" + str(v) for k, v in kwargs.items()])
        else:
            self.url = url
        for i in range(10):
            try:
                f = urlopen(self.url)
            except IOError:
                time.sleep(i + 1)
                continue
            else:
                break
        else:
            raise IOError("cannot connect to arXiv")
        try:
            self.root = ET.parse(f).getroot()
        except ET.ParseError as e:
            print("Something wrong with URL: {}".format(url))
            raise e

        first_entry = self.root.find("atom:entry", _ns)
        if (
            first_entry is not None
            and first_entry.findtext("atom:title", "Error", _ns) == "Error"
        ):
            self.root.remove(first_entry)

        self._entries = None

    @property
    def entries(self):
        if self._entries is None:
            self._entries = [arxiv_entry(e) for e in self.root.findall("atom:entry", _ns)]
        return list(self._entries)

    def iterentries(self):
        for entry in self.entries:
            yield entry

    def getentries(self):
        return self.entries
