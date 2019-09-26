'''
Logging during tests with human readable output to file.

Much simpler than logging: this is intended to be used only from test code.

Command line usage:
    $ TRACELOG=traces.log ./test

Beware of multi-process capable runners: they will interweave messages.
'''

import atexit
from datetime import datetime
import inspect
import os


__all__ = ('TRACELOG',)


trace_file_name = os.environ.get('TRACELOG')
trim_path = os.path.dirname(__file__) + os.path.sep

trace_file = None
if trace_file_name:
    trace_file = open(trace_file_name, 'a')

last_test_function = None


def _cleanup():
    global trace_file
    global last_test_function
    last_test_function = None

    _write('END')
    if trace_file:
        trace_file.close()
    trace_file = None


atexit.register(_cleanup)


def _get_test(stack):
    for _frame, filename, lineno, function, code_context, _index in stack:
        if function.startswith('test'):
            return f'{_shorten(filename)} {function}()'


def _shorten(filepath):
    relpath = os.path.relpath(filepath, trim_path)
    if len(relpath) < len(filepath):
        return relpath
    return filepath


def _write(message):
    if trace_file:
        trace_file.write(message)
        trace_file.write('\n')
        trace_file.flush()


def TRACELOG(*args, **kwargs):
    global last_test_function

    if not trace_file:
        return

    now = datetime.now()

    message = ' '.join(repr(arg) for arg in args)
    if kwargs:
        message += '   ** ' + ' | '.join(
            f'{key}: {value!r}'
            for key, value in sorted(kwargs.items()))

    try:
        stack = inspect.stack()
    except OSError:
        # it can happen e.g. if the current directory is deleted
        _write(f'{now} (?) {message}')
        return

    try:
        # assume calls from tests
        test_function = _get_test(stack)

        # caller info
        _frame, filename, lineno, function, _code_context, _index = stack[1]
    finally:
        del stack

    if test_function != last_test_function:
        if last_test_function:
            _write(f'{now} END TEST {last_test_function}\n')
        if test_function:
            _write(f'\n{now} BEGIN TEST {test_function}')
        last_test_function = test_function

    location = f'{_shorten(filename)}:{lineno:<4d} @{function:5s}'

    if last_test_function:
        # we have time in the test header-footer
        _write(f'  {location} {message}')
    else:
        _write(f'{now} {location} {message}')
