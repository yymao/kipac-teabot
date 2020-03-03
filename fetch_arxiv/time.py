import time

__all__ = ["get_time_range", "is_holiday"]

# announcement time:                  03:00 UTC (02:00 if DST)
# submission deadline time ( < 2017): 21:00 UTC (20:00 if DST)
# submission deadline time (>= 2017): 19:00 UTC (18:00 if DST)

_oneday = 24 * 60 * 60
_holidays = {"20191128", "20191225", "20191226", "20191230", "20200101"}


def _parse_time(t):
    return t, time.gmtime(t), time.localtime(t).tm_isdst


def _print_date(t_st):
    return time.strftime("%Y%m%d", t_st)


def _print_deadline(t):
    _, now_st, dst = _parse_time(t)
    deadline_hour = 21 if now_st.tm_year < 2017 else 19
    return "%s%d00" % (_print_date(now_st), deadline_hour - dst)


def _last_workday(t):
    now, now_st, _ = _parse_time(t)
    while now_st.tm_wday >= 5 or _print_date(now_st) in _holidays:
        now, now_st, _ = _parse_time(now - _oneday)
    return now


def get_time_range(t, fwd_days=1):
    now, now_st, dst = _parse_time(t)
    now = _last_workday(now if now_st.tm_hour + dst >= 3 else now - _oneday)
    now = _last_workday(now - _oneday)
    then = _last_workday(now - _oneday * fwd_days)
    return _print_deadline(then), _print_deadline(now)


def is_holiday(t_st=None):
    if t_st is None:
        t_st = time.localtime()
    return _print_date(t_st) in _holidays
