from __future__ import print_function, absolute_import
import re
import datetime
import xml.etree.ElementTree as ET

from .utils import load_url

__all__ = ["fetch_arxiv_rss"]

_url_base = "https://rss.arxiv.org/rss/astro-ph"
_ns = {"arxiv": "http://arxiv.org/schemas/atom", "dc":"http://purl.org/dc/elements/1.1/"}


class arxiv_entry:
    def __init__(self, entry):
        self.entry = entry
        self._attr_cache = dict()

    def __getattr__(self, name):
        if name not in self._attr_cache:
            if name == "authors":
                output = [a.strip() for a in re.sub(r"\(.*?\)", "", self.entry.findtext("dc:creator", "", _ns)).split(",")]
            elif name == "first_author":
                output = self.authors[0]
            elif name == "authors_text":
                output = ", ".join(self.authors)
            elif name in ("key", "id"):
                output = self.entry.findtext("link").partition("/abs/")[-1]
            elif name == "title":
                output = self.entry.findtext("title").strip()
            elif name == "summary":
                output = self.entry.findtext("description", "", _ns).partition("Abstract:")[-1].strip()
            elif name == "is_new":
                output = self.entry.findtext("arxiv:announce_type", "", _ns).strip() in ["new", "cross"]
            else:
                output = self.entry.findtext(name, None, _ns)

            if output is not None:
                self._attr_cache[name] = output

        return self._attr_cache[name]

    __getitem__ = __getattr__

    def __repr__(self):
        return "{}".format(self.entry)


class fetch_arxiv_rss:
    def __init__(self, **kwargs):
        xml = load_url(_url_base)
        try:
            self.root = ET.fromstring(xml).find("channel")
        except ET.ParseError as e:
            print("Something wrong with URL: {}".format(_url_base))
            raise e

        self._entries = None

    @property
    def date(self):
        date_str = self.root.findtext("pubDate")
        date_str = " ".join(date_str.split()[1:4])
        return datetime.datetime.strptime(date_str, "%d %b %Y").strftime("%Y%m%d")

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
