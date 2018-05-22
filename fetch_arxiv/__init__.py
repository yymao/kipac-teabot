__all__ = ['fetch_arxiv', 'get_time_range', 'is_holiday']
import re
import time
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
                time.sleep(2)
                continue
            else:
                break
        else:
            raise IOError('cannot connect to arXiv')
        try:
            self.root = ET.parse(f).getroot()
        except ET.ParseError as e:
            print 'Something wrong with URL: {}'.format(url)
            raise e

        first_entry = self.root.find(_prefix+'entry')
        if first_entry is not None and \
                first_entry.findtext(_prefix+'title') == 'Error':
            self.root.remove(first_entry)

    def getentries(self):
        return map(arxiv_entry, self.root.iterfind(_prefix+'entry'))

    def iterentries(self):
        for entry in self.root.iterfind(_prefix+'entry'):
            yield arxiv_entry(entry)



#announcement time:                  03:00 UTC (02:00 if DST)
#submission deadline time ( < 2017): 21:00 UTC (20:00 if DST)
#submission deadline time (>= 2017): 19:00 UTC (18:00 if DST)

_oneday = 24*60*60
_holidays = {'20151126','20151225','20151229','20160101','20161124','20161226','20161228'}

def _parse_time(t):
    return t, time.gmtime(t), time.localtime(t).tm_isdst

def _print_date(t_st):
    return time.strftime('%Y%m%d', t_st)

def _print_deadline(t):
    now, now_st, dst = _parse_time(t)
    deadline_hour = 21 if now_st.tm_year < 2017 else 19
    return '%s%d00'%(_print_date(now_st), deadline_hour-dst)

def _last_workday(t):
    now, now_st, dst = _parse_time(t)
    while now_st.tm_wday >= 5 or _print_date(now_st) in _holidays:
        now, now_st, dst = _parse_time(now-_oneday)
    return now

def get_time_range(t, fwd_days=1):
    now, now_st, dst = _parse_time(t)
    now = _last_workday(now if now_st.tm_hour + dst >= 3 else now-_oneday)
    now = _last_workday(now-_oneday)
    then = _last_workday(now-_oneday*fwd_days)
    return _print_deadline(then), _print_deadline(now)

def is_holiday(t_st=None):
    if t_st is None:
        t_st = time.localtime()
    return (_print_date(t_st) in _holidays)
