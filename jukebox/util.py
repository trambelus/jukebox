"""Utility functions."""

import six
from datetime import timedelta
from .app import app

def convert(data):
    """Used to convert kwargs to use string-based keys and values, not bytes."""
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            result[convert(key)] = convert(value)
    elif isinstance(data, list):
        result = []
        for x in data:
            result.append(convert(x))
    elif isinstance(data, six.string_types) or isinstance(data, bytes):
        try:
            result = data.decode()
        except AttributeError as e:
            result = data
    else:
        result = data
    return result

def format_timedelta(td):
    """Format timedelta td."""
    fmt = [] # The format as a list.
    seconds = int(td.total_seconds())
    years, seconds = divmod(seconds, 31536000)
    if years:
        fmt.append('%d %s' % (years, 'year' if years == 1 else 'years'))
    months, seconds = divmod(seconds, 2592000)
    if months:
        fmt.append('%d %s' % (months, 'month' if months == 1 else 'months'))
    days, seconds = divmod(seconds, 86400)
    if days:
        fmt.append('%d %s' % (days, 'day' if days == 1 else 'days'))
    hours, seconds = divmod(seconds, 3600)
    if hours:
        fmt.append('%d %s' % (hours, 'hour' if hours == 1 else 'hours'))
    minutes, seconds = divmod(seconds, 60)
    if minutes:
        fmt.append('%d %s' % (minutes, 'minute' if minutes == 1 else 'minutes'))
    if seconds:
        fmt.append('%d %s' % (seconds, 'second' if seconds == 1 else 'seconds'))
    if len(fmt) == 1:
        return fmt[0]
    else:
        res = ''
        for pos, item in enumerate(fmt):
            if pos == len(fmt) - 1:
                res += ', and '
            elif res:
                res += ', '
            res += item
        return res

def queue_duration():
    """Get the duration of the queue."""
    return format_timedelta(sum([track.duration for track in app.queue], timedelta()))
