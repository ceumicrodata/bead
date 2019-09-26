import re
from datetime import tzinfo, timedelta, datetime


#########################################################
# source: https://docs.python.org/2/library/datetime.html
# Example tzinfo classes:
# A class capturing the platform's idea of local time.

import time as _time

ZERO = timedelta(0)


class FixedOffset(tzinfo):
    """Fixed offset in minutes east from UTC."""

    def __init__(self, offset, name):
        self.__offset = timedelta(minutes = offset)
        self.__name = name

    def utcoffset(self, dt):
        return self.__offset

    def tzname(self, dt):
        return self.__name

    def dst(self, dt):
        return ZERO


STDOFFSET = timedelta(seconds = -_time.timezone)
if _time.daylight:
    DSTOFFSET = timedelta(seconds = -_time.altzone)
else:
    DSTOFFSET = STDOFFSET

DSTDIFF = DSTOFFSET - STDOFFSET


class LocalTimezone(tzinfo):

    def utcoffset(self, dt):
        if self._isdst(dt):
            return DSTOFFSET
        else:
            return STDOFFSET

    def dst(self, dt):
        if self._isdst(dt):
            return DSTDIFF
        else:
            return ZERO

    def tzname(self, dt):
        return _time.tzname[self._isdst(dt)]

    def _isdst(self, dt):
        tt = (dt.year, dt.month, dt.day,
              dt.hour, dt.minute, dt.second,
              dt.weekday(), 0, 0)
        stamp = _time.mktime(tt)
        tt = _time.localtime(stamp)
        return tt.tm_isdst > 0


Local = LocalTimezone()


# end of code from python docs
#########################################################


# it would be nice if we could use datetime.strptime
# but timezone parsing (%z) is not working on Python 2.*
# http://stackoverflow.com/questions/20194496/iso-to-datetime-object-z-is-a-bad-directive
#
# so the 2 options are:
# - use dateutil (cons: external dependency)
# - implement just what is needed (cons: errors?)


_NAMED_REGEXPS = (
    ('{YEAR}',     '(?P<year>DIGIT{4})'),
    ('{MONTH}',    '(?P<month>DIGIT{2})'),
    ('{DAY}',      '(?P<day>DIGIT{2})'),
    ('{HOUR}',     '(?P<hour>DIGIT{2})'),
    ('{MINUTE}',   '(?P<minute>DIGIT{2})'),
    ('{SECOND}',   '(?P<second>DIGIT{2})'),
    ('{MICROSEC}', '(?P<microsec>DIGIT{6})'),
    ('{TIMEZONE}', '(?P<tzsign>[-+])(?P<tzhour>DIGIT{2})(?P<tzmin>DIGIT{2})'),
    ('DIGIT',      '[0-9]')
)


def _compile_parser(template):
    for name, regexp in _NAMED_REGEXPS:
        template = template.replace(name, regexp)
    match = re.compile(template + '$').match

    def convert(timeish):
        parts = match(timeish)
        if parts:
            values = parts.groupdict()

            # v for value
            def v(key, default):
                return int(values.get(key, default))
            tzoffset = (
                (-1 if values.get('tzsign', '+') == '-' else 1)
                *
                (v('tzhour', 0) * 60 + v('tzmin', 0)))

            return datetime(
                v('year', 0),
                v('month', 1),
                v('day', 1),
                v('hour', 0),
                v('minute', 0),
                v('second', 0),
                v('microsec', 0),
                FixedOffset(tzoffset, 'TZ' + str(tzoffset)))
    return convert


_DEFAULT_FULL_TIMESTAMP = '{YEAR}{MONTH}{DAY}T{HOUR}{MINUTE}{SECOND}{MICROSEC}{TIMEZONE}'
_parse_default_timestamp = _compile_parser(_DEFAULT_FULL_TIMESTAMP)

