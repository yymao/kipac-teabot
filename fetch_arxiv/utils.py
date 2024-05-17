import ssl
import time
from urllib2 import urlopen

__all__ = ['arxiv_id_pattern', 'load_url']


arxiv_id_pattern = r"\d{4}\.\d{4,5}|[a-z-]+(?:\.[A-Za-z-]+)?\/\d{7}"


def load_url(url, check_prefix="<?xml"):
    context = ssl._create_unverified_context()
    for i in range(1, 11):
        try:
            feed = urlopen(url, timeout=20, context=context).read()
        except IOError:
            pass
        else:
            if (check_prefix and feed.startswith(check_prefix)) or (feed and not check_prefix):
                return feed
        time.sleep(i * 2)
    raise IOError("Not able to connect to " + url)
