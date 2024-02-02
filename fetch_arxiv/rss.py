from __future__ import print_function, absolute_import
import re
import time
import datetime
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
_ns = {"arxiv": "http://arxiv.org/schemas/atom", "dc":"http://purl.org/dc/elements/1.1/"}


class arxiv_entry:
    def __init__(self, entry):
        self.entry = entry
        self._attr_cache = dict()

    def __getattr__(self, name):
        if name not in self._attr_cache:
            if name == "authors":
                output = [unescape(a.text).strip() for a in self.entry.find("dc:creator", _ns).findall("a")]
            elif name == "first_author":
                output = self.authors[0]
            elif name == "authors_text":
                output = ", ".join(self.authors)
            elif name in ("key", "id"):
                output = self.entry.findtext("link").partition("arxiv.org/abs/")[-1].strip()
            elif name == "title":
                output = self.entry.findtext("title").partition(". (arXiv:")[0].strip()
            elif name == "summary":
                summary_raw = self.entry.findtext("description", "", _ns)
                output = re.sub(r"\s+", " ", re.sub(r"<[^<>]*>", "", summary_raw)).strip()
            elif name == "is_new":
                output = self.entry.findtext("arxiv:announce_type", "", _ns).strip() in ["new", "cross"]
            else:
                output = self.entry.findtext("rss:{}".format(name), None, _ns)

            if output is not None:
                self._attr_cache[name] = output

        return self._attr_cache[name]

    __getitem__ = __getattr__


class fetch_arxiv_rss:
    def __init__(self, **kwargs):
        url = _url_base
        for i in range(20):
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
            self.root = ET.parse(f).getroot().find("channel")
        except ET.ParseError as e:
            print("Something wrong with URL: {}".format(url))
            raise e

        self._entries = None

    @property
    def date(self):
        date_str = self.root.findtext("pubDate")
        date_str = " ".join(date_str.split()[1:4])
        return datetime.datetime.strptime("02 Feb 2024", "%d %b %Y").strftime("%Y%m%d")

    @property
    def entries(self):
        if self._entries is None:
            self._entries = []
            for entry_raw in self.root.findall("item"):
                entry = arxiv_entry(entry_raw)
                if entry.is_new:
                    self._entries.append(entry)
        return list(self._entries)

    def iterentries(self):
        for entry in self.entries:
            yield entry

    def getentries(self):
        return self.entries