_ISO8601_PARSERS = [
    _parse_default_timestamp
] + [
    _compile_parser(template) for template in (
        '{YEAR}',
        '{YEAR}{MONTH}',
        '{YEAR}-{MONTH}',
        '{YEAR}{MONTH}{DAY}',
        '{YEAR}-{MONTH}-{DAY}',
        '{YEAR}{MONTH}{DAY}T{HOUR}{MINUTE}{SECOND}{TIMEZONE}',
        '{YEAR}-{MONTH}-{DAY}T{HOUR}:{MINUTE}:{SECOND}{TIMEZONE}',
        '{YEAR}-{MONTH}-{DAY}T{HOUR}:{MINUTE}:{SECOND}.{MICROSEC}{TIMEZONE}',
    )]


def parse_iso8601(timeish):
    '''
        Parse some iso-8601 date/time formats to a datetime with timezone.
    '''
    for parse in _ISO8601_PARSERS:
        parsed = parse(timeish)
        if parsed is not None:
            return parsed
    raise ValueError('Time is not in a recognised iso-8601 format', timeish)


_TIME_UNITS = {
    'y': 'years',
    'm': 'months',
    'w': 'weeks',
    'd': 'days',
    # expected to be less used:
    'H': 'hours',
    'M': 'minutes',
    'S': 'seconds',
}

_DELTA = r'([+-]?\d+)([{units}])'.format(units=''.join(_TIME_UNITS.keys()))
_DELTAS = '(?:{})*$'.format(_DELTA)


def parse_timedelta(delta_str):
    '''
        Parse a time-delta of the format {AMOUNT}{UNIT}[{AMOUNT}{UNIT}[..]]

        E.g. '2w4d' for 2 weeks and 4 days
    '''
    match = re.match(_DELTAS, delta_str)
    if match:
        delta = timedelta()
        for amount, unit_abbrev in re.findall(_DELTA, delta_str):
            delta += timedelta(**{_TIME_UNITS[unit_abbrev]: int(amount)})
        return delta
    raise ValueError('Invalid delta format', delta_str)


def timestamp():
    '''
        A string representation of this moment.

        With millisecond resolution and time zone so that
        - users recognise the time they made it,
          even if they live in non-trivial time zones (think: +0800)
        - when parsed back, can be compared with others
          even from different time zones
    '''
    return datetime.now(Local).strftime('%Y%m%dT%H%M%S%f%z')


# a not so forgiving parser
def time_from_timestamp(timestamp_str):
    '''
        Parse a datetime from a timestamp string - strict!
    '''
    parsed = _parse_default_timestamp(timestamp_str)
    if parsed is None:
        raise ValueError(
            'Not a full, basic timestamp (%s)' % _DEFAULT_FULL_TIMESTAMP,
            timestamp_str)
    return parsed


def time_from_user(timeish):
    '''
        Parse a datetime from user entered string - multiple formats

        Allows informal differences from current time.
    '''
    try:
        return parse_iso8601(timeish)
    except ValueError:
        pass
    try:
        # fall back to interpreting it as a time-delta added to `now`
        return datetime.now(Local) + parse_timedelta(timeish)
    except ValueError:
        raise ValueError(
            'Can not interpret string either as time or as delta', timeish)


# TODO: add tests for timestamps, parse_iso8601, parse_timedelta
# ts = timestamp()
# print(ts, time_from_timestamp(ts))
# print(ts, parse_iso8601(ts))
# print(parse_iso8601('2012'))
# print(parse_iso8601('201211'))
# print(parse_iso8601('2012-11'))
# print(parse_iso8601('20121129'))
# print(parse_iso8601('2012-11-29'))
# print(parse_iso8601('2012-11-30T23:59:47-0100'))
# print(parse_iso8601('20121130T235947-0100'))
# print(parse_iso8601('20121120T090000-0100'), parse_iso8601('20121120T120000+0200'))
assert parse_iso8601('20121120T090000-0100') == parse_iso8601('20121120T120000+0200')
