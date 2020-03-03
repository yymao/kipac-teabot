from __future__ import print_function
import re
import time
import xml.etree.ElementTree as ET

try:
    from urllib import urlopen
except ImportError:
    from urllib.request import urlopen

try:
    from HTMLParser import HTMLParser
except ImportError:
    from html import unescape
else:
    _html_parser = HTMLParser()
    def unescape(s):
        return _html_parser.unescape(s)

__all__ = ["fetch_arxiv_rss"]

_url_base = "http://export.arxiv.org/rss/astro-ph"
_ns = {"rss": "http://purl.org/rss/1.0/", "el": "http://purl.org/dc/elements/1.1/"}


class arxiv_entry:
    def __init__(self, entry):
        self.entry = entry

    def __getitem__(self, key):
        if key == "authors":
            authors_raw = self.entry.findtext("el:creator", "", _ns)
            return [unescape(a.replace("</a>", "").strip()) for a in re.sub(r"<a[^<>]+>", "", authors_raw).split("</a>,")]
        if key == "first_author":
            return self["authors"][0]
        if key in ("key", "id"):
            return self.entry.findtext("rss:link", "", _ns).partition("arxiv.org/abs/")[-1]
        if key == "title":
            return self.entry.findtext("rss:title", "", _ns).partition(". (arXiv:")[0]
        if key == "summary":
            summary_raw = self.entry.findtext("rss:description", "", _ns)
            return re.sub(r"\s+", " ", re.sub(r"<[^<>]*>", "", summary_raw)).strip()
        return self.entry.findtext("rss:{}".format(key), "", _ns)


class fetch_arxiv_rss:
    def __init__(self, **kwargs):
        url = _url_base
        for i in range(10):
            try:
                f = urlopen(url)
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

        self._entries = None

    @property
    def entries(self):
        if self._entries is None:
            self._entries = []
            _current_key = None
            for entry_raw in self.root.findall("rss:item", _ns):
                entry = arxiv_entry(entry_raw)
                if _current_key and entry["key"] < _current_key:
                    break
                self._entries.append(entry)
        return list(self._entries)

    def iterentries(self):
        for entry in self.entries:
            yield entry

    def getentries(self):
        return self.entries
