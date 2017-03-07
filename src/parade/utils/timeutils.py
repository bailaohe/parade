import datetime
import time

import pytz


def datetime_str_to_timestamp(datetime_str, tz=None):
    dt = datetime.datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
    return datetime_to_timestamp(dt, tz)


def datetime_to_timestamp(dt, tz=None):
    if tz:
        dt = pytz.timezone(tz).localize(dt)
        return int((dt - datetime.datetime(1970, 1, 1, tzinfo=pytz.utc)).total_seconds())
    return int(time.mktime(dt.timetuple()))


def timestamp_to_datetime(ts, tz=None):
    if tz:
        return datetime.datetime.fromtimestamp(ts, pytz.timezone(tz))
    return datetime.datetime.fromtimestamp(ts)
